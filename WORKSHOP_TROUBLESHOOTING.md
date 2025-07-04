# Workshop Troubleshooting Guide

## Quick Start for Students

### Step 1: Check Your WSL Setup
```bash
bash check_wsl_setup.sh
```

### Step 2: Run Automated Setup
```bash
bash workshop_setup.sh
```

### Step 3: If Automated Setup Fails
1. **Check if you have multiple WSL distros:**
   ```cmd
   wsl -l -v
   ```
   Make sure you're in the correct distro!

2. **Find your Windows IP manually:**
   ```cmd
   ipconfig
   ```
   Look for IPv4 addresses in these adapters:
   - `Ethernet adapter Ethernet`
   - `Wireless LAN adapter Wi-Fi`
   - `Ethernet adapter vEthernet (WSL)`

3. **Test the IP in WSL:**
   ```bash
   export GRASSHOPPER_HOST=192.168.1.100  # Replace with your IP
   timeout 5 bash -c "echo >/dev/tcp/$GRASSHOPPER_HOST/8081" && echo "✅ Success!" || echo "❌ Failed!"
   ```

## Common Issues and Solutions

### Issue 1: "No module named 'grasshopper_mcp'"
**Solution:**
```bash
cd src/bridge_design_system/mcp
uv pip install -e .
cd ../../..
```

### Issue 2: "Connection refused" or "Connection failed"
**Causes:**
- Grasshopper isn't running
- MCP component not loaded in Grasshopper
- Wrong IP address
- Windows Firewall blocking

**Solutions:**
1. **Check Grasshopper:**
   - Open Grasshopper
   - Load the MCP component
   - Verify it shows "Listening on port 8081"

2. **Check Windows Firewall:**
   - Windows Security → Firewall & network protection
   - Allow Grasshopper/Rhino through firewall
   - Or temporarily disable for testing

3. **Try different IPs:**
   ```bash
   # Test each IP from your ipconfig output
   export GRASSHOPPER_HOST=192.168.1.100
   timeout 5 bash -c "echo >/dev/tcp/$GRASSHOPPER_HOST/8081" && echo "Works!"
   ```

### Issue 3: Wrong WSL Distro
**Problem:** Student is in wrong WSL distro (e.g., Docker Desktop WSL vs Ubuntu)

**Solution:**
1. **Check current distro:**
   ```bash
   cat /etc/os-release | grep PRETTY_NAME
   ```

2. **Exit and switch to correct distro:**
   ```cmd
   # In Windows Command Prompt
   wsl -d Ubuntu
   # or
   wsl -d Ubuntu-24.04
   ```

3. **Set default distro:**
   ```cmd
   wsl --set-default Ubuntu
   ```

### Issue 4: WSL1 vs WSL2 Networking
**Problem:** WSL1 has different networking than WSL2

**Solution:**
1. **Check WSL version:**
   ```cmd
   wsl -l -v
   ```

2. **Convert to WSL2 if needed:**
   ```cmd
   wsl --set-version Ubuntu 2
   ```

3. **Restart WSL:**
   ```cmd
   wsl --shutdown
   wsl
   ```

### Issue 5: Environment Variables Not Persisting
**Problem:** GRASSHOPPER_HOST resets after closing terminal

**Solution:**
```bash
# Add to ~/.bashrc permanently
echo "export GRASSHOPPER_HOST=192.168.1.100" >> ~/.bashrc
source ~/.bashrc
```

### Issue 6: Multiple Network Adapters
**Problem:** Student has VPN, Docker, or other network adapters

**Solution:**
1. **Try all adapter IPs:**
   ```bash
   # Get all IPs from ipconfig
   # Test each one:
   for ip in 192.168.1.100 10.0.0.1 172.16.0.1; do
     echo "Testing $ip..."
     timeout 3 bash -c "echo >/dev/tcp/$ip/8081" && echo "✅ $ip works!" && break
   done
   ```

## Workshop Instructor Commands

### Quick Health Check
```bash
# Run on student's machine
bash check_wsl_setup.sh
```

### Emergency Manual Setup
```bash
# If everything fails, manual setup:
export GRASSHOPPER_HOST=INSTRUCTOR_PROVIDES_IP
echo "export GRASSHOPPER_HOST=INSTRUCTOR_PROVIDES_IP" >> ~/.bashrc
```

### Common Instructor IPs to Try
- `192.168.1.1` (home router)
- `192.168.0.1` (home router)
- `10.0.0.1` (corporate)
- `172.16.0.1` (VPN/corporate)
- Main Windows adapter IP from `ipconfig`

## Testing Commands

### Test Connection
```bash
timeout 5 bash -c "echo >/dev/tcp/$GRASSHOPPER_HOST/8081" && echo "✅ Connected!" || echo "❌ Failed!"
```

### Test Full Pipeline
```bash
export GRASSHOPPER_HOST=YOUR_IP
uv run python -m src.bridge_design_system.agents.rational_smolagents
```

### Debug Network Issues
```bash
# Show all network info
ip addr show
ip route show
cat /etc/resolv.conf

# Test specific IP
nc -zv 192.168.1.100 8081
```

## Distro-Specific Issues

### Ubuntu
- Usually works well with WSL2
- Default networking should work

### Debian
- May need manual network configuration
- Check `/etc/network/interfaces`

### Alpine
- Different networking stack
- May need `apk add` for tools

### Docker Desktop WSL
- **Don't use this for the workshop!**
- Switch to Ubuntu/Debian distro

## Final Resort Solutions

### Solution 1: Use Windows Host Main IP
```bash
# In Windows, get main adapter IP
ipconfig | findstr "IPv4"
# Use that IP (usually 192.168.1.x or 10.0.0.x)
```

### Solution 2: Port Forwarding
```bash
# If firewall blocks, try different ports
export GRASSHOPPER_PORT=8082
# Update Grasshopper component to use port 8082
```

### Solution 3: Network Bridge
```cmd
# In Windows as Admin (risky)
netsh interface portproxy add v4tov4 listenport=8081 listenaddress=0.0.0.0 connectport=8081 connectaddress=127.0.0.1
```

## Success Indicators

### Working Setup Shows:
- ✅ WSL detection successful
- ✅ IP address found
- ✅ Port 8081 connection successful
- ✅ Environment variable saved
- ✅ Agent runs without timeout errors

### Failing Setup Shows:
- ❌ Connection timeouts
- ❌ "No module named grasshopper_mcp"
- ❌ "Connection refused"
- ❌ Wrong WSL distro
- ❌ Network interface issues