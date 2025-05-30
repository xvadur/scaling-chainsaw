#!/bin/bash
set -e

echo "=== AetheroOS REŽIM II Deployment Script ==="
echo "Initializing deployment..."

# Create necessary directories
mkdir -p logs
mkdir -p data/aethero_mem
mkdir -p data/prometheus
mkdir -p data/grafana

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required dependencies
echo "Checking dependencies..."
REQUIRED_COMMANDS=("docker" "docker-compose" "python3" "pip3" "git")
for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command_exists "$cmd"; then
        echo "Error: $cmd is required but not installed."
        exit 1
    fi
done

# Setup Python virtual environment
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize configuration
echo "Initializing configuration..."
cp config/aetheroos_sovereign_agent_stack_v1.0.yaml config/active_config.yaml
cp monitoring/prometheus.yml monitoring/active_prometheus.yml
cp monitoring/grafana_dashboards.json monitoring/active_dashboards.json

# Run tests
echo "Running test suite..."
pytest tests/ -v

# Start monitoring stack
echo "Starting monitoring stack..."
docker-compose -f monitoring/docker-compose.yml up -d prometheus grafana alertmanager

# Wait for monitoring services
echo "Waiting for monitoring services to be ready..."
sleep 10

# Initialize Aethero_Mem
echo "Initializing Aethero_Mem..."
python -m aetheros_protocol.memory.init_db

# Start agent services
echo "Starting AetheroOS agents..."
docker-compose -f agents/docker-compose.yml up -d

# Initialize reflection agent
echo "Initializing reflection agent..."
python -m aetheros_protocol.reflection.reflection_agent &
REFLECTION_PID=$!

# Start visualization service
echo "Starting visualization service..."
python -m aetheros_protocol.visualization.langgraph_server &
VIZ_PID=$!

# Health check
echo "Performing health check..."
./health_check.sh

# Register services with service discovery
echo "Registering services..."
python -m aetheros_protocol.deploy.register_services

# Initialize monitoring
echo "Initializing monitoring..."
curl -X POST http://localhost:9090/-/reload  # Reload Prometheus config
curl -X POST http://localhost:3000/api/admin/provisioning/dashboards/reload  # Reload Grafana dashboards

# Verify deployment
echo "Verifying deployment..."
python -m aetheros_protocol.deploy.verify_deployment

# Print status
echo "=== Deployment Status ==="
echo "Monitoring Stack:"
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000"
echo "- Alertmanager: http://localhost:9093"
echo
echo "Agent Services:"
echo "- ReflectionAgent: Running (PID: $REFLECTION_PID)"
echo "- Visualization: http://localhost:8080"
echo
echo "Aethero_Mem: Running"
echo "LangGraph: Running"
echo
echo "Deployment complete! System is ready."

# Trap cleanup on script exit
cleanup() {
    echo "Cleaning up..."
    kill $REFLECTION_PID
    kill $VIZ_PID
    docker-compose -f monitoring/docker-compose.yml down
    docker-compose -f agents/docker-compose.yml down
    deactivate
}
trap cleanup EXIT

# Keep script running
echo "Press Ctrl+C to shutdown..."
wait
