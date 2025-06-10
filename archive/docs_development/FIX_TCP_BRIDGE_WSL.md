# Fix TCP Bridge for WSL Connection

## The Problem

The TCP bridge component is currently using `IPAddress.Loopback` which only listens on `localhost` (127.0.0.1). This prevents WSL from connecting because WSL needs to connect via the Windows host IP.

## The Solution

Change line 119 in `GH_MCPComponent.cs`:

**From:**
```csharp
listener = new TcpListener(IPAddress.Loopback, grasshopperPort);
```

**To:**
```csharp
listener = new TcpListener(IPAddress.Any, grasshopperPort);
```

## Steps to Fix

### Option 1: Edit and Rebuild

1. **Edit the file:**
   ```
   reference/GH_MCP/GH_MCP/GH_MCPComponent.cs
   ```
   Change line 119 as shown above

2. **Rebuild in Windows:**
   ```cmd
   cd C:\Users\Samko\Documents\github\vizor_agents\reference\GH_MCP\GH_MCP\
   dotnet build --configuration Release
   ```

3. **Redeploy:**
   ```cmd
   copy "bin\Release\net48\GH_MCP.gha" "%APPDATA%\Grasshopper\Libraries\"
   ```

4. **Restart Grasshopper** and add component again

### Option 2: Use Port Forwarding (No Rebuild)

If you can't rebuild, use Windows port forwarding:

**In Windows PowerShell (Admin):**
```powershell
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8080 connectaddress=127.0.0.1 connectport=8080
```

This forwards all connections on port 8080 to localhost:8080.

**To remove later:**
```powershell
netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=8080
```

### Option 3: Alternative Workaround

Run the MCP bridge test from Windows PowerShell instead of WSL:

1. **Install Python on Windows** (if not already)
2. **In Windows PowerShell:**
   ```powershell
   cd C:\Users\Samko\Documents\github\vizor_agents
   python test_tcp_bridge_simple.py
   ```

## Why This Happens

- **IPAddress.Loopback**: Only binds to 127.0.0.1 (localhost)
- **IPAddress.Any**: Binds to 0.0.0.0 (all interfaces)
- WSL has its own network interface and can't access Windows localhost directly
- Windows host is accessible from WSL via the IP in /etc/resolv.conf

## Security Note

Using `IPAddress.Any` makes the TCP bridge accessible from all network interfaces. For development this is fine, but for production you might want to restrict it to specific IPs.

## Recommended Solution

**For development**: Use Option 1 (rebuild with IPAddress.Any)
**For quick testing**: Use Option 2 (port forwarding)
**For production**: Consider a more secure binding configuration