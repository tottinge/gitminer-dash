#!/usr/bin/env python3
"""
Test script for the ideal affinity factor algorithm.

This script tests the calculate_ideal_affinity function to ensure it correctly
calculates an ideal minimum affinity threshold that results in 5-20 nodes.
"""


# Import from tests package to set up path
from tests import setup_path
setup_path()  # This ensures we can import modules from the project root
import os
import sys
import json
from datetime import datetime
from pathlib import Path
import networkx as nx
from collections import defaultdict
from itertools import combinations

# Test data directory
TEST_DATA_DIR = Path(os.path.join(os.path.dirname(__file__), "test_data"))

# Copy of the calculate_ideal_affinity function from affinity_groups.py
def calculate_ideal_affinity(commits, target_node_count=15, max_nodes=50):
    """
    Calculate an ideal minimum affinity threshold that will result in approximately
    the target number of connected nodes.
    
    Args:
        commits: Iterable of commit objects
        target_node_count: Target number of nodes in the final graph (default: 15)
        max_nodes: Maximum number of nodes to consider (default: 50)
        
    Returns:
        A tuple of (ideal_min_affinity, estimated_node_count, estimated_edge_count)
    """
    if not commits:
        return 0.2, 0, 0  # Default values if no commits
    
    # Reset commits iterator if it was consumed
    if hasattr(commits, 'seek') and callable(getattr(commits, 'seek')):
        commits.seek(0)
    elif not hasattr(commits, '__len__'):
        commits = list(commits)
    
    # Calculate affinities
    affinities = defaultdict(float)
    for commit in commits:
        files_in_commit = len(commit.stats.files)
        if files_in_commit < 2:
            continue
        for combo in combinations(commit.stats.files, 2):
            ordered_key = tuple(sorted(combo))
            affinities[ordered_key] += 1 / files_in_commit
    
    # Get unique files and their total affinities
    file_total_affinity = defaultdict(float)
    for (file1, file2), affinity in affinities.items():
        file_total_affinity[file1] += affinity
        file_total_affinity[file2] += affinity
    
    # Get top files by total affinity
    top_files = sorted(file_total_affinity.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
    top_file_set = {file for file, _ in top_files}
    
    # Get all affinity values between top files
    relevant_affinities = []
    for (file1, file2), affinity in affinities.items():
        if file1 in top_file_set and file2 in top_file_set:
            relevant_affinities.append(affinity)
    
    if not relevant_affinities:
        return 0.2, 0, 0  # Default if no relevant affinities
    
    # Sort affinities in descending order
    sorted_affinities = sorted(relevant_affinities, reverse=True)
    
    # Try different thresholds to find one that gives us the target node count
    thresholds = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
    best_threshold = 0.2  # Default if we can't find a better one
    best_node_count = 0
    best_edge_count = 0
    
    for threshold in thresholds:
        # Count edges that would be included with this threshold
        edge_count = sum(1 for a in relevant_affinities if a >= threshold)
        
        # Estimate connected nodes (this is an approximation)
        connected_nodes = set()
        for (file1, file2), affinity in affinities.items():
            if file1 in top_file_set and file2 in top_file_set and affinity >= threshold:
                connected_nodes.add(file1)
                connected_nodes.add(file2)
        
        node_count = len(connected_nodes)
        
        # If this threshold gives us a node count in our target range, use it
        if 5 <= node_count <= 20:
            best_threshold = threshold
            best_node_count = node_count
            best_edge_count = edge_count
            break
        
        # If we're below the target range but better than our current best, update
        if node_count > 0 and abs(node_count - target_node_count) < abs(best_node_count - target_node_count):
            best_threshold = threshold
            best_node_count = node_count
            best_edge_count = edge_count
    
    return best_threshold, best_node_count, best_edge_count


# Copy of the create_file_affinity_network function from affinity_groups.py
def create_file_affinity_network(commits, min_affinity=0.5, max_nodes=50):
    """
    Create a network graph of file affinities based on commit history.
    
    Args:
        commits: Iterable of commit objects
        min_affinity: Minimum affinity threshold for including edges
        max_nodes: Maximum number of nodes to include in the graph
        
    Returns:
        A tuple of (networkx graph, communities)
    """
    if not commits:
        return nx.Graph(), []
        
    # Calculate affinities as in strongest_pairings.py
    affinities = defaultdict(float)
    for commit in commits:
        files_in_commit = len(commit.stats.files)
        if files_in_commit < 2:
            continue
        for combo in combinations(commit.stats.files, 2):
            ordered_key = tuple(sorted(combo))
            affinities[ordered_key] += 1 / files_in_commit
    
    # Create a network graph
    G = nx.Graph()
    
    # Add nodes (files)
    all_files = set()
    for file_pair in affinities.keys():
        all_files.update(file_pair)
    
    # Sort files by their total affinity and limit to max_nodes
    file_total_affinity = defaultdict(float)
    for (file1, file2), affinity in affinities.items():
        file_total_affinity[file1] += affinity
        file_total_affinity[file2] += affinity
    
    top_files = sorted(file_total_affinity.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
    top_file_set = {file for file, _ in top_files}
    
    # Add nodes for top files
    for file in top_file_set:
        G.add_node(file)
    
    # Add edges with weights based on affinity
    for (file1, file2), affinity in affinities.items():
        if file1 in top_file_set and file2 in top_file_set and affinity >= min_affinity:
            G.add_edge(file1, file2, weight=affinity)
    
    # Find communities/clusters using Louvain method
    # Check if the graph has any nodes before calling louvain_communities
    if len(G.nodes()) > 0:
        communities = nx.community.louvain_communities(G)
        
        # Assign community ID to each node
        for i, community in enumerate(communities):
            for node in community:
                G.nodes[node]['community'] = i
    else:
        # Return empty communities list if graph is empty
        communities = []
    
    return G, communities


def create_mock_commit(commit_data):
    """
    Create a mock commit object from simplified commit data.
    
    Args:
        commit_data: Dictionary with commit data
        
    Returns:
        A mock commit object with the necessary attributes
    """
    class MockCommit:
        def __init__(self, data):
            self.hexsha = data['hash']
            self.message = data['message']
            self.committed_date = datetime.fromisoformat(data['date']).timestamp()
            self.committed_datetime = datetime.fromisoformat(data['date'])
            
            class MockStats:
                def __init__(self, files):
                    self.files = {file: {'insertions': 1, 'deletions': 1} for file in files}
            
            self.stats = MockStats(data['files'])
    
    return MockCommit(commit_data)


def load_commits_data(period):
    """
    Load commit data from a file.
    
    Args:
        period: Time period string
        
    Returns:
        List of simplified commit objects
    """
    filename = f"commits_{period.replace(' ', '_').lower()}.json"
    filepath = TEST_DATA_DIR / filename
    
    if not filepath.exists():
        print(f"No saved data found for {period}")
        return None
    
    with open(filepath, 'r') as f:
        commits = json.load(f)
    
    print(f"Loaded {len(commits)} commits from {filepath}")
    return commits


def test_calculate_ideal_affinity_with_real_data():
    """Test the calculate_ideal_affinity function with real commit data."""
    print("\nTesting calculate_ideal_affinity with real data...")
    
    # Test periods
    test_periods = ["Last 6 Months", "Last 1 Year", "Last 5 Years"]
    
    for period in test_periods:
        # Load commit data
        commits_data = load_commits_data(period)
        if not commits_data:
            print(f"Skipping {period} - no data available")
            continue
        
        # Create mock commits
        mock_commits = [create_mock_commit(commit) for commit in commits_data]
        
        # Calculate ideal affinity
        ideal_affinity, node_count, edge_count = calculate_ideal_affinity(
            mock_commits, target_node_count=15, max_nodes=50
        )
        
        print(f"\nResults for {period}:")
        print(f"Ideal affinity: {ideal_affinity:.2f}")
        print(f"Estimated nodes: {node_count}")
        print(f"Estimated edges: {edge_count}")
        
        # Verify the node count is within the expected range (5-20)
        if 5 <= node_count <= 20:
            print(f"✓ Node count {node_count} is within the expected range (5-20)")
        else:
            print(f"✗ Node count {node_count} is outside the expected range (5-20)")
        
        # Verify the result by creating a network with the calculated affinity
        G, communities = create_file_affinity_network(
            mock_commits, min_affinity=ideal_affinity, max_nodes=50
        )
        
        actual_node_count = len(G.nodes())
        actual_edge_count = len(G.edges())
        
        print(f"Actual nodes: {actual_node_count}")
        print(f"Actual edges: {actual_edge_count}")
        
        # Verify the actual node count is within the expected range (5-20)
        if 5 <= actual_node_count <= 20:
            print(f"✓ Actual node count {actual_node_count} is within the expected range (5-20)")
        else:
            print(f"✗ Actual node count {actual_node_count} is outside the expected range (5-20)")


def test_calculate_ideal_affinity_with_edge_cases():
    """Test the calculate_ideal_affinity function with edge cases."""
    print("\nTesting calculate_ideal_affinity with edge cases...")
    
    # Test with empty commits
    print("\nTest with empty commits:")
    ideal_affinity, node_count, edge_count = calculate_ideal_affinity([], target_node_count=15, max_nodes=50)
    print(f"Ideal affinity: {ideal_affinity:.2f}")
    print(f"Estimated nodes: {node_count}")
    print(f"Estimated edges: {edge_count}")
    
    # Test with a single commit
    print("\nTest with a single commit:")
    single_commit = [{
        'hash': '123456',
        'author': 'Test Author',
        'date': '2025-10-23T13:53:00',
        'message': 'Test commit',
        'files': ['file1.py', 'file2.py', 'file3.py']
    }]
    mock_commits = [create_mock_commit(commit) for commit in single_commit]
    ideal_affinity, node_count, edge_count = calculate_ideal_affinity(mock_commits, target_node_count=15, max_nodes=50)
    print(f"Ideal affinity: {ideal_affinity:.2f}")
    print(f"Estimated nodes: {node_count}")
    print(f"Estimated edges: {edge_count}")
    
    # Test with commits that have no file pairs
    print("\nTest with commits that have no file pairs:")
    no_pairs_commits = [
        {
            'hash': '123456',
            'author': 'Test Author',
            'date': '2025-10-23T13:53:00',
            'message': 'Test commit 1',
            'files': ['file1.py']
        },
        {
            'hash': '789012',
            'author': 'Test Author',
            'date': '2025-10-23T14:53:00',
            'message': 'Test commit 2',
            'files': ['file2.py']
        }
    ]
    mock_commits = [create_mock_commit(commit) for commit in no_pairs_commits]
    ideal_affinity, node_count, edge_count = calculate_ideal_affinity(mock_commits, target_node_count=15, max_nodes=50)
    print(f"Ideal affinity: {ideal_affinity:.2f}")
    print(f"Estimated nodes: {node_count}")
    print(f"Estimated edges: {edge_count}")


def test_calculate_ideal_affinity_with_synthetic_data():
    """Test the calculate_ideal_affinity function with synthetic data."""
    print("\nTesting calculate_ideal_affinity with synthetic data...")
    
    # Create synthetic commits with known affinity patterns
    synthetic_commits = []
    
    # Group 1: Files that always change together (high affinity)
    for i in range(5):
        synthetic_commits.append({
            'hash': f'group1_{i}',
            'author': 'Test Author',
            'date': f'2025-10-{23-i}T13:53:00',
            'message': f'Group 1 commit {i}',
            'files': ['group1_file1.py', 'group1_file2.py', 'group1_file3.py']
        })
    
    # Group 2: Files that sometimes change together (medium affinity)
    for i in range(10):
        files = ['group2_file1.py']
        if i % 2 == 0:
            files.append('group2_file2.py')
        if i % 3 == 0:
            files.append('group2_file3.py')
        
        synthetic_commits.append({
            'hash': f'group2_{i}',
            'author': 'Test Author',
            'date': f'2025-09-{30-i}T13:53:00',
            'message': f'Group 2 commit {i}',
            'files': files
        })
    
    # Group 3: Files that rarely change together (low affinity)
    for i in range(20):
        files = ['group3_file1.py']
        if i % 10 == 0:
            files.append('group3_file2.py')
        if i % 15 == 0:
            files.append('group3_file3.py')
        
        synthetic_commits.append({
            'hash': f'group3_{i}',
            'author': 'Test Author',
            'date': f'2025-08-{31-i}T13:53:00',
            'message': f'Group 3 commit {i}',
            'files': files
        })
    
    # Create mock commits
    mock_commits = [create_mock_commit(commit) for commit in synthetic_commits]
    
    # Calculate ideal affinity
    ideal_affinity, node_count, edge_count = calculate_ideal_affinity(
        mock_commits, target_node_count=15, max_nodes=50
    )
    
    print(f"\nResults for synthetic data:")
    print(f"Ideal affinity: {ideal_affinity:.2f}")
    print(f"Estimated nodes: {node_count}")
    print(f"Estimated edges: {edge_count}")
    
    # Verify the node count is within the expected range (5-20)
    if 5 <= node_count <= 20:
        print(f"✓ Node count {node_count} is within the expected range (5-20)")
    else:
        print(f"✗ Node count {node_count} is outside the expected range (5-20)")
    
    # Verify the result by creating a network with the calculated affinity
    G, communities = create_file_affinity_network(
        mock_commits, min_affinity=ideal_affinity, max_nodes=50
    )
    
    actual_node_count = len(G.nodes())
    actual_edge_count = len(G.edges())
    
    print(f"Actual nodes: {actual_node_count}")
    print(f"Actual edges: {actual_edge_count}")
    
    # Verify the actual node count is within the expected range (5-20)
    if 5 <= actual_node_count <= 20:
        print(f"✓ Actual node count {actual_node_count} is within the expected range (5-20)")
    else:
        print(f"✗ Actual node count {actual_node_count} is outside the expected range (5-20)")


def main():
    """Main function to run all tests."""
    # Ensure test data directory exists
    TEST_DATA_DIR.mkdir(exist_ok=True)
    
    # Run tests
    test_calculate_ideal_affinity_with_real_data()
    test_calculate_ideal_affinity_with_edge_cases()
    test_calculate_ideal_affinity_with_synthetic_data()
    
    print("\nAll tests completed!")


if __name__ == "__main__":
    main()