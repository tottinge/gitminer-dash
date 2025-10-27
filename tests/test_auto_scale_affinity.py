#!/usr/bin/env python3
"""
Test script for the auto-scaling affinity factor.

This script tests the find_affinity_range function to ensure it correctly
calculates the minimum, maximum, and ideal affinity values.
"""


# Import from tests package to set up path
from tests import setup_path
setup_path()  # This ensures we can import modules from the project root
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dash import Dash

# Create a Dash app instance to prevent PageError when importing pages
app = Dash(__name__, suppress_callback_exceptions=True)

# Import project modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Import after Dash app instantiation to avoid PageError
from pages.affinity_groups import find_affinity_range

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

# Test data directory
TEST_DATA_DIR = Path(os.path.join(os.path.dirname(__file__), "test_data"))


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


def test_find_affinity_range_with_real_data():
    """Test the find_affinity_range function with real commit data."""
    print("\nTesting find_affinity_range with real data...")
    
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
        
        # Find affinity range
        min_affinity, max_affinity, ideal_affinity = find_affinity_range(
            mock_commits, max_nodes=50
        )
        
        print(f"\nResults for {period}:")
        print(f"Min affinity: {min_affinity:.2f}")
        print(f"Ideal affinity: {ideal_affinity:.2f}")
        print(f"Max affinity: {max_affinity:.2f}")
        
        # Verify the min is less than or equal to the ideal, which is less than or equal to the max
        if min_affinity <= ideal_affinity <= max_affinity:
            print(f"✓ Affinity range is valid: {min_affinity:.2f} <= {ideal_affinity:.2f} <= {max_affinity:.2f}")
        else:
            print(f"✗ Affinity range is invalid: {min_affinity:.2f} <= {ideal_affinity:.2f} <= {max_affinity:.2f}")


def test_find_affinity_range_with_edge_cases():
    """Test the find_affinity_range function with edge cases."""
    print("\nTesting find_affinity_range with edge cases...")
    
    # Test with empty commits
    print("\nTest with empty commits:")
    min_affinity, max_affinity, ideal_affinity = find_affinity_range([], max_nodes=50)
    print(f"Min affinity: {min_affinity:.2f}")
    print(f"Ideal affinity: {ideal_affinity:.2f}")
    print(f"Max affinity: {max_affinity:.2f}")
    
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
    min_affinity, max_affinity, ideal_affinity = find_affinity_range(mock_commits, max_nodes=50)
    print(f"Min affinity: {min_affinity:.2f}")
    print(f"Ideal affinity: {ideal_affinity:.2f}")
    print(f"Max affinity: {max_affinity:.2f}")


def main():
    """Run all tests."""
    print("Testing auto-scaling affinity factor...")
    
    test_find_affinity_range_with_real_data()
    test_find_affinity_range_with_edge_cases()
    
    print("\nAll tests completed.")


if __name__ == "__main__":
    main()