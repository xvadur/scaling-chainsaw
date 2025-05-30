#!/bin/bash
set -e

echo "=== AetheroOS Health Check ==="

# Function to check HTTP endpoint
check_endpoint() {
    local service=$1
    local url=$2
    local expected_code=$3
    
    echo -n "Checking $service... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" $url)
    
    if [ "$response" = "$expected_code" ]; then
        echo "OK"
        return 0
    else
        echo "FAILED (Expected: $expected_code, Got: $response)"
        return 1
    fi
}

# Function to check Docker container
check_container() {
    local container=$1
    
    echo -n "Checking container $container... "
    
    if docker ps | grep -q $container; then
        echo "OK"
        return 0
    else
        echo "FAILED"
        return 1
    fi
}

# Initialize error counter
errors=0

# Check Monitoring Stack
echo "Monitoring Stack:"
check_endpoint "Prometheus" "http://localhost:9090/-/healthy" "200" || ((errors++))
check_endpoint "Grafana" "http://localhost:3000/api/health" "200" || ((errors++))
check_endpoint "Alertmanager" "http://localhost:9093/-/healthy" "200" || ((errors++))
check_endpoint "Pushgateway" "http://localhost:9091/-/healthy" "200" || ((errors++))

# Check Agent Services
echo -e "\nAgent Services:"
check_container "aetheros_planner" || ((errors++))
check_container "aetheros_scout" || ((errors++))
check_container "aetheros_analyst" || ((errors++))
check_container "aetheros_generator" || ((errors++))
check_container "aetheros_synthesis" || ((errors++))
check_container "aetheros_reflection" || ((errors++))

# Check Core Services
echo -e "\nCore Services:"
check_container "aetheros_mem" || ((errors++))
check_container "aetheros_deepeval" || ((errors++))

# Check API endpoints
echo -e "\nAPI Endpoints:"
check_endpoint "Aethero_Mem API" "http://localhost:9091/health" "200" || ((errors++))
check_endpoint "DeepEval API" "http://localhost:9092/health" "200" || ((errors++))
check_endpoint "Reflection Agent API" "http://localhost:8005/health" "200" || ((errors++))

# Check Metrics
echo -e "\nMetrics Collection:"
check_endpoint "Agent Metrics" "http://localhost:9091/metrics" "200" || ((errors++))
check_endpoint "Memory Metrics" "http://localhost:9091/metrics" "200" || ((errors++))
check_endpoint "DeepEval Metrics" "http://localhost:9092/metrics" "200" || ((errors++))

# Check Memory System
echo -e "\nMemory System:"
if curl -s "http://localhost:9091/api/v1/status" | grep -q "\"status\":\"healthy\""; then
    echo "Aethero_Mem Status... OK"
else
    echo "Aethero_Mem Status... FAILED"
    ((errors++))
fi

# Check Reflection System
echo -e "\nReflection System:"
if curl -s "http://localhost:8005/api/v1/status" | grep -q "\"status\":\"ready\""; then
    echo "Reflection System Status... OK"
else
    echo "Reflection System Status... FAILED"
    ((errors++))
fi

# Final Status
echo -e "\n=== Health Check Summary ==="
if [ $errors -eq 0 ]; then
    echo "All systems operational"
    exit 0
else
    echo "Found $errors error(s)"
    exit 1
fi
