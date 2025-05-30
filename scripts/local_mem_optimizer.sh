#!/bin/bash
set -e

echo "=== AetheroOS Local Memory Optimizer ==="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$ROOT_DIR/data"
LOG_DIR="$ROOT_DIR/logs"

# Parse arguments
CLEANUP=false
AGGRESSIVE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --cleanup)
            CLEANUP=true
            shift
            ;;
        --aggressive)
            AGGRESSIVE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to optimize process memory
optimize_process() {
    local service=$1
    local pid_file="$LOG_DIR/${service}.pid"
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Optimizing $service (PID: $pid)..."
            # Send SIGQUIT to trigger Python garbage collection
            kill -SIGQUIT "$pid" 2>/dev/null || true
        else
            echo "Warning: $service is not running"
        fi
    else
        echo "Warning: PID file not found for $service"
    fi
}

# Function to cleanup memory data
cleanup_memory() {
    echo "Cleaning up memory data..."
    
    # Stop memory service
    "$SCRIPT_DIR/local_service_manager.sh" stop
    
    # Clear memory data
    if [ "$AGGRESSIVE" = true ]; then
        echo "Performing aggressive cleanup..."
        rm -rf "$DATA_DIR/aethero_mem"/*
        rm -rf "$LOG_DIR"/*.log
    else
        echo "Performing standard cleanup..."
        find "$DATA_DIR/aethero_mem" -type f -mtime +7 -delete
        find "$LOG_DIR" -name "*.log" -mtime +7 -delete
    fi
    
    # Restart memory service
    "$SCRIPT_DIR/local_service_manager.sh" start
}

# Main optimization process
echo "Starting memory optimization..."

# List of services to optimize
SERVICES=("aethero_mem" "reflection_agent" "planner_agent" "scout_agent" "analyst_agent" "langgraph")

for service in "${SERVICES[@]}"; do
    optimize_process "$service"
done

# Perform cleanup if requested
if [ "$CLEANUP" = true ]; then
    cleanup_memory
fi

# Verify optimization
echo "Verifying optimization results..."

# Check memory usage after optimization
for service in "${SERVICES[@]}"; do
    pid_file="$LOG_DIR/${service}.pid"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            mem_usage=$(ps -o %mem -p "$pid" | tail -n 1)
            echo "$service memory usage: $mem_usage%"
            
            if (( $(echo "$mem_usage > 80" | bc -l) )); then
                echo "Warning: High memory usage in $service"
            fi
        fi
    fi
done

echo "Memory optimization complete!"

# Return status
if [ "$CLEANUP" = true ]; then
    echo "Cleanup completed successfully"
fi

if [ "$AGGRESSIVE" = true ]; then
    echo "Aggressive optimization completed"
fi

exit 0
