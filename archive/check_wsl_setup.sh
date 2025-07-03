#!/bin/bash

# Quick WSL Setup Checker for Workshop Students
echo "🔍 WSL Setup Checker"
echo "===================="

# Check if in WSL
if [[ ! $(uname -r) =~ microsoft ]]; then
    echo "❌ Not running in WSL"
    echo "   Run this script inside WSL (Ubuntu, Debian, etc.)"
    exit 1
fi

echo "✅ Running in WSL"
echo ""

# Show current distro info
echo "📋 Current WSL Distro:"
echo "   Name: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "   Version: $(cat /etc/os-release | grep VERSION= | cut -d'"' -f2)"
echo "   Kernel: $(uname -r)"
echo ""

# Show Windows WSL info (if available)
echo "🪟 Windows WSL Status:"
if command -v wsl.exe >/dev/null 2>&1; then
    echo "   Available distros:"
    wsl.exe -l -v 2>/dev/null | sed 's/^/      /' || echo "      Unable to get WSL list"
else
    echo "   wsl.exe not available (normal in WSL environment)"
fi
echo ""

# Network diagnostics
echo "🌐 Network Configuration:"
echo "   Network interfaces:"
ip addr show | grep -E "^[0-9]+:|inet " | sed 's/^/      /'
echo ""

echo "   Routing table:"
ip route show | sed 's/^/      /'
echo ""

echo "   DNS servers:"
cat /etc/resolv.conf | grep nameserver | sed 's/^/      /'
echo ""

# Test common Windows host IPs
echo "🧪 Testing Common Windows Host IPs:"
TEST_IPS=("172.28.192.1" "172.16.0.1" "192.168.0.1" "192.168.1.1" "10.0.0.1")

for ip in "${TEST_IPS[@]}"; do
    printf "   %-15s: " "$ip"
    if timeout 2 bash -c "echo >/dev/tcp/$ip/8081" 2>/dev/null; then
        echo "✅ Reachable on port 8081"
    else
        echo "❌ Not reachable"
    fi
done
echo ""

# Check if environment variable is set
echo "🔧 Environment Check:"
if [ ! -z "$GRASSHOPPER_HOST" ]; then
    echo "   GRASSHOPPER_HOST is set to: $GRASSHOPPER_HOST"
    printf "   Testing connection: "
    if timeout 3 bash -c "echo >/dev/tcp/$GRASSHOPPER_HOST/8081" 2>/dev/null; then
        echo "✅ Working"
    else
        echo "❌ Not working"
    fi
else
    echo "   GRASSHOPPER_HOST is not set"
fi
echo ""

echo "💡 Next Steps:"
echo "1. If no IPs work, run 'ipconfig' in Windows to find your actual IP"
echo "2. Make sure Grasshopper is open with MCP component loaded"
echo "3. Try: export GRASSHOPPER_HOST=YOUR_WINDOWS_IP"
echo "4. Test: timeout 5 bash -c 'echo >/dev/tcp/\$GRASSHOPPER_HOST/8081' && echo 'Success!'"