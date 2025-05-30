#!/bin/bash
set -e

echo "=== AetheroOS REŽIM II Local Deployment Script ==="
echo "Initializing deployment..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Create necessary directories
mkdir -p "$ROOT_DIR/logs"
mkdir -p "$ROOT_DIR/data/aethero_mem"

# Check required dependencies
echo "Checking dependencies..."
REQUIRED_COMMANDS=("python3" "pip3" "git")
for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Error: $cmd is required but not installed."
        exit 1
    fi
done

# Setup Python virtual environment
echo "Setting up Python environment..."
cd "$ROOT_DIR"
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize configuration
echo "Initializing configuration..."
cp config/aetheroos_sovereign_agent_stack_v1.0.yaml config/active_config.yaml

# Run tests
echo "Running test suite..."
python -m pytest tests/ -v

# Initialize memory system
echo "Initializing memory system..."
python -m aetheros_protocol.memory.init_db

# Start all services using local service manager
echo "Starting services..."
"$ROOT_DIR/scripts/local_service_manager.sh" start

# Verify deployment
echo "Verifying deployment..."
python -m aetheros_protocol.deploy.verify_deployment

# Print status
echo "=== Deployment Status ==="
echo "Agent Services:"
"$ROOT_DIR/scripts/local_service_manager.sh" status

echo
echo "Memory System: Running"
echo "LangGraph: Running"
echo
echo "Deployment complete! System is ready."

# Trap cleanup on script exit
cleanup() {
    echo "Cleaning up..."
    deactivate
}
trap cleanup EXIT

echo "Press Ctrl+C to shutdown..."
wait
