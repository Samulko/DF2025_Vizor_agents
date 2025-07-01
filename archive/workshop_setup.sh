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

# Show WSL distro and networking info
echo "📋 System Information:"
echo "   Distro: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "   WSL Version: $(wsl.exe -l -v 2>/dev/null | grep -E '\*|default' || echo 'Unknown')"
echo "   Kernel: $(uname -r)"
echo ""

# Show network interfaces
echo "🌐 Network Interfaces:"
ip addr show | grep -E "^[0-9]+:|inet " | sed 's/^/   /'
echo ""

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

# Method 3: Extract all possible IPs from network interfaces
echo "📡 Extracting all network gateway IPs..."
GATEWAY_IPS=()

# Get default gateway
DEFAULT_GW=$(ip route show default | awk '/default/ { print $3 }' | head -1)
if [ ! -z "$DEFAULT_GW" ]; then
    GATEWAY_IPS+=("$DEFAULT_GW")
    echo "   Found default gateway: $DEFAULT_GW"
fi

# Get all gateway IPs from routing table
while IFS= read -r gateway; do
    if [[ ! " ${GATEWAY_IPS[@]} " =~ " ${gateway} " ]]; then
        GATEWAY_IPS+=("$gateway")
        echo "   Found additional gateway: $gateway"
    fi
done < <(ip route | awk '/via/ { print $3 }' | sort -u)

# Method 4: Try network broadcast addresses
echo "📡 Finding network broadcast addresses..."
NETWORK_IPS=()

# Extract network addresses and try .1
while IFS= read -r network; do
    # Convert network/mask to .1 address
    base_ip=$(echo "$network" | cut -d'/' -f1 | cut -d'.' -f1-3)
    test_ip="${base_ip}.1"
    if [[ ! " ${NETWORK_IPS[@]} " =~ " ${test_ip} " ]]; then
        NETWORK_IPS+=("$test_ip")
        echo "   Found network gateway candidate: $test_ip"
    fi
done < <(ip route | awk '/\/[0-9]+/ && !/default/ { print $1 }' | sort -u)

# Method 5: Try common WSL IPs
echo "📡 Adding common WSL IP addresses..."
COMMON_IPS=("172.28.192.1" "172.16.0.1" "192.168.0.1" "10.0.0.1" "192.168.1.1" "192.168.100.1")

# Combine all IPs and remove duplicates
ALL_IPS=("${GATEWAY_IPS[@]}" "${NETWORK_IPS[@]}" "${COMMON_IPS[@]}")
UNIQUE_IPS=($(printf '%s\n' "${ALL_IPS[@]}" | sort -u))

echo "📡 Testing ${#UNIQUE_IPS[@]} potential Windows host IPs..."
for ip in "${UNIQUE_IPS[@]}"; do
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

# Method 6: Manual setup with enhanced debugging
echo ""
echo "❌ Automatic detection failed. Enhanced manual setup:"
echo ""
echo "🔍 Debugging Information:"
echo "   Current WSL networking setup:"
ip route show | sed 's/^/      /'
echo ""
echo "   Current DNS configuration:"
cat /etc/resolv.conf | sed 's/^/      /'
echo ""

echo "📋 Manual Setup Steps:"
echo "1. In Windows, open PowerShell/CMD and run:"
echo "   ipconfig"
echo ""
echo "2. Look for network adapters with IPv4 addresses:"
echo "   • Main network adapter (Ethernet/WiFi)"
echo "   • vEthernet (WSL) - if available"
echo "   • Any adapter with 192.168.x.x, 10.x.x.x, or 172.x.x.x"
echo ""
echo "3. Try each IP address in WSL:"
echo "   export GRASSHOPPER_HOST=192.168.1.100  # Replace with actual IP"
echo "   timeout 5 bash -c 'echo >/dev/tcp/\$GRASSHOPPER_HOST/8081' && echo '✅ Success!' || echo '❌ Failed!'"
echo ""
echo "4. Once you find a working IP, save it:"
echo "   echo 'export GRASSHOPPER_HOST=WORKING_IP_HERE' >> ~/.bashrc"
echo ""
echo "5. Run the agent:"
echo "   uv run python -m src.bridge_design_system.agents.rational_smolagents"
echo ""

echo "🚨 Common Issues & Solutions:"
echo "• No connection: Check if Grasshopper MCP component is running on port 8081"
echo "• WSL1 vs WSL2: Try 'wsl --set-version DISTRO_NAME 2' in Windows"
echo "• Multiple distros: Make sure you're in the correct WSL distro"
echo "• Firewall: Temporarily disable Windows Firewall to test"
echo "• Wrong distro: List all with 'wsl -l -v' in Windows PowerShell"

# Check if Grasshopper is running
echo "🔍 Troubleshooting tips:"
echo "• Make sure Grasshopper is open with the MCP component loaded"
echo "• Check Windows Firewall allows Grasshopper/Rhino"  
echo "• Try temporarily disabling Windows Firewall"
echo "• Make sure the GH_MCPComponent shows port 8081"

echo ""
echo "📋 For more help, see WSL_NETWORKING_GUIDE.md"