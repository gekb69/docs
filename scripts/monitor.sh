#!/bin/bash

echo "📊 Monitoring Super Agent..."

# Function to check service health
check_service() {
    local name=$1
    local protocol=$2
    local host=$3
    local port=$4
    local timeout=$5

    if [ "$protocol" == "http" ]; then
        if curl -s --max-time $timeout "http://$host:$port" > /dev/null 2>&1; then
            echo "✅ $name is healthy"
            return 0
        else
            echo "❌ $name is down"
            return 1
        fi
    elif [ "$protocol" == "tcp" ]; then
        if nc -z -w $timeout $host $port > /dev/null 2>&1; then
            echo "✅ $name is healthy"
            return 0
        else
            echo "❌ $name is down"
            return 1
        fi
    fi
}

# Check all services
while true; do
    clear
    echo "===== Super Agent Monitor ($(date)) ====="

    check_service "Redis" "tcp" "localhost" "6379" 2
    check_service "Warp Core" "http" "localhost" "8080" 1
    check_service "Master Agent" "http" "localhost" "8000" 1
    check_service "Sharded Vault" "tcp" "localhost" "9000" 1

    # System resources
    echo ""
    echo "💾 System Resources:"
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')"
    echo "RAM: $(free -h | awk 'NR==2{print $3"/"$2}')"
    echo "Disk: $(df -h / | awk 'NR==2{print $3"/"$2}')"

    echo ""
    echo "Press Ctrl+C to stop monitoring..."
    sleep 5
done
