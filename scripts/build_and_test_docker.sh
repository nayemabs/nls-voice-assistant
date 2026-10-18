#!/bin/bash
# Build and test Docker container

echo "==========================================="
echo "Voice Assistant - Docker Build & Test"
echo "==========================================="
echo ""

cd "/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"

# Clean up old builds
echo "Cleaning up old Docker images..."
docker rmi voice-assistant:latest 2>/dev/null || true

# Build the image
echo ""
echo "Building Docker image..."
echo "This may take several minutes..."
docker build -t voice-assistant .

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Docker build failed!"
    exit 1
fi

echo ""
echo "✅ Docker image built successfully!"
echo ""

# Show image size
echo "Image details:"
docker images voice-assistant

echo ""
echo "==========================================="
echo "Running quick test..."
echo "==========================================="
echo ""

# Test Python works
echo "Test 1: Python version"
docker run voice-assistant python --version

echo ""
echo "Test 2: Check modules"
docker run voice-assistant python -c "import modules.nlu; print('✅ Modules imported successfully')"

echo ""
echo "==========================================="
echo "Build and test completed!"
echo "==========================================="
echo ""
echo "To run the voice assistant:"
echo "  docker run -it voice-assistant"
echo ""
echo "Or with docker-compose:"
echo "  docker-compose up"
echo ""
