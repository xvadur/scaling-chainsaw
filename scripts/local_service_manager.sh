#!/bin/bash
set -e

echo "=== AetheroOS Local Service Manager ==="

# Directory setup
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$ROOT_DIR/logs"
DATA_DIR="$ROOT_DIR/data"

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$DATA_DIR/aethero_mem"
mkdir -p "$DATA_DIR/prometheus"
mkdir -p "$DATA_DIR/grafana"

# Function to start a Python service
start_service() {
    local service_name=$1
    local module_path=$2
    local log_file="$LOG_DIR/${service_name}.log"
    
    echo "Starting $service_name..."
    python3 -m "$module_path" > "$log_file" 2>&1 &
    echo $! > "$LOG_DIR/${service_name}.pid"
}

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="$LOG_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        echo "Stopping $service_name (PID: $pid)..."
        kill -15 "$pid" 2>/dev/null || true
        rm "$pid_file"
    fi
}

# Function to check service status
check_service() {
    local service_name=$1
    local pid_file="$LOG_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "$service_name is running (PID: $pid)"
            return 0
        fi
    fi
    echo "$service_name is not running"
    return 1
}

# Start all services
start_all() {
    # Start core services
    start_service "aethero_mem" "aetheros_protocol.memory.mem_service"
    sleep 2
    
    # Start agent services
    start_service "reflection_agent" "aetheros_protocol.reflection.reflection_agent"
    start_service "planner_agent" "aetheros_protocol.agents.planner_agent"
    start_service "scout_agent" "aetheros_protocol.agents.scout_agent"
    start_service "analyst_agent" "aetheros_protocol.agents.analyst_agent"
    
    # Start visualization
    start_service "langgraph" "aetheros_protocol.visualization.langgraph_server"
    
    echo "All services started"
}

# Stop all services
stop_all() {
    services=("langgraph" "analyst_agent" "scout_agent" "planner_agent" "reflection_agent" "aethero_mem")
    
    for service in "${services[@]}"; do
        stop_service "$service"
    done
    
    echo "All services stopped"
}

# Check status of all services
status_all() {
    services=("aethero_mem" "reflection_agent" "planner_agent" "scout_agent" "analyst_agent" "langgraph")
    
    for service in "${services[@]}"; do
        check_service "$service"
    done
}

# Restart all services
restart_all() {
    echo "Restarting all services..."
    stop_all
    sleep 2
    start_all
}

# Parse command line arguments
case "$1" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        status_all
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
