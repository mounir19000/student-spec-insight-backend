import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import base64
from typing import List, Dict, Tuple, Optional, Any
import json

class DataAnalyzer:
    """
    A comprehensive data analysis class for PCA and clustering analysis
    """
    
    def __init__(self):
        self.data = None
        self.selected_modules = None
        self.scaler = StandardScaler()
        self.pca = None
        self.pca_data = None
        self.kmeans = None
        self.cluster_labels = None
        self.explained_variance = None
        self.loadings = None
        
    def load_data(self, students_data: List[Dict], selected_modules: List[str]) -> Dict[str, Any]:
        """
        Load and prepare data for analysis
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(students_data)
            
            # Extract grades from JSON if needed
            if 'grades' in df.columns:
                grades_df = pd.json_normalize(df['grades'])
                # Keep only selected modules that exist in grades
                available_modules = [mod for mod in selected_modules if mod in grades_df.columns]
                if not available_modules:
                    raise ValueError("None of the selected modules are available in the data")
                grades_df = grades_df[available_modules]
            else:
                # Check if modules are direct columns
                available_modules = [mod for mod in selected_modules if mod in df.columns]
                if not available_modules:
                    raise ValueError("None of the selected modules are available in the data")
                grades_df = df[available_modules]
            
            # Remove rows with missing values
            grades_df = grades_df.dropna()
            
            if grades_df.empty:
                raise ValueError("No valid data after removing missing values")
            
            # Store matricule for student identification
            matricules = df['matricule'].iloc[grades_df.index].tolist()
            
            self.data = grades_df
            self.selected_modules = available_modules
            self.matricules = matricules
            
            return {
                'success': True,
                'data_shape': grades_df.shape,
                'available_modules': available_modules,
                'sample_count': len(grades_df)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def perform_pca(self, n_components: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform Principal Component Analysis
        """
        try:
            if self.data is None:
                raise ValueError("No data loaded. Call load_data first.")
            
            # Standardize the data
            scaled_data = self.scaler.fit_transform(self.data)
            
            # Determine number of components
            if n_components is None:
                n_components = min(len(self.selected_modules), len(self.data))
            
            # Perform PCA
            self.pca = PCA(n_components=n_components)
            self.pca_data = self.pca.fit_transform(scaled_data)
            
            # Calculate explained variance
            self.explained_variance = self.pca.explained_variance_ratio_
            
            # Calculate loadings (components)
            self.loadings = pd.DataFrame(
                self.pca.components_.T,
                columns=[f'PC{i+1}' for i in range(n_components)],
                index=self.selected_modules
            )
            
            # Create variance plots
            variance_plot = self._create_variance_plot()
            cumulative_plot = self._create_cumulative_variance_plot()
            
            return {
                'success': True,
                'explained_variance': self.explained_variance.tolist(),
                'cumulative_variance': np.cumsum(self.explained_variance).tolist(),
                'loadings': self.loadings.to_dict('index'),
                'n_components': n_components,
                'variance_plot': variance_plot,
                'cumulative_plot': cumulative_plot,
                'pca_data_shape': self.pca_data.shape
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def find_optimal_clusters(self, max_k: int = 10) -> Dict[str, Any]:
        """
        Find optimal number of clusters using elbow method
        """
        try:
            if self.pca_data is None:
                raise ValueError("PCA not performed. Call perform_pca first.")
            
            k_range = range(1, min(max_k + 1, len(self.pca_data)))
            inertias = []
            silhouette_scores = []
            
            for k in k_range:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                kmeans.fit(self.pca_data)
                inertias.append(kmeans.inertia_)
                
                if k > 1:  # Silhouette score requires at least 2 clusters
                    score = silhouette_score(self.pca_data, kmeans.labels_)
                    silhouette_scores.append(score)
                else:
                    silhouette_scores.append(0)
            
            # Find elbow using the "elbow method"
            optimal_k = self._find_elbow_point(list(k_range), inertias)
            
            # Create elbow plot
            elbow_plot = self._create_elbow_plot(list(k_range), inertias, optimal_k)
            
            return {
                'success': True,
                'k_range': list(k_range),
                'inertias': inertias,
                'silhouette_scores': silhouette_scores,
                'optimal_k': optimal_k,
                'elbow_plot': elbow_plot
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def perform_clustering(self, n_clusters: int) -> Dict[str, Any]:
        """
        Perform K-means clustering
        """
        try:
            if self.pca_data is None:
                raise ValueError("PCA not performed. Call perform_pca first.")
            
            # Perform K-means clustering
            self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            self.cluster_labels = self.kmeans.fit_predict(self.pca_data)
            
            # Calculate cluster statistics
            cluster_stats = self._calculate_cluster_statistics(n_clusters)
            
            # Create cluster assignments
            cluster_assignments = pd.DataFrame({
                'matricule': self.matricules,
                'cluster': self.cluster_labels,
                **{f'PC{i+1}': self.pca_data[:, i] for i in range(self.pca_data.shape[1])}
            })
            
            return {
                'success': True,
                'cluster_assignments': cluster_assignments.to_dict('records'),
                'cluster_statistics': cluster_stats,
                'n_clusters': n_clusters,
                'silhouette_score': silhouette_score(self.pca_data, self.cluster_labels)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_biplot(self, pc1: int = 1, pc2: int = 2) -> Dict[str, Any]:
        """
        Create biplot visualization
        """
        try:
            if self.pca_data is None or self.cluster_labels is None:
                raise ValueError("PCA and clustering must be performed first.")
            
            pc1_idx = pc1 - 1
            pc2_idx = pc2 - 1
            
            if pc1_idx >= self.pca_data.shape[1] or pc2_idx >= self.pca_data.shape[1]:
                raise ValueError("Selected principal components exceed available components.")
            
            # Create scatter plot of students
            fig = go.Figure()
            
            # Add student points colored by cluster
            unique_clusters = np.unique(self.cluster_labels)
            colors = px.colors.qualitative.Set1[:len(unique_clusters)]
            
            for i, cluster in enumerate(unique_clusters):
                mask = self.cluster_labels == cluster
                fig.add_trace(go.Scatter(
                    x=self.pca_data[mask, pc1_idx],
                    y=self.pca_data[mask, pc2_idx],
                    mode='markers',
                    name=f'Cluster {cluster}',
                    marker=dict(color=colors[i], size=8),
                    text=[self.matricules[j] for j in range(len(mask)) if mask[j]],
                    hovertemplate='Matricule: %{text}<br>PC%{pc1}: %{x}<br>PC%{pc2}: %{y}<extra></extra>'.replace('%{pc1}', str(pc1)).replace('%{pc2}', str(pc2))
                ))
            
            # Add loading vectors (module contributions)
            loadings_scale = 10  # Scale factor for visibility (increased from 3)
            for i, module in enumerate(self.selected_modules):
                loading1 = self.loadings.iloc[i, pc1_idx] * loadings_scale
                loading2 = self.loadings.iloc[i, pc2_idx] * loadings_scale
                
                # Add arrow
                fig.add_trace(go.Scatter(
                    x=[0, loading1],
                    y=[0, loading2],
                    mode='lines',
                    line=dict(color='black', width=2),  # Changed to black and width 3
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                # Add arrowhead
                arrow_length = 0.2
                angle = np.arctan2(loading2, loading1)
                arrow_x1 = loading1 - arrow_length * np.cos(angle - np.pi/6)
                arrow_y1 = loading2 - arrow_length * np.sin(angle - np.pi/6)
                arrow_x2 = loading1 - arrow_length * np.cos(angle + np.pi/6)
                arrow_y2 = loading2 - arrow_length * np.sin(angle + np.pi/6)
                
                # Add arrowhead lines
                fig.add_trace(go.Scatter(
                    x=[loading1, arrow_x1],
                    y=[loading2, arrow_y1],
                    mode='lines',
                    line=dict(color='black', width=3),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                fig.add_trace(go.Scatter(
                    x=[loading1, arrow_x2],
                    y=[loading2, arrow_y2],
                    mode='lines',
                    line=dict(color='black', width=3),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                # Add text label
                fig.add_trace(go.Scatter(
                    x=[loading1],
                    y=[loading2],
                    mode='text',
                    text=[module],
                    textposition='top center',
                    showlegend=False,
                    hoverinfo='skip',
                    textfont=dict(color='black', size=12)  # Changed to black
                ))
            
            # Update layout
            fig.update_layout(
                title=f'PCA Biplot - PC{pc1} vs PC{pc2}',
                xaxis_title=f'PC{pc1} ({self.explained_variance[pc1_idx]:.1%} variance)',
                yaxis_title=f'PC{pc2} ({self.explained_variance[pc2_idx]:.1%} variance)',
                width=800,
                height=600,
                showlegend=True
            )
            
            # Convert to JSON for frontend
            biplot_json = fig.to_json()
            
            return {
                'success': True,
                'biplot': biplot_json,
                'pc1': pc1,
                'pc2': pc2,
                'explained_variance_pc1': self.explained_variance[pc1_idx],
                'explained_variance_pc2': self.explained_variance[pc2_idx]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_variance_plot(self) -> str:
        """Create explained variance plot"""
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[f'PC{i+1}' for i in range(len(self.explained_variance))],
            y=self.explained_variance,
            marker_color='steelblue'
        ))
        fig.update_layout(
            title='Explained Variance by Principal Component',
            xaxis_title='Principal Component',
            yaxis_title='Explained Variance Ratio',
            width=600,
            height=400
        )
        return fig.to_json()
    
    def _create_cumulative_variance_plot(self) -> str:
        """Create cumulative explained variance plot"""
        cumulative = np.cumsum(self.explained_variance)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[f'PC{i+1}' for i in range(len(cumulative))],
            y=cumulative,
            mode='lines+markers',
            marker_color='steelblue'
        ))
        fig.update_layout(
            title='Cumulative Explained Variance',
            xaxis_title='Principal Component',
            yaxis_title='Cumulative Explained Variance Ratio',
            width=600,
            height=400
        )
        return fig.to_json()
    
    def _create_elbow_plot(self, k_range: List[int], inertias: List[float], optimal_k: int) -> str:
        """Create elbow method plot"""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=k_range,
            y=inertias,
            mode='lines+markers',
            marker_color='steelblue',
            name='Inertia'
        ))
        
        # Highlight optimal k
        fig.add_trace(go.Scatter(
            x=[optimal_k],
            y=[inertias[k_range.index(optimal_k)]],
            mode='markers',
            marker=dict(color='red', size=12),
            name=f'Optimal k={optimal_k}'
        ))
        
        fig.update_layout(
            title='Elbow Method for Optimal Clusters',
            xaxis_title='Number of Clusters (k)',
            yaxis_title='Inertia',
            width=600,
            height=400
        )
        return fig.to_json()
    
    def _find_elbow_point(self, k_range: List[int], inertias: List[float]) -> int:
        """Find elbow point using the elbow method"""
        if len(inertias) < 3:
            return k_range[0] if k_range else 2
        
        # Calculate the rate of change
        diffs = np.diff(inertias)
        diff2 = np.diff(diffs)
        
        # Find the point with maximum second derivative (most bent)
        if len(diff2) > 0:
            elbow_idx = np.argmax(diff2) + 2  # +2 because of double diff
            if elbow_idx < len(k_range):
                return k_range[elbow_idx]
        
        # Fallback: use the point where inertia reduction slows down significantly
        for i in range(1, len(diffs)):
            if abs(diffs[i]) < abs(diffs[i-1]) * 0.7:
                return k_range[i+1]
        
        return k_range[min(3, len(k_range)-1)]  # Default to k=3 or 4
    
    def _calculate_cluster_statistics(self, n_clusters: int) -> Dict[str, Any]:
        """Calculate cluster statistics"""
        stats = {}
        
        for cluster in range(n_clusters):
            mask = self.cluster_labels == cluster
            cluster_data = self.data.iloc[mask]
            
            stats[f'cluster_{cluster}'] = {
                'size': int(np.sum(mask)),
                'percentage': float(np.sum(mask) / len(self.data) * 100),
                'mean_scores': cluster_data.mean().to_dict(),
                'std_scores': cluster_data.std().to_dict(),
                'students': [self.matricules[i] for i in range(len(mask)) if mask[i]][:10]  # Limit to first 10
            }
        
        return stats
    
    def export_analysis_results(self) -> Dict[str, Any]:
        """Export comprehensive analysis results"""
        try:
            if self.pca is None or self.cluster_labels is None:
                raise ValueError("Complete analysis not performed.")
            
            results = {
                'metadata': {
                    'selected_modules': self.selected_modules,
                    'n_components': self.pca.n_components_,
                    'n_clusters': len(np.unique(self.cluster_labels)),
                    'sample_size': len(self.data)
                },
                'pca_results': {
                    'explained_variance': self.explained_variance.tolist(),
                    'cumulative_variance': np.cumsum(self.explained_variance).tolist(),
                    'loadings': self.loadings.to_dict('index')
                },
                'cluster_results': {
                    'assignments': pd.DataFrame({
                        'matricule': self.matricules,
                        'cluster': self.cluster_labels
                    }).to_dict('records'),
                    'statistics': self._calculate_cluster_statistics(len(np.unique(self.cluster_labels)))
                }
            }
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }