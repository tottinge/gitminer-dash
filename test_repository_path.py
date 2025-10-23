import sys

def test_repository_path_with_arg():
    print("Testing repository_path() with command-line argument...")
    
    # Set sys.argv with a repository path
    sys.argv = ["app.py", "."]  # Use current directory as repository path
    
    # Import data module after setting sys.argv
    import data
    
    try:
        repo_path = data.repository_path()
        print(f"Repository path: {repo_path}")
        print("Test PASSED: repository_path() returned a value with command-line argument")
        return True
    except Exception as e:
        print(f"Test FAILED: repository_path() raised an exception: {str(e)}")
        return False

def test_repository_path_without_arg():
    print("\nTesting repository_path() without command-line argument...")
    
    # Reset modules to ensure clean import
    if 'data' in sys.modules:
        del sys.modules['data']
    
    # Set sys.argv without a repository path
    sys.argv = ["app.py"]
    
    # Import data module after setting sys.argv
    import data
    
    try:
        repo_path = data.repository_path()
        print(f"Repository path: {repo_path}")
        print("Test FAILED: repository_path() should have raised an exception without command-line argument")
        return False
    except ValueError as e:
        print(f"Expected exception raised: {str(e)}")
        print("Test PASSED: repository_path() correctly raised ValueError without command-line argument")
        return True
    except Exception as e:
        print(f"Test FAILED: repository_path() raised an unexpected exception: {str(e)}")
        return False

if __name__ == "__main__":
    # Run the tests
    with_arg_result = test_repository_path_with_arg()
    without_arg_result = test_repository_path_without_arg()
    
    # Print summary
    print("\nTest Summary:")
    print(f"repository_path() with command-line argument: {'PASSED' if with_arg_result else 'FAILED'}")
    print(f"repository_path() without command-line argument: {'PASSED' if without_arg_result else 'FAILED'}")
    
    # Overall result
    if with_arg_result and without_arg_result:
        print("\nAll tests PASSED!")
        sys.exit(0)
    else:
        print("\nSome tests FAILED!")
        sys.exit(1)