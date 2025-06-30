# WSL Networking Guide for Workshop Students

If you're having trouble connecting from WSL to Grasshopper on Windows, try these solutions in order:

## Solution 1: Find Your Windows IP (Recommended)

1. **In WSL, run these commands to find your Windows IP:**
   ```bash
   ip route show | grep default
   # Look for something like: default via 172.28.192.1 dev eth0
   ```

2. **Or check your Windows host IP:**
   ```bash
   cat /etc/resolv.conf | grep nameserver
   # Look for something like: nameserver 172.28.192.1
   ```

3. **Set the environment variable with your actual IP:**
   ```bash
   export GRASSHOPPER_HOST=172.28.192.1  # Use YOUR actual IP
   uv run python -m src.bridge_design_system.agents.rational_smolagents
   ```

## Solution 2: Use Windows IP Command

1. **In Windows PowerShell/CMD:**
   ```cmd
   ipconfig
   ```
   Look for your main network adapter's IP address

2. **In WSL, set the environment variable:**
   ```bash
   export GRASSHOPPER_HOST=192.168.1.100  # Use YOUR Windows IP
   uv run python -m src.bridge_design_system.agents.rational_smolagents
   ```

## Solution 3: Alternative WSL IP Detection

If the above don't work, try:

```bash
# Get Windows host IP via WSL2 method
export GRASSHOPPER_HOST=$(ip route show | grep default | awk '{print $3}')
echo "Using Windows host: $GRASSHOPPER_HOST"
uv run python -m src.bridge_design_system.agents.rational_smolagents
```

## Solution 4: Windows Firewall Check

If you can find the IP but still can't connect:

1. **Check Windows Firewall:**
   - Open Windows Defender Firewall
   - Allow an app through firewall
   - Make sure Grasshopper/Rhino is allowed for "Private networks"

2. **Or temporarily disable firewall for testing:**
   - Windows Security → Firewall & network protection
   - Turn off for Private network (temporarily)

## Solution 5: Alternative Ports

If port 8081 is blocked:

```bash
export GRASSHOPPER_HOST=YOUR_IP
export GRASSHOPPER_PORT=8082  # Try different port
uv run python -m src.bridge_design_system.agents.rational_smolagents
```

## Quick Test Script

Create a file `test_connection.py`:

```python
import socket
import os

host = os.environ.get("GRASSHOPPER_HOST", "172.28.192.1")
port = int(os.environ.get("GRASSHOPPER_PORT", "8081"))

print(f"Testing connection to {host}:{port}")

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((host, port))
    if result == 0:
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed")
    sock.close()
except Exception as e:
    print(f"❌ Error: {e}")
```

Run it:
```bash
export GRASSHOPPER_HOST=YOUR_IP
python test_connection.py
```

## Windows Home Edition Fix

If students don't see `vEthernet (WSL (Hyper-V firewall))` in ipconfig (common on Windows Home):

### Method 1: Enable WSL2 Features
1. **Run as Administrator in PowerShell:**
   ```powershell
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   ```

2. **Restart Windows**

3. **Set WSL2 as default:**
   ```powershell
   wsl --set-default-version 2
   ```

4. **Update WSL kernel:**
   ```powershell
   wsl --update
   ```

### Method 2: Manual Network Bridge Setup
If WSL2 networking still doesn't work:

1. **In Windows PowerShell (as Admin):**
   ```powershell
   # Find your main network adapter
   Get-NetAdapter | Where-Object {$_.Status -eq "Up"}
   
   # Note the InterfaceDescription of your main adapter
   ```

2. **Create network bridge (risky - may lose internet):**
   ```powershell
   # Only if you know what you're doing
   New-NetBridge -Name "WSL-Bridge" -NetAdapterName "Ethernet", "vEthernet (WSL)"
   ```

### Method 3: Use Windows Main IP (Simplest)
1. **Find Windows main IP:**
   ```cmd
   ipconfig | findstr IPv4
   ```

2. **In WSL, use that IP:**
   ```bash
   export GRASSHOPPER_HOST=192.168.1.100  # Your main Windows IP
   ```

## Workshop Quick Fix

For the workshop, instructors can have students run:

### Automated Setup Script
```bash
# Run the automated setup script (recommended)
./workshop_setup.sh
```

### Manual Commands
```bash
# Find Windows IP
WINDOWS_IP=$(ip route show | grep default | awk '{print $3}')
echo "Your Windows IP is: $WINDOWS_IP"

# Set environment variable
export GRASSHOPPER_HOST=$WINDOWS_IP

# Test connection first
python -c "import socket; sock=socket.socket(); sock.settimeout(5); print('✅ Success' if sock.connect_ex(('$WINDOWS_IP', 8081))==0 else '❌ Failed'); sock.close()"

# Run the agent
uv run python -m src.bridge_design_system.agents.rational_smolagents
```

### Windows Home Students
If students have Windows Home and missing the WSL virtual adapter:

1. **Use the automated script:** `./workshop_setup.sh`
2. **Or manually find Windows main IP:**
   - Windows: `ipconfig` → look for main adapter IPv4
   - WSL: `export GRASSHOPPER_HOST=192.168.1.XXX` (their actual IP)

## Troubleshooting

- **Connection refused**: Grasshopper component not running or wrong IP
- **Timeout**: Windows firewall blocking or wrong port
- **Host unreachable**: Wrong IP address or network issue

## Environment Variables Reference

- `GRASSHOPPER_HOST`: Override Windows host IP detection
- `GRASSHOPPER_PORT`: Override port (default: 8081)

Example:
```bash
export GRASSHOPPER_HOST=192.168.1.100
export GRASSHOPPER_PORT=8081
```