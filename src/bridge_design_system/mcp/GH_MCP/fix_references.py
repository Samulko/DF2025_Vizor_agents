#!/usr/bin/env python3
"""
Fix Grasshopper References Script
This script helps fix the reference paths based on your Rhino installation
"""

import os
import sys
import platform

def find_rhino_installation():
    """Find Rhino installation on the system"""
    
    # Common Rhino installation paths
    if platform.system() == "Windows":
        common_paths = [
            r"C:\Program Files\Rhino 8",
            r"C:\Program Files\Rhino 7",
            r"C:\Program Files\Rhinoceros 5 (64-bit)",
            r"C:\Program Files\Rhinoceros 5",
            # Check Program Files (x86) as well
            r"C:\Program Files (x86)\Rhino 8",
            r"C:\Program Files (x86)\Rhino 7",
        ]
    else:
        print("This script is designed for Windows Rhino installations.")
        return None
    
    for path in common_paths:
        if os.path.exists(path):
            print(f"✓ Found Rhino at: {path}")
            return path
    
    return None

def check_required_dlls(rhino_path):
    """Check if all required DLLs exist"""
    dlls = {
        "Grasshopper.dll": os.path.join(rhino_path, "Plug-ins", "Grasshopper", "Grasshopper.dll"),
        "GH_IO.dll": os.path.join(rhino_path, "Plug-ins", "Grasshopper", "GH_IO.dll"),
        "RhinoCommon.dll": os.path.join(rhino_path, "System", "RhinoCommon.dll")
    }
    
    all_found = True
    print("\nChecking for required DLLs...")
    
    for dll_name, dll_path in dlls.items():
        if os.path.exists(dll_path):
            print(f"✓ Found {dll_name}")
        else:
            print(f"✗ Missing {dll_name}")
            all_found = False
    
    return all_found, dlls

def generate_csproj_references(dlls):
    """Generate the XML for .csproj file"""
    xml = """
  <!-- Grasshopper and Rhino References -->
  <ItemGroup>
    <Reference Include="Grasshopper">
      <HintPath>{}</HintPath>
      <Private>false</Private>
    </Reference>
    <Reference Include="GH_IO">
      <HintPath>{}</HintPath>
      <Private>false</Private>
    </Reference>
    <Reference Include="RhinoCommon">
      <HintPath>{}</HintPath>
      <Private>false</Private>
    </Reference>
  </ItemGroup>
""".format(
        dlls["Grasshopper.dll"],
        dlls["GH_IO.dll"],
        dlls["RhinoCommon.dll"]
    )
    
    return xml

def main():
    print("Grasshopper Reference Fix Helper")
    print("================================")
    print()
    
    # Find Rhino installation
    rhino_path = find_rhino_installation()
    
    if not rhino_path:
        print("\nERROR: Could not find Rhino installation!")
        print("Please edit VizorAgents.GH_MCP.csproj manually with your Rhino path.")
        
        # Provide manual instructions
        print("\nManual fix instructions:")
        print("1. Find your Rhino installation folder")
        print("2. Locate these files:")
        print("   - Grasshopper.dll (usually in Plug-ins\\Grasshopper\\)")
        print("   - GH_IO.dll (usually in Plug-ins\\Grasshopper\\)")
        print("   - RhinoCommon.dll (usually in System\\)")
        print("3. Update the HintPath values in VizorAgents.GH_MCP.csproj")
        return 1
    
    # Check for required DLLs
    all_found, dlls = check_required_dlls(rhino_path)
    
    if not all_found:
        print("\nERROR: Some required DLLs are missing!")
        print("Please check your Rhino installation.")
        return 1
    
    # Generate the XML
    xml = generate_csproj_references(dlls)
    
    print("\nAll DLLs found! Here are the correct reference paths for your .csproj file:")
    print("\nCopy and paste these into VizorAgents.GH_MCP.csproj:")
    print("-" * 60)
    print(xml)
    print("-" * 60)
    
    # Option to save to file
    response = input("\nWould you like to save this to 'references.xml' for easy copying? (y/n): ")
    if response.lower() == 'y':
        with open('references.xml', 'w') as f:
            f.write(xml)
        print("✓ Saved to references.xml")
    
    print("\nAfter updating the references, rebuild the project in Visual Studio.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())