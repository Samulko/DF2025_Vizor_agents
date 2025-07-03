# Fix Grasshopper References Script
# This script helps fix the reference paths based on your Rhino installation

Write-Host "Grasshopper Reference Fix Helper" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Common Rhino installation paths
$rhinoPaths = @(
    "C:\Program Files\Rhino 8",
    "C:\Program Files\Rhino 7",
    "C:\Program Files\Rhinoceros 5 (64-bit)",
    "C:\Program Files\Rhinoceros 5"
)

# Find Rhino installation
$rhinoPath = ""
foreach ($path in $rhinoPaths) {
    if (Test-Path $path) {
        $rhinoPath = $path
        Write-Host "Found Rhino at: $rhinoPath" -ForegroundColor Cyan
        break
    }
}

if ($rhinoPath -eq "") {
    Write-Host "ERROR: Could not find Rhino installation!" -ForegroundColor Red
    Write-Host "Please edit VizorAgents.GH_MCP.csproj manually with your Rhino path." -ForegroundColor Yellow
    exit 1
}

# Check for required DLLs
$grasshopperDll = Join-Path $rhinoPath "Plug-ins\Grasshopper\Grasshopper.dll"
$ghIoDll = Join-Path $rhinoPath "Plug-ins\Grasshopper\GH_IO.dll"
$rhinoCommonDll = Join-Path $rhinoPath "System\RhinoCommon.dll"

Write-Host ""
Write-Host "Checking for required DLLs..." -ForegroundColor Yellow

$allFound = $true
if (Test-Path $grasshopperDll) {
    Write-Host "✓ Found Grasshopper.dll" -ForegroundColor Green
} else {
    Write-Host "✗ Missing Grasshopper.dll" -ForegroundColor Red
    $allFound = $false
}

if (Test-Path $ghIoDll) {
    Write-Host "✓ Found GH_IO.dll" -ForegroundColor Green
} else {
    Write-Host "✗ Missing GH_IO.dll" -ForegroundColor Red
    $allFound = $false
}

if (Test-Path $rhinoCommonDll) {
    Write-Host "✓ Found RhinoCommon.dll" -ForegroundColor Green
} else {
    Write-Host "✗ Missing RhinoCommon.dll" -ForegroundColor Red
    $allFound = $false
}

if (-not $allFound) {
    Write-Host ""
    Write-Host "ERROR: Some required DLLs are missing!" -ForegroundColor Red
    Write-Host "Please check your Rhino installation." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "All DLLs found! Here are the correct reference paths for your .csproj file:" -ForegroundColor Green
Write-Host ""
Write-Host "Copy and paste these into VizorAgents.GH_MCP.csproj:" -ForegroundColor Yellow
Write-Host ""
Write-Host @"
  <ItemGroup>
    <Reference Include="Grasshopper">
      <HintPath>$grasshopperDll</HintPath>
      <Private>false</Private>
    </Reference>
    <Reference Include="GH_IO">
      <HintPath>$ghIoDll</HintPath>
      <Private>false</Private>
    </Reference>
    <Reference Include="RhinoCommon">
      <HintPath>$rhinoCommonDll</HintPath>
      <Private>false</Private>
    </Reference>
  </ItemGroup>
"@ -ForegroundColor Cyan

Write-Host ""
Write-Host "After updating the references, rebuild the project." -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")