#!/bin/bash
# Set Python version
pyenv local 3.9.15

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "Virtual environment created."
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

echo "Setup complete! Virtual environment is now active."
echo "Run 'python pr_analyses.py' to start the PR analysis."
echo "When finished, type 'deactivate' to exit the virtual environment." 