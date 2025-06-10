@echo off
echo.
echo ========================================
echo  Grasshopper Bridge Test Server
echo ========================================
echo.
echo Starting test server on http://localhost:8001
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
uv run python src/bridge_design_system/mcp/grasshopper_bridge_test_server.py

pause