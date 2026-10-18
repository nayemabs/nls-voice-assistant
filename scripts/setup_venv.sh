#!/bin/bash
# Setup script with virtual environment for Voice Assistant project

echo "========================================="
echo "Voice Assistant - Virtual Environment Setup"
echo "========================================="
echo ""

PROJECT_DIR="/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"
cd "$PROJECT_DIR"

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

echo "Virtual environment created successfully!"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

echo "Virtual environment activated!"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing project dependencies..."
echo "This may take a few minutes..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo ""
echo "========================================="
echo "Setup completed successfully!"
echo "========================================="
echo ""
echo "Virtual environment is now active."
echo ""
echo "To use the voice assistant:"
echo "  1. Make sure the virtual environment is activated:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the assistant:"
echo "     python main.py --text          # Text mode"
echo "     python main.py                 # Voice mode"
echo ""
echo "  3. Run tests:"
echo "     python test_commands.py"
echo ""
echo "To deactivate the virtual environment later:"
echo "  deactivate"
echo ""
