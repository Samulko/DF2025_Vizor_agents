# Grasshopper Bridge Test Helper Script

Write-Host "🧪 Grasshopper Bridge Test Helper" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""

# Get script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptPath

# Menu
Write-Host "Choose an option:" -ForegroundColor Yellow
Write-Host "1. Start Test Server" -ForegroundColor White
Write-Host "2. Run Interactive Test Client" -ForegroundColor White  
Write-Host "3. Monitor Bridge Activity" -ForegroundColor White
Write-Host "4. Check Server Status" -ForegroundColor White
Write-Host "5. Quick Component Test" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host "🚀 Starting test server..." -ForegroundColor Green
        Write-Host "Server will be available at http://localhost:8001" -ForegroundColor Cyan
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
        Write-Host ""
        uv run python src/bridge_design_system/mcp/grasshopper_bridge_test_server.py
    }
    "2" {
        Write-Host "🎮 Starting interactive test client..." -ForegroundColor Green
        uv run python test_grasshopper_bridge.py
    }
    "3" {
        Write-Host "👀 Monitoring bridge activity..." -ForegroundColor Green
        Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
        uv run python test_grasshopper_bridge.py monitor
    }
    "4" {
        Write-Host "📊 Checking server status..." -ForegroundColor Green
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8001/test/status" -Method Get
            Write-Host "Server Status:" -ForegroundColor Green
            $response | ConvertTo-Json -Depth 3 | Write-Host
        }
        catch {
            Write-Host "❌ Server not responding. Is it running?" -ForegroundColor Red
        }
    }
    "5" {
        Write-Host "⚡ Running quick component test..." -ForegroundColor Green
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8001/test/add_point_component" -Method Post
            Write-Host "✅ Point component test sent:" -ForegroundColor Green
            $response | ConvertTo-Json | Write-Host
            Write-Host ""
            Write-Host "Check your Grasshopper canvas for a new Point component!" -ForegroundColor Cyan
        }
        catch {
            Write-Host "❌ Failed to send test command. Is the server running?" -ForegroundColor Red
        }
    }
    default {
        Write-Host "❌ Invalid choice" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")