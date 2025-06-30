#!/bin/bash

# Workshop Setup Script for WSL Networking Issues
# This script helps students with Windows Home edition connect to Grasshopper

echo "🔧 Workshop WSL Networking Setup"
echo "================================="

# Check if running in WSL
if [[ ! $(uname -r) =~ microsoft ]]; then
    echo "❌ This script should be run inside WSL"
    exit 1
fi

echo "✅ Running in WSL"

# Method 1: Try automatic detection
echo "📡 Attempting automatic Windows host detection..."

# Check default route
DEFAULT_IP=$(ip route show | grep default | awk '{print $3}' | head -1)
if [ ! -z "$DEFAULT_IP" ]; then
    echo "🔍 Found default route IP: $DEFAULT_IP"
    
    # Test connection
    echo "🧪 Testing connection to $DEFAULT_IP:8081..."
    if timeout 5 bash -c "echo >/dev/tcp/$DEFAULT_IP/8081" 2>/dev/null; then
        echo "✅ Connection successful!"
        export GRASSHOPPER_HOST=$DEFAULT_IP
        echo "export GRASSHOPPER_HOST=$DEFAULT_IP" >> ~/.bashrc
        echo "💾 Saved GRASSHOPPER_HOST=$DEFAULT_IP to ~/.bashrc"
        echo "🚀 You can now run: uv run python -m src.bridge_design_system.agents.rational_smolagents"
        exit 0
    else
        echo "❌ Cannot connect to $DEFAULT_IP:8081"
    fi
fi

# Method 2: Check resolv.conf
echo "📡 Checking /etc/resolv.conf..."
RESOLV_IP=$(grep nameserver /etc/resolv.conf | awk '{print $2}' | head -1)
if [ ! -z "$RESOLV_IP" ]; then
    echo "🔍 Found nameserver IP: $RESOLV_IP"
    
    # Test connection
    echo "🧪 Testing connection to $RESOLV_IP:8081..."
    if timeout 5 bash -c "echo >/dev/tcp/$RESOLV_IP/8081" 2>/dev/null; then
        echo "✅ Connection successful!"
        export GRASSHOPPER_HOST=$RESOLV_IP
        echo "export GRASSHOPPER_HOST=$RESOLV_IP" >> ~/.bashrc
        echo "💾 Saved GRASSHOPPER_HOST=$RESOLV_IP to ~/.bashrc"
        echo "🚀 You can now run: uv run python -m src.bridge_design_system.agents.rational_smolagents"
        exit 0
    else
        echo "❌ Cannot connect to $RESOLV_IP:8081"
    fi
fi

# Method 3: Try common Windows Home IPs
echo "📡 Trying common Windows Home IP addresses..."
COMMON_IPS=("172.28.192.1" "172.16.0.1" "192.168.0.1" "10.0.0.1")

for ip in "${COMMON_IPS[@]}"; do
    echo "🧪 Testing $ip:8081..."
    if timeout 3 bash -c "echo >/dev/tcp/$ip/8081" 2>/dev/null; then
        echo "✅ Connection successful to $ip!"
        export GRASSHOPPER_HOST=$ip
        echo "export GRASSHOPPER_HOST=$ip" >> ~/.bashrc
        echo "💾 Saved GRASSHOPPER_HOST=$ip to ~/.bashrc"
        echo "🚀 You can now run: uv run python -m src.bridge_design_system.agents.rational_smolagents"
        exit 0
    fi
done

# Method 4: Manual setup
echo ""
echo "❌ Automatic detection failed. Manual setup required:"
echo ""
echo "1. In Windows, open PowerShell and run:"
echo "   ipconfig"
echo ""
echo "2. Look for your main network adapter's IPv4 Address (e.g., 192.168.1.100)"
echo ""
echo "3. In WSL, run:"
echo "   export GRASSHOPPER_HOST=YOUR_IP_HERE"
echo "   echo 'export GRASSHOPPER_HOST=YOUR_IP_HERE' >> ~/.bashrc"
echo ""
echo "4. Test the connection:"
echo "   timeout 5 bash -c 'echo >/dev/tcp/YOUR_IP_HERE/8081' && echo 'Success!' || echo 'Failed!'"
echo ""
echo "5. If successful, run the agent:"
echo "   uv run python -m src.bridge_design_system.agents.rational_smolagents"
echo ""

# Check if Grasshopper is running
echo "🔍 Troubleshooting tips:"
echo "• Make sure Grasshopper is open with the MCP component loaded"
echo "• Check Windows Firewall allows Grasshopper/Rhino"  
echo "• Try temporarily disabling Windows Firewall"
echo "• Make sure the GH_MCPComponent shows port 8081"

echo ""
echo "📋 For more help, see WSL_NETWORKING_GUIDE.md"