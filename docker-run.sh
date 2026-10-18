#!/bin/bash
# ============================================================
# Voice Assistant Docker Runner
# Automatically selects the best configuration for your system
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Voice Assistant Docker Runner${NC}"
echo -e "${BLUE}============================================${NC}"

# Detect available GPU
detect_gpu() {
    # Check for NVIDIA GPU
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi &> /dev/null; then
            echo "cuda"
            return
        fi
    fi

    # Check for Apple Silicon (MPS not supported in Docker)
    if [[ "$(uname -m)" == "arm64" ]] && [[ "$(uname)" == "Darwin" ]]; then
        echo -e "${YELLOW}Note: Apple Silicon detected but MPS not available in Docker${NC}" >&2
        echo -e "${YELLOW}For GPU acceleration, run natively: python main.py${NC}" >&2
    fi

    echo "cpu"
}

# Parse command line arguments
MODE="cpu"
ACTION="run"
PROFILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --cuda|--gpu)
            MODE="cuda"
            shift
            ;;
        --cpu)
            MODE="cpu"
            shift
            ;;
        --auto)
            MODE="auto"
            shift
            ;;
        --build)
            ACTION="build"
            shift
            ;;
        --evaluate|--eval)
            ACTION="evaluate"
            shift
            ;;
        --shell)
            ACTION="shell"
            shift
            ;;
        --stop)
            ACTION="stop"
            shift
            ;;
        --logs)
            ACTION="logs"
            shift
            ;;
        -h|--help)
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --auto       Auto-detect best GPU (default)"
            echo "  --cuda       Force CUDA/NVIDIA GPU mode"
            echo "  --cpu        Force CPU mode"
            echo "  --build      Build container only"
            echo "  --evaluate   Run evaluation on audio files"
            echo "  --shell      Open shell in container"
            echo "  --stop       Stop running containers"
            echo "  --logs       Show container logs"
            echo "  -h, --help   Show this help"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Auto-detect if not specified
if [[ "$MODE" == "auto" ]] || [[ -z "$PROFILE" ]]; then
    DETECTED=$(detect_gpu)
    if [[ "$MODE" == "auto" ]]; then
        MODE="$DETECTED"
    fi
fi

echo -e "${GREEN}Mode: ${MODE}${NC}"

# Set profile based on mode
case $MODE in
    cuda)
        PROFILE="cuda"
        SERVICE="voice-assistant-cuda"
        echo -e "${GREEN}Using NVIDIA CUDA GPU acceleration${NC}"
        ;;
    cpu)
        PROFILE="cpu"
        SERVICE="voice-assistant"
        echo -e "${YELLOW}Using CPU mode${NC}"
        ;;
esac

# Execute action
case $ACTION in
    build)
        echo -e "\n${BLUE}Building container...${NC}"
        docker compose --profile $PROFILE build
        echo -e "${GREEN}Build complete!${NC}"
        ;;
    run)
        echo -e "\n${BLUE}Starting Voice Assistant...${NC}"
        docker compose --profile $PROFILE up -d $SERVICE
        echo -e "${GREEN}Container started!${NC}"
        echo ""
        echo "To interact with the assistant:"
        echo "  docker attach nls-voice-assistant"
        echo ""
        echo "To detach without stopping: Ctrl+P, Ctrl+Q"
        echo "To stop: ./docker-run.sh --stop"
        ;;
    evaluate)
        echo -e "\n${BLUE}Running evaluation...${NC}"
        docker compose --profile evaluate up evaluator
        ;;
    shell)
        echo -e "\n${BLUE}Opening shell...${NC}"
        docker compose --profile $PROFILE run --rm $SERVICE /bin/bash
        ;;
    stop)
        echo -e "\n${BLUE}Stopping containers...${NC}"
        docker compose --profile cpu --profile cuda down
        echo -e "${GREEN}Containers stopped!${NC}"
        ;;
    logs)
        docker compose logs -f
        ;;
esac
