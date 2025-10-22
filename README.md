# gitminer-dash
A python dash app for visualizing various facts about a git repository

## Getting Started

### Quick Setup
Run the onboard script to set up your environment:

    ./onboard

This script will:
- Check for required dependencies (Python 3.10+, uv, git)
- Offer to install missing dependencies
- Create a virtual environment
- Install all required packages

### Running the Application
You can run the application using the convenient "run" script:

    ./run path-to-local-git-repository

This script will:
- Validate that the provided path is a valid git repository
- Automatically run the onboard script if the virtual environment doesn't exist
- Activate the virtual environment
- Start the application with the provided git repository

Alternatively, you can run the application manually:

    source .venv/bin/activate
    python app.py path-to-local-git-workspace

## Usage Notes
This is not a turbo fast program, and you may have to wait for data loading sometimes.
We can make it more obvious/pretty but for now watch the 'updating' notice in the tab.
Also, if there is a refresh button, it will be greyed out during loading.

Enjoy.