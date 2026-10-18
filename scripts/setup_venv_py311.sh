#!/bin/bash
# Setup script with Python 3.11 virtual environment for Voice Assistant project

echo "========================================="
echo "Voice Assistant - Python 3.11 Virtual Environment Setup"
echo "========================================="
echo ""

PROJECT_DIR="/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"
cd "$PROJECT_DIR"

# Check if Python 3.11 is available
echo "Checking for Python 3.11..."
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
    echo "Found: $(python3.11 --version)"
elif command -v python3 &> /dev/null; then
    version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    if [ "$version" == "3.11" ]; then
        PYTHON_CMD=python3
        echo "Found: $(python3 --version)"
    else
        echo "Warning: Python 3.11 not found. Current: $(python3 --version)"
        echo "Using available Python, but Coqui TTS may not be available."
        PYTHON_CMD=python3
    fi
else
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo ""

# Remove old venv if exists
if [ -d "venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf venv
fi

# Create virtual environment with Python 3.11
echo "Creating virtual environment with $PYTHON_CMD..."
$PYTHON_CMD -m venv venv

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
echo "Python version: $(python --version)"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing project dependencies..."
echo "This may take several minutes (downloading PyTorch, Whisper, etc.)..."
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
echo "Python version: $(python --version)"
echo "Virtual environment is now active."
echo ""
echo "To use the voice assistant:"
echo "  python main.py --text          # Text mode"
echo "  python main.py                 # Voice mode"
echo ""
echo "To run tests:"
echo "  python test_commands.py"
echo ""
echo "To deactivate the virtual environment later:"
echo "  deactivate"
echo ""
echo "To reactivate in the future:"
echo "  source venv/bin/activate"
echo ""
