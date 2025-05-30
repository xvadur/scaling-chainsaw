#!/bin/bash
set -e

echo "=== AetheroOS Memory Optimizer ==="

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

# Function to check container existence
check_container() {
    docker ps -q -f name=$1
}

# Function to optimize container memory
optimize_container() {
    local container=$1
    echo "Optimizing container: $container"
    
    if [ "$AGGRESSIVE" = true ]; then
        echo "Performing aggressive memory optimization..."
        docker exec $container sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'
    else
        echo "Performing standard memory optimization..."
        docker exec $container sh -c 'sync; echo 1 > /proc/sys/vm/drop_caches'
    fi
}

# Function to cleanup memory data
cleanup_memory() {
    echo "Cleaning up memory data..."
    
    # Stop services that might be writing to memory
    docker-compose -f ../agents/docker-compose.yml stop aethero_mem
    
    # Clear memory data
    if [ "$AGGRESSIVE" = true ]; then
        echo "Performing aggressive cleanup..."
        rm -rf ../data/aethero_mem/*
    else
        echo "Performing standard cleanup..."
        find ../data/aethero_mem -type f -mtime +7 -delete
    fi
    
    # Restart services
    docker-compose -f ../agents/docker-compose.yml start aethero_mem
}

# Main optimization process
echo "Starting memory optimization..."

# Check for running containers
CONTAINERS=("aetheros_mem" "aetheros_reflection" "aetheros_planner" "aetheros_scout" "aetheros_analyst")

for container in "${CONTAINERS[@]}"; do
    if [ -n "$(check_container $container)" ]; then
        optimize_container $container
    else
        echo "Warning: Container $container not found"
    fi
done

# Perform cleanup if requested
if [ "$CLEANUP" = true ]; then
    cleanup_memory
fi

# Verify optimization
echo "Verifying optimization results..."

# Check memory usage after optimization
for container in "${CONTAINERS[@]}"; do
    if [ -n "$(check_container $container)" ]; then
        MEMORY_USAGE=$(docker stats $container --no-stream --format "{{.MemPerc}}" | cut -d'%' -f1)
        echo "$container memory usage: $MEMORY_USAGE%"
        
        if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
            echo "Warning: High memory usage in $container"
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
