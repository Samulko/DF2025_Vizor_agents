#!/bin/bash

echo "Grasshopper Reference Fix Helper"
echo "================================"
echo ""

# Common Rhino installation paths
RHINO_PATHS=(
    "/mnt/c/Program Files/Rhino 8"
    "/mnt/c/Program Files/Rhino 7"
    "/mnt/c/Program Files/Rhinoceros 5 (64-bit)"
    "C:/Program Files/Rhino 8"
    "C:/Program Files/Rhino 7"
    "C:/Program Files/Rhinoceros 5 (64-bit)"
)

# Find Rhino installation
RHINO_PATH=""
for path in "${RHINO_PATHS[@]}"; do
    if [ -d "$path" ]; then
        RHINO_PATH="$path"
        echo "✓ Found Rhino at: $RHINO_PATH"
        break
    fi
done

if [ -z "$RHINO_PATH" ]; then
    echo "ERROR: Could not find Rhino installation!"
    echo "Please edit VizorAgents.GH_MCP.csproj manually with your Rhino path."
    echo ""
    echo "Manual fix instructions:"
    echo "1. Find your Rhino installation folder"
    echo "2. Locate these files:"
    echo "   - Grasshopper.dll (usually in Plug-ins/Grasshopper/)"
    echo "   - GH_IO.dll (usually in Plug-ins/Grasshopper/)"
    echo "   - RhinoCommon.dll (usually in System/)"
    echo "3. Update the HintPath values in VizorAgents.GH_MCP.csproj"
    exit 1
fi

# Check for required DLLs
GRASSHOPPER_DLL="$RHINO_PATH/Plug-ins/Grasshopper/Grasshopper.dll"
GH_IO_DLL="$RHINO_PATH/Plug-ins/Grasshopper/GH_IO.dll"
RHINO_COMMON_DLL="$RHINO_PATH/System/RhinoCommon.dll"

echo ""
echo "Checking for required DLLs..."

ALL_FOUND=true
if [ -f "$GRASSHOPPER_DLL" ]; then
    echo "✓ Found Grasshopper.dll"
else
    echo "✗ Missing Grasshopper.dll"
    ALL_FOUND=false
fi

if [ -f "$GH_IO_DLL" ]; then
    echo "✓ Found GH_IO.dll"
else
    echo "✗ Missing GH_IO.dll"
    ALL_FOUND=false
fi

if [ -f "$RHINO_COMMON_DLL" ]; then
    echo "✓ Found RhinoCommon.dll"
else
    echo "✗ Missing RhinoCommon.dll"
    ALL_FOUND=false
fi

if [ "$ALL_FOUND" != true ]; then
    echo ""
    echo "ERROR: Some required DLLs are missing!"
    echo "Please check your Rhino installation."
    exit 1
fi

echo ""
echo "All DLLs found! Here are the correct reference paths for your .csproj file:"
echo ""
echo "Copy and paste these into VizorAgents.GH_MCP.csproj:"
echo "------------------------------------------------------------"
cat << EOF

  <!-- Grasshopper and Rhino References -->
  <ItemGroup>
    <Reference Include="Grasshopper">
      <HintPath>$GRASSHOPPER_DLL</HintPath>
      <Private>false</Private>
    </Reference>
    <Reference Include="GH_IO">
      <HintPath>$GH_IO_DLL</HintPath>
      <Private>false</Private>
    </Reference>
    <Reference Include="RhinoCommon">
      <HintPath>$RHINO_COMMON_DLL</HintPath>
      <Private>false</Private>
    </Reference>
  </ItemGroup>

EOF
echo "------------------------------------------------------------"

echo ""
echo "After updating the references, rebuild the project in Visual Studio."
echo ""