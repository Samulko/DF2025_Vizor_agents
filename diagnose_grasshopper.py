#!/usr/bin/env python3
"""
Quick diagnostics script for Grasshopper connection issues.
Run this script to test your WSL-Windows Grasshopper connection.
"""

import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("🔍 Grasshopper Connection Diagnostics")
    print("=" * 50)
    
    try:
        from bridge_design_system.mcp.grasshopper_mcp.utils.communication import diagnose_connection
        
        print("Running comprehensive diagnostics...")
        print("This may take a few seconds...\n")
        
        result = diagnose_connection()
        
        print("\n" + "=" * 50)
        print("🏁 Diagnostics Complete!")
        print("=" * 50)
        
        # Check if any connections worked
        working_hosts = []
        for host, info in result.get("connection_tests", {}).items():
            if info.get("tcp_connect"):
                working_hosts.append(host)
        
        if working_hosts:
            print(f"✅ Found working host(s): {', '.join(working_hosts)}")
            print("\n📝 Recommended action:")
            print(f"   export GRASSHOPPER_HOST={working_hosts[0]}")
            print("   # Add this to your ~/.bashrc or ~/.zshrc for persistence")
        else:
            print("❌ No working connections found")
            print("\n🛠️  Next steps:")
            print("1. Start Rhino Grasshopper on Windows")
            print("2. Load the TCP bridge component")
            print("3. Ensure it shows 'Listening on 0.0.0.0:8081'")
            print("4. Check Windows Firewall settings")
        
        return result
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
        return None
    except Exception as e:
        print(f"❌ Diagnostic error: {e}")
        return None

if __name__ == "__main__":
    main()