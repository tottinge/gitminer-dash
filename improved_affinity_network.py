"""
Improved Affinity Network Module

This module provides an improved version of the file affinity network functionality
that works better with repositories that have sparse commit patterns.
"""

import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict
from itertools import combinations


def create_improved_file_affinity_network(commits, min_affinity=0.2, max_nodes=50, min_edge_count=1):
    """
    Create an improved network graph of file affinities based on commit history.
    
    This function is an enhanced version of the original create_file_affinity_network
    function with the following improvements:
    
    1. Lower default min_affinity threshold (0.2 instead of 0.5)
    2. Added min_edge_count parameter to filter out files with too few connections
    3. Better handling of isolated nodes
    4. More detailed logging of network statistics
    
    Args:
        commits: Iterable of commit objects
        min_affinity: Minimum affinity threshold for including edges (default: 0.2)
        max_nodes: Maximum number of nodes to include in the graph (default: 50)
        min_edge_count: Minimum number of edges a node must have to be included (default: 1)
        
    Returns:
        A tuple of (networkx graph, communities, stats)
    """
    if not commits:
        return nx.Graph(), [], {"error": "No commits provided"}
    
    # Statistics to return
    stats = {
        "total_commits": 0,
        "commits_with_multiple_files": 0,
        "unique_files": 0,
        "file_pairs": 0,
        "nodes_before_filtering": 0,
        "nodes_after_filtering": 0,
        "edges_before_filtering": 0,
        "edges_after_filtering": 0,
        "isolated_nodes": 0,
        "communities": 0,
        "avg_node_degree": 0,
        "avg_edge_weight": 0,
        "avg_community_size": 0
    }
    
    # Count total commits
    stats["total_commits"] = sum(1 for _ in commits)
    
    # Reset commits iterator if it was consumed
    if hasattr(commits, 'seek') and callable(getattr(commits, 'seek')):
        commits.seek(0)
    elif not hasattr(commits, '__len__'):
        commits = list(commits)
    
    # Calculate affinities
    affinities = defaultdict(float)
    file_counts = defaultdict(int)  # Count how many times each file appears in commits
    
    for commit in commits:
        files_in_commit = len(commit.stats.files)
        
        # Count files
        for file in commit.stats.files:
            file_counts[file] += 1
        
        if files_in_commit < 2:
            continue
            
        stats["commits_with_multiple_files"] += 1
        
        for combo in combinations(commit.stats.files, 2):
            ordered_key = tuple(sorted(combo))
            affinities[ordered_key] += 1 / files_in_commit
    
    # Get unique files
    all_files = set()
    for file_pair in affinities.keys():
        all_files.update(file_pair)
    
    stats["unique_files"] = len(all_files)
    stats["file_pairs"] = len(affinities)
    
    # Create a network graph
    G = nx.Graph()
    
    # Sort files by their total affinity and limit to max_nodes
    file_total_affinity = defaultdict(float)
    for (file1, file2), affinity in affinities.items():
        file_total_affinity[file1] += affinity
        file_total_affinity[file2] += affinity
    
    top_files = sorted(file_total_affinity.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
    top_file_set = {file for file, _ in top_files}
    
    # Add nodes for top files
    for file in top_file_set:
        G.add_node(file, commit_count=file_counts[file])
    
    stats["nodes_before_filtering"] = len(G.nodes())
    
    # Add edges with weights based on affinity
    for (file1, file2), affinity in affinities.items():
        if file1 in top_file_set and file2 in top_file_set and affinity >= min_affinity:
            G.add_edge(file1, file2, weight=affinity)
    
    stats["edges_before_filtering"] = len(G.edges())
    
    # Remove nodes with too few connections
    if min_edge_count > 0:
        nodes_to_remove = [node for node, degree in G.degree() if degree < min_edge_count]
        G.remove_nodes_from(nodes_to_remove)
        stats["isolated_nodes"] = len(nodes_to_remove)
    
    stats["nodes_after_filtering"] = len(G.nodes())
    stats["edges_after_filtering"] = len(G.edges())
    
    # Find communities/clusters using Louvain method
    if len(G.nodes()) > 0:
        communities = nx.community.louvain_communities(G)
        stats["communities"] = len(communities)
        
        # Calculate average community size
        if communities:
            community_sizes = [len(community) for community in communities]
            stats["avg_community_size"] = sum(community_sizes) / len(communities)
        
        # Assign community ID to each node
        for i, community in enumerate(communities):
            for node in community:
                G.nodes[node]['community'] = i
    else:
        communities = []
    
    # Calculate average node degree
    if len(G.nodes()) > 0:
        degrees = [degree for _, degree in G.degree()]
        stats["avg_node_degree"] = sum(degrees) / len(G.nodes())
    
    # Calculate average edge weight
    if len(G.edges()) > 0:
        weights = [data['weight'] for _, _, data in G.edges(data=True)]
        stats["avg_edge_weight"] = sum(weights) / len(G.edges())
    
    return G, communities, stats


def create_improved_network_visualization(G, communities, title="Improved File Affinity Network"):
    """
    Create an improved Plotly figure for visualizing the file affinity network.
    
    This function is an enhanced version of the original create_network_visualization
    function with the following improvements:
    
    1. Better handling of empty graphs
    2. Improved node sizing based on commit count
    3. More informative tooltips
    4. Fixed Plotly property names
    5. Better color scheme for communities
    
    Args:
        G: NetworkX graph of file affinities
        communities: List of communities detected in the graph
        title: Title for the visualization (default: "Improved File Affinity Network")
        
    Returns:
        A Plotly figure object
    """
    if len(G.nodes()) == 0:
        # Return a figure with a 'no data' message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for the selected time period",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        fig.update_layout(
            title=title + ' - No Data',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        return fig
    
    # Use a force-directed layout algorithm
    pos = nx.spring_layout(G, seed=42)
    
    # Create edge traces
    edge_x = []
    edge_y = []
    edge_weights = []
    edge_texts = []
    
    # Check if there are any edges before creating edge trace
    if len(G.edges()) > 0:
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
            weight = G.edges[edge]['weight']
            edge_weights.append(weight)
            
            # Create informative tooltip text
            edge_texts.append(f"{edge[0]} - {edge[1]}<br>Affinity: {weight:.2f}")
        
        # Normalize edge weights for width
        max_weight = max(edge_weights) if edge_weights else 1
        
        # Create separate edge traces for each edge with its own width
        edge_traces = []
        for i in range(0, len(edge_x), 3):  # Each edge is 3 points (x0, x1, None)
            if i + 2 < len(edge_x):  # Ensure we have a complete edge
                # Calculate width for this edge
                edge_idx = i // 3
                if edge_idx < len(edge_weights):
                    width = 2 + (edge_weights[edge_idx] / max_weight) * 6
                    text = edge_texts[edge_idx] if edge_idx < len(edge_texts) else ""
                else:
                    width = 2  # Default width if index is out of range
                    text = ""
                
                # Create a trace for this single edge
                edge_trace = go.Scatter(
                    x=edge_x[i:i+3],  # Just this edge's x coordinates
                    y=edge_y[i:i+3],  # Just this edge's y coordinates
                    line=dict(width=width, color='#888'),
                    hoverinfo='text',
                    text=text,
                    mode='lines',
                    showlegend=False
                )
                edge_traces.append(edge_trace)
        
        # If no edges were created, create an empty edge trace
        if not edge_traces:
            edge_trace = go.Scatter(
                x=[], y=[],
                line=dict(width=0, color='#888'),
                hoverinfo='none',
                mode='lines'
            )
            edge_traces = [edge_trace]
    else:
        # Create an empty edge trace if there are no edges
        edge_trace = go.Scatter(
            x=[], y=[],
            line=dict(width=0, color='#888'),
            hoverinfo='none',
            mode='lines')
        edge_traces = [edge_trace]
    
    # Create node traces (one per community for different colors)
    node_traces = []
    
    # Get a color map for communities - use a more distinct color palette
    community_colors = px.colors.qualitative.D3
    
    # Get community IDs from node attributes, handle case where there are no communities
    community_ids = set(nx.get_node_attributes(G, 'community').values())
    
    # If there are no communities but there are nodes, create a single community with all nodes
    if not community_ids and len(G.nodes()) > 0:
        # Create a trace with all nodes in a single color
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Create informative tooltip text
            commit_count = G.nodes[node].get('commit_count', 0)
            degree = G.degree(node)
            node_text.append(f"File: {node}<br>Commits: {commit_count}<br>Connections: {degree}")
            
            # Node size based on commit count and degree
            base_size = 10
            commit_factor = min(commit_count * 0.5, 20)  # Cap the size increase
            degree_factor = degree * 2
            node_size.append(base_size + commit_factor + degree_factor)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                color=community_colors[0],
                size=node_size,
                line=dict(width=1, color='#333')
            ),
            name='All Files'
        )
        
        node_traces.append(node_trace)
    else:
        # Process each community
        for community_id in community_ids:
            community_nodes = [node for node, data in G.nodes(data=True) 
                              if data.get('community') == community_id]
            
            node_x = []
            node_y = []
            node_text = []
            node_size = []
            
            for node in community_nodes:
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                
                # Create informative tooltip text
                commit_count = G.nodes[node].get('commit_count', 0)
                degree = G.degree(node)
                node_text.append(f"File: {node}<br>Commits: {commit_count}<br>Connections: {degree}")
                
                # Node size based on commit count and degree
                base_size = 10
                commit_factor = min(commit_count * 0.5, 20)  # Cap the size increase
                degree_factor = degree * 2
                node_size.append(base_size + commit_factor + degree_factor)
            
            color = community_colors[community_id % len(community_colors)]
            
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers',
                hoverinfo='text',
                text=node_text,
                marker=dict(
                    color=color,
                    size=node_size,
                    line=dict(width=1, color='#333')
                ),
                name=f'Group {community_id + 1}'
            )
            
            node_traces.append(node_trace)
    
    # Create figure
    fig = go.Figure(data=[*edge_traces, *node_traces],
                 layout=go.Layout(
                    title=title,
                    title_font=dict(size=16),  # Use title_font instead of titlefont
                    showlegend=True,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                ))
    
    return fig