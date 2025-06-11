using System;
using System.Collections.Generic;
using System.Reflection;
using GrasshopperMCP.Models;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Parameters;
using Grasshopper.Kernel.Special;
using Rhino;
using Rhino.Geometry;
using Grasshopper;
using System.Linq;
using Grasshopper.Kernel.Components;
using System.Threading;
using GH_MCP.Utils;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Types;

namespace GrasshopperMCP.Commands
{
    /// <summary>
    /// 處理組件相關命令的處理器
    /// </summary>
    public static class ComponentCommandHandler
    {
        /// <summary>
        /// 添加組件
        /// </summary>
        /// <param name="command">包含組件類型和位置的命令</param>
        /// <returns>添加的組件信息</returns>
        public static object AddComponent(Command command)
        {
            string type = command.GetParameter<string>("type");
            double x = command.GetParameter<double>("x");
            double y = command.GetParameter<double>("y");
            
            if (string.IsNullOrEmpty(type))
            {
                throw new ArgumentException("Component type is required");
            }
            
            // 使用模糊匹配獲取標準化的元件名稱
            string normalizedType = FuzzyMatcher.GetClosestComponentName(type);
            
            // 記錄請求信息
            RhinoApp.WriteLine($"AddComponent request: type={type}, normalized={normalizedType}, x={x}, y={y}");
            
            // Log all parameters for debugging
            RhinoApp.WriteLine($"All parameters received:");
            foreach (var param in command.Parameters)
            {
                RhinoApp.WriteLine($"  {param.Key}: {param.Value}");
            }
            
            object result = null;
            Exception exception = null;
            
            // 在 UI 線程上執行
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    // 獲取 Grasshopper 文檔
                    var doc = Grasshopper.Instances.ActiveCanvas?.Document;
                    if (doc == null)
                    {
                        throw new InvalidOperationException("No active Grasshopper document");
                    }
                    
                    // 創建組件
                    IGH_DocumentObject component = null;
                    
                    // 記錄可用的組件類型（僅在第一次調用時記錄）
                    bool loggedComponentTypes = false;
                    if (!loggedComponentTypes)
                    {
                        var availableTypes = Grasshopper.Instances.ComponentServer.ObjectProxies
                            .Select(p => p.Desc.Name)
                            .OrderBy(n => n)
                            .ToList();
                        
                        RhinoApp.WriteLine($"Available component types: {string.Join(", ", availableTypes.Take(50))}...");
                        loggedComponentTypes = true;
                    }
                    
                    // 根據類型創建不同的組件
                    switch (normalizedType.ToLowerInvariant())
                    {
                        // 平面元件
                        case "xy plane":
                            component = CreateComponentByName("XY Plane");
                            break;
                        case "xz plane":
                            component = CreateComponentByName("XZ Plane");
                            break;
                        case "yz plane":
                            component = CreateComponentByName("YZ Plane");
                            break;
                        case "plane 3pt":
                            component = CreateComponentByName("Plane 3Pt");
                            break;
                            
                        // 基本幾何元件
                        case "box":
                            component = CreateComponentByName("Box");
                            break;
                        case "sphere":
                            component = CreateComponentByName("Sphere");
                            break;
                        case "cylinder":
                            component = CreateComponentByName("Cylinder");
                            break;
                        case "cone":
                            component = CreateComponentByName("Cone");
                            break;
                        case "circle":
                            component = CreateComponentByName("Circle");
                            break;
                        case "rectangle":
                            component = CreateComponentByName("Rectangle");
                            break;
                        case "line":
                            component = CreateComponentByName("Line");
                            break;
                            
                        // 參數元件
                        case "point":
                        case "pt":
                        case "pointparam":
                        case "param_point":
                            component = new Param_Point();
                            break;
                        case "curve":
                        case "crv":
                        case "curveparam":
                        case "param_curve":
                            component = new Param_Curve();
                            break;
                        case "circleparam":
                        case "param_circle":
                            component = new Param_Circle();
                            break;
                        case "lineparam":
                        case "param_line":
                            component = new Param_Line();
                            break;
                        case "panel":
                        case "gh_panel":
                            component = new GH_Panel();
                            break;
                        case "slider":
                        case "numberslider":
                        case "gh_numberslider":
                            var slider = new GH_NumberSlider();
                            
                            try
                            {
                                // Check if initCode was provided directly
                                string initCode = command.GetParameter<string>("initCode");
                                if (!string.IsNullOrEmpty(initCode))
                                {
                                    slider.SetInitCode(initCode);
                                    RhinoApp.WriteLine($"GH_MCP: Slider created with initCode: {initCode}");
                                }
                                else
                                {
                                    // Use default
                                    slider.SetInitCode("0.0 < 0.5 < 1.0");
                                }
                            }
                            catch (Exception ex)
                            {
                                // If anything goes wrong, use default
                                RhinoApp.WriteLine($"GH_MCP: Error setting slider initCode: {ex.Message}. Using default.");
                                slider.SetInitCode("0.0 < 0.5 < 1.0");
                            }
                            
                            component = slider;
                            break;
                        case "number":
                        case "num":
                        case "integer":
                        case "int":
                        case "param_number":
                        case "param_integer":
                            component = new Param_Number();
                            break;
                        case "construct point":
                        case "constructpoint":
                        case "pt xyz":
                        case "xyz":
                            // 嘗試查找構造點組件
                            var pointProxy = Grasshopper.Instances.ComponentServer.ObjectProxies
                                .FirstOrDefault(p => p.Desc.Name.Equals("Construct Point", StringComparison.OrdinalIgnoreCase));
                            if (pointProxy != null)
                            {
                                component = pointProxy.CreateInstance();
                            }
                            else
                            {
                                throw new ArgumentException("Construct Point component not found");
                            }
                            break;
                        case "py3":  // The proper Python 3 component in Rhino 8
                        case "python 3 script":
                        case "python3":
                        case "python script":
                        case "python":
                            // Create Python 3 Script component (Py3)
                            string scriptContent = command.Parameters.ContainsKey("script") 
                                ? command.GetParameter<string>("script") 
                                : "";
                            
                            RhinoApp.WriteLine($"=== Python Script Component Creation ===");
                            RhinoApp.WriteLine($"Looking for Py3 component specifically...");
                            
                            // The documentation says the Script component is in Maths tab, Script panel
                            // and it can handle multiple languages including Python 3
                            IGH_ObjectProxy pythonProxy = null;
                            
                            // Strategy 1: Look in the Maths/Script category specifically
                            RhinoApp.WriteLine("=== Searching in Maths/Script category ===");
                            var mathsScriptComponents = Grasshopper.Instances.ComponentServer.ObjectProxies
                                .Where(p => p.Desc.Category == "Maths" && p.Desc.SubCategory == "Script")
                                .ToList();
                            
                            foreach (var comp in mathsScriptComponents)
                            {
                                RhinoApp.WriteLine($"  Found: '{comp.Desc.Name}' (GUID: {comp.Guid})");
                                
                                // Check if this is the unified Script component or a Python 3 specific one
                                if (comp.Desc.Name == "Script" || 
                                    comp.Desc.Name.Contains("Python") && comp.Desc.Name.Contains("3"))
                                {
                                    pythonProxy = comp;
                                    RhinoApp.WriteLine($"  *** Selected: {comp.Desc.Name} ***");
                                    break;
                                }
                            }
                            
                            // Strategy 2: Look for components by their display name/nickname
                            if (pythonProxy == null)
                            {
                                RhinoApp.WriteLine("\n=== Searching all components for Py3 nickname ===");
                                
                                // List ALL components for debugging
                                var allComponents = Grasshopper.Instances.ComponentServer.ObjectProxies.ToList();
                                RhinoApp.WriteLine($"Total components available: {allComponents.Count}");
                                
                                // Search for components with Python in name
                                var pythonComponents = allComponents
                                    .Where(p => p.Desc.Name.ToLower().Contains("py") || 
                                               p.Desc.Name.ToLower().Contains("script"))
                                    .ToList();
                                
                                foreach (var proxy in pythonComponents)
                                {
                                    try
                                    {
                                        var instance = proxy.CreateInstance();
                                        if (instance != null)
                                        {
                                            RhinoApp.WriteLine($"  Component: {proxy.Desc.Name}");
                                            RhinoApp.WriteLine($"    Category: {proxy.Desc.Category}/{proxy.Desc.SubCategory}");
                                            RhinoApp.WriteLine($"    Type: {instance.GetType().FullName}");
                                            RhinoApp.WriteLine($"    NickName: {instance.NickName}");
                                            RhinoApp.WriteLine($"    GUID: {proxy.Guid}");
                                            
                                            // Check if this creates the "Py3" component we see in the screenshot
                                            if (instance.NickName == "Py3" || 
                                                instance.NickName == "Python 3" ||
                                                (proxy.Desc.Name.Contains("Python") && 
                                                 !proxy.Desc.Name.Contains("2") && 
                                                 (proxy.Desc.Name.Contains("3") || !proxy.Desc.Name.Contains("Legacy"))))
                                            {
                                                pythonProxy = proxy;
                                                RhinoApp.WriteLine("    *** THIS IS THE PY3 COMPONENT! ***");
                                                break;
                                            }
                                        }
                                    }
                                    catch (Exception ex)
                                    {
                                        RhinoApp.WriteLine($"  Error checking {proxy.Desc.Name}: {ex.Message}");
                                    }
                                }
                            }
                            
                            // Strategy 3: Try known GUIDs for Python components
                            if (pythonProxy == null)
                            {
                                RhinoApp.WriteLine("\n=== Trying known component GUIDs ===");
                                
                                // These are potential GUIDs for Python components - may vary by Rhino version
                                Guid[] knownGuids = new Guid[]
                                {
                                    new Guid("E69B937B-03AB-4CAA-9D11-75D46C5B89E8"), // Possible Py3 GUID
                                    new Guid("79EF4718-2B5A-4DCA-89FC-E94E807692D2"), // Script component
                                    new Guid("A8F1E0AA-603F-4B4B-A5E5-238162B9BC73"), // Python 3
                                    new Guid("410755B1-224A-4C1E-A407-BF32FB45EA7E"), // GhPython
                                };
                                
                                foreach (var guid in knownGuids)
                                {
                                    try
                                    {
                                        var testComponent = Grasshopper.Instances.ComponentServer.EmitObject(guid);
                                        if (testComponent != null)
                                        {
                                            RhinoApp.WriteLine($"  Found component with GUID {guid}:");
                                            RhinoApp.WriteLine($"    Type: {testComponent.GetType().FullName}");
                                            RhinoApp.WriteLine($"    NickName: {testComponent.NickName}");
                                            
                                            if (testComponent.NickName == "Py3")
                                            {
                                                component = testComponent;
                                                RhinoApp.WriteLine("    *** THIS IS THE PY3 COMPONENT! ***");
                                                break;
                                            }
                                        }
                                    }
                                    catch
                                    {
                                        // GUID not found, continue
                                    }
                                }
                            }
                            
                            // Create component from proxy if we found one
                            if (component == null && pythonProxy != null)
                            {
                                component = pythonProxy.CreateInstance();
                                RhinoApp.WriteLine($"\nCreated component: {pythonProxy.Desc.Name}");
                            }
                            
                            // Last resort - use any Python component
                            if (component == null)
                            {
                                RhinoApp.WriteLine("\n=== Last resort: finding any Python component ===");
                                pythonProxy = Grasshopper.Instances.ComponentServer.ObjectProxies
                                    .FirstOrDefault(p => p.Desc.Name.Contains("Python") && !p.Desc.Name.Contains("Legacy"));
                                
                                if (pythonProxy != null)
                                {
                                    component = pythonProxy.CreateInstance();
                                    RhinoApp.WriteLine($"Using fallback: {pythonProxy.Desc.Name}");
                                }
                                else
                                {
                                    throw new ArgumentException("No Python component found in Grasshopper");
                                }
                            }
                            
                            // Configure the component
                            if (component != null)
                            {
                                var scriptName = command.Parameters.ContainsKey("name") 
                                    ? command.GetParameter<string>("name") 
                                    : "Python Script";
                                
                                // Set component nickname
                                try
                                {
                                    var nickNameProp = component.GetType().GetProperty("NickName");
                                    if (nickNameProp != null && nickNameProp.CanWrite)
                                    {
                                        nickNameProp.SetValue(component, scriptName);
                                    }
                                }
                                catch { }
                                
                                // Set the script content
                                if (!string.IsNullOrEmpty(scriptContent))
                                {
                                    var componentType = component.GetType();
                                    RhinoApp.WriteLine($"\nSetting script on: {componentType.FullName}");
                                    bool scriptSet = false;
                                    
                                    // Ensure script has Python 3 language specifier
                                    string fullScript = scriptContent;
                                    if (!scriptContent.StartsWith("#!"))
                                    {
                                        fullScript = "#! python 3\n\n" + scriptContent;
                                    }
                                    
                                    // Try various methods to set the script
                                    // Method 1: SetSource
                                    var setSourceMethod = componentType.GetMethod("SetSource", new Type[] { typeof(string) });
                                    if (setSourceMethod != null)
                                    {
                                        try
                                        {
                                            setSourceMethod.Invoke(component, new object[] { fullScript });
                                            RhinoApp.WriteLine("  Script set using SetSource");
                                            scriptSet = true;
                                        }
                                        catch (Exception ex)
                                        {
                                            RhinoApp.WriteLine($"  SetSource failed: {ex.Message}");
                                        }
                                    }
                                    
                                    // Method 2: Properties
                                    if (!scriptSet)
                                    {
                                        string[] propNames = { "Code", "ScriptSource", "Text", "ScriptText", "Source" };
                                        foreach (var propName in propNames)
                                        {
                                            var prop = componentType.GetProperty(propName);
                                            if (prop != null && prop.CanWrite)
                                            {
                                                try
                                                {
                                                    prop.SetValue(component, fullScript);
                                                    RhinoApp.WriteLine($"  Script set using {propName} property");
                                                    scriptSet = true;
                                                    break;
                                                }
                                                catch { }
                                            }
                                        }
                                    }
                                    
                                    // Try to sync parameters
                                    var syncMethod = componentType.GetMethod("SetParametersFromScript") ??
                                                    componentType.GetMethod("SyncParametersFromScript");
                                    if (syncMethod != null)
                                    {
                                        try
                                        {
                                            syncMethod.Invoke(component, null);
                                            RhinoApp.WriteLine("  Parameters synced");
                                        }
                                        catch { }
                                    }
                                    
                                    // Expire solution
                                    if (component is IGH_ActiveObject activeObj)
                                    {
                                        activeObj.ExpireSolution(true);
                                    }
                                    
                                    if (!scriptSet)
                                    {
                                        RhinoApp.WriteLine("  WARNING: Could not set script content");
                                    }
                                }
                            }
                            break;
                        default:
                            // 嘗試通過 Guid 查找組件
                            Guid componentGuid;
                            if (Guid.TryParse(type, out componentGuid))
                            {
                                component = Grasshopper.Instances.ComponentServer.EmitObject(componentGuid);
                                RhinoApp.WriteLine($"Attempting to create component by GUID: {componentGuid}");
                            }
                            
                            if (component == null)
                            {
                                // 嘗試通過名稱查找組件（不區分大小寫）
                                RhinoApp.WriteLine($"Attempting to find component by name: {type}");
                                var obj = Grasshopper.Instances.ComponentServer.ObjectProxies
                                    .FirstOrDefault(p => p.Desc.Name.Equals(type, StringComparison.OrdinalIgnoreCase));
                                    
                                if (obj != null)
                                {
                                    RhinoApp.WriteLine($"Found component: {obj.Desc.Name}");
                                    component = obj.CreateInstance();
                                }
                                else
                                {
                                    // 嘗試通過部分名稱匹配
                                    RhinoApp.WriteLine($"Attempting to find component by partial name match: {type}");
                                    obj = Grasshopper.Instances.ComponentServer.ObjectProxies
                                        .FirstOrDefault(p => p.Desc.Name.IndexOf(type, StringComparison.OrdinalIgnoreCase) >= 0);
                                        
                                    if (obj != null)
                                    {
                                        RhinoApp.WriteLine($"Found component by partial match: {obj.Desc.Name}");
                                        component = obj.CreateInstance();
                                    }
                                }
                            }
                            
                            if (component == null)
                            {
                                // 記錄一些可能的組件類型
                                var possibleMatches = Grasshopper.Instances.ComponentServer.ObjectProxies
                                    .Where(p => p.Desc.Name.IndexOf(type, StringComparison.OrdinalIgnoreCase) >= 0)
                                    .Select(p => p.Desc.Name)
                                    .Take(10)
                                    .ToList();
                                
                                var errorMessage = $"Unknown component type: {type}";
                                if (possibleMatches.Any())
                                {
                                    errorMessage += $". Possible matches: {string.Join(", ", possibleMatches)}";
                                }
                                
                                throw new ArgumentException(errorMessage);
                            }
                            break;
                    }
                    
                    // 設置組件位置
                    if (component != null)
                    {
                        // 確保組件有有效的屬性對象
                        if (component.Attributes == null)
                        {
                            RhinoApp.WriteLine("Component attributes are null, creating new attributes");
                            component.CreateAttributes();
                        }
                        
                        // 設置位置
                        component.Attributes.Pivot = new System.Drawing.PointF((float)x, (float)y);
                        
                        // 添加到文檔
                        doc.AddObject(component, false);
                        
                        // 刷新畫布
                        doc.NewSolution(false);
                        
                        // 返回組件信息
                        result = new
                        {
                            id = component.InstanceGuid.ToString(),
                            type = component.GetType().Name,
                            name = component.NickName,
                            x = component.Attributes.Pivot.X,
                            y = component.Attributes.Pivot.Y
                        };
                    }
                    else
                    {
                        throw new InvalidOperationException("Failed to create component");
                    }
                }
                catch (Exception ex)
                {
                    exception = ex;
                    RhinoApp.WriteLine($"Error in AddComponent: {ex.Message}");
                }
            }));
            
            // 等待 UI 線程操作完成
            while (result == null && exception == null)
            {
                Thread.Sleep(10);
            }
            
            // 如果有異常，拋出
            if (exception != null)
            {
                throw exception;
            }
            
            return result;
        }
        
        /// <summary>
        /// 連接組件
        /// </summary>
        /// <param name="command">包含源和目標組件信息的命令</param>
        /// <returns>連接信息</returns>
        public static object ConnectComponents(Command command)
        {
            var fromData = command.GetParameter<Dictionary<string, object>>("from");
            var toData = command.GetParameter<Dictionary<string, object>>("to");
            
            if (fromData == null || toData == null)
            {
                throw new ArgumentException("Source and target component information are required");
            }
            
            object result = null;
            Exception exception = null;
            
            // 在 UI 線程上執行
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    // 獲取 Grasshopper 文檔
                    var doc = Grasshopper.Instances.ActiveCanvas?.Document;
                    if (doc == null)
                    {
                        throw new InvalidOperationException("No active Grasshopper document");
                    }
                    
                    // 解析源組件信息
                    string fromIdStr = fromData["id"].ToString();
                    string fromParamName = fromData["parameterName"].ToString();
                    
                    // 解析目標組件信息
                    string toIdStr = toData["id"].ToString();
                    string toParamName = toData["parameterName"].ToString();
                    
                    // 將字符串 ID 轉換為 Guid
                    Guid fromId, toId;
                    if (!Guid.TryParse(fromIdStr, out fromId) || !Guid.TryParse(toIdStr, out toId))
                    {
                        throw new ArgumentException("Invalid component ID format");
                    }
                    
                    // 查找源和目標組件
                    IGH_Component fromComponent = doc.FindComponent(fromId) as IGH_Component;
                    IGH_Component toComponent = doc.FindComponent(toId) as IGH_Component;
                    
                    if (fromComponent == null || toComponent == null)
                    {
                        throw new ArgumentException("Source or target component not found");
                    }
                    
                    // 查找源輸出參數
                    IGH_Param fromParam = null;
                    foreach (var param in fromComponent.Params.Output)
                    {
                        if (param.Name.Equals(fromParamName, StringComparison.OrdinalIgnoreCase))
                        {
                            fromParam = param;
                            break;
                        }
                    }
                    
                    // 查找目標輸入參數
                    IGH_Param toParam = null;
                    foreach (var param in toComponent.Params.Input)
                    {
                        if (param.Name.Equals(toParamName, StringComparison.OrdinalIgnoreCase))
                        {
                            toParam = param;
                            break;
                        }
                    }
                    
                    if (fromParam == null || toParam == null)
                    {
                        throw new ArgumentException("Source or target parameter not found");
                    }
                    
                    // 連接參數
                    toParam.AddSource(fromParam);
                    
                    // 刷新畫布
                    doc.NewSolution(false);
                    
                    // 返回連接信息
                    result = new
                    {
                        from = new
                        {
                            id = fromComponent.InstanceGuid.ToString(),
                            name = fromComponent.NickName,
                            parameter = fromParam.Name
                        },
                        to = new
                        {
                            id = toComponent.InstanceGuid.ToString(),
                            name = toComponent.NickName,
                            parameter = toParam.Name
                        }
                    };
                }
                catch (Exception ex)
                {
                    exception = ex;
                    RhinoApp.WriteLine($"Error in ConnectComponents: {ex.Message}");
                }
            }));
            
            // 等待 UI 線程操作完成
            while (result == null && exception == null)
            {
                Thread.Sleep(10);
            }
            
            // 如果有異常，拋出
            if (exception != null)
            {
                throw exception;
            }
            
            return result;
        }
        
        /// <summary>
        /// 設置組件值
        /// </summary>
        /// <param name="command">包含組件 ID 和值的命令</param>
        /// <returns>操作結果</returns>
        public static object SetComponentValue(Command command)
        {
            string idStr = command.GetParameter<string>("id");
            string value = command.GetParameter<string>("value");
            
            if (string.IsNullOrEmpty(idStr))
            {
                throw new ArgumentException("Component ID is required");
            }
            
            object result = null;
            Exception exception = null;
            
            // 在 UI 線程上執行
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    // 獲取 Grasshopper 文檔
                    var doc = Grasshopper.Instances.ActiveCanvas?.Document;
                    if (doc == null)
                    {
                        throw new InvalidOperationException("No active Grasshopper document");
                    }
                    
                    // 將字符串 ID 轉換為 Guid
                    Guid id;
                    if (!Guid.TryParse(idStr, out id))
                    {
                        throw new ArgumentException("Invalid component ID format");
                    }
                    
                    // 查找組件
                    IGH_DocumentObject component = doc.FindObject(id, true);
                    if (component == null)
                    {
                        throw new ArgumentException($"Component with ID {idStr} not found");
                    }
                    
                    // 根據組件類型設置值
                    if (component is GH_Panel panel)
                    {
                        panel.UserText = value;
                    }
                    else if (component is GH_NumberSlider slider)
                    {
                        double doubleValue;
                        if (double.TryParse(value, out doubleValue))
                        {
                            slider.SetSliderValue((decimal)doubleValue);
                        }
                        else
                        {
                            throw new ArgumentException("Invalid slider value format");
                        }
                    }
                    else if (component is IGH_Component ghComponent)
                    {
                        // 嘗試設置第一個輸入參數的值
                        if (ghComponent.Params.Input.Count > 0)
                        {
                            var param = ghComponent.Params.Input[0];
                            if (param is Param_String stringParam)
                            {
                                stringParam.PersistentData.Clear();
                                stringParam.PersistentData.Append(new Grasshopper.Kernel.Types.GH_String(value));
                            }
                            else if (param is Param_Number numberParam)
                            {
                                double doubleValue;
                                if (double.TryParse(value, out doubleValue))
                                {
                                    numberParam.PersistentData.Clear();
                                    numberParam.PersistentData.Append(new Grasshopper.Kernel.Types.GH_Number(doubleValue));
                                }
                                else
                                {
                                    throw new ArgumentException("Invalid number value format");
                                }
                            }
                            else
                            {
                                throw new ArgumentException($"Cannot set value for parameter type {param.GetType().Name}");
                            }
                        }
                        else
                        {
                            throw new ArgumentException("Component has no input parameters");
                        }
                    }
                    else
                    {
                        throw new ArgumentException($"Cannot set value for component type {component.GetType().Name}");
                    }
                    
                    // 刷新畫布
                    doc.NewSolution(false);
                    
                    // 返回操作結果
                    result = new
                    {
                        id = component.InstanceGuid.ToString(),
                        type = component.GetType().Name,
                        value = value
                    };
                }
                catch (Exception ex)
                {
                    exception = ex;
                    RhinoApp.WriteLine($"Error in SetComponentValue: {ex.Message}");
                }
            }));
            
            // 等待 UI 線程操作完成
            while (result == null && exception == null)
            {
                Thread.Sleep(10);
            }
            
            // 如果有異常，拋出
            if (exception != null)
            {
                throw exception;
            }
            
            return result;
        }
        
        /// <summary>
        /// 獲取組件信息
        /// </summary>
        /// <param name="command">包含組件 ID 的命令</param>
        /// <returns>組件信息</returns>
        public static object GetComponentInfo(Command command)
        {
            string idStr = command.GetParameter<string>("id");
            
            if (string.IsNullOrEmpty(idStr))
            {
                throw new ArgumentException("Component ID is required");
            }
            
            object result = null;
            Exception exception = null;
            
            // 在 UI 線程上執行
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    // 獲取 Grasshopper 文檔
                    var doc = Grasshopper.Instances.ActiveCanvas?.Document;
                    if (doc == null)
                    {
                        throw new InvalidOperationException("No active Grasshopper document");
                    }
                    
                    // 將字符串 ID 轉換為 Guid
                    Guid id;
                    if (!Guid.TryParse(idStr, out id))
                    {
                        throw new ArgumentException("Invalid component ID format");
                    }
                    
                    // 查找組件
                    IGH_DocumentObject component = doc.FindObject(id, true);
                    if (component == null)
                    {
                        throw new ArgumentException($"Component with ID {idStr} not found");
                    }
                    
                    // 收集組件信息
                    var componentInfo = new Dictionary<string, object>
                    {
                        { "id", component.InstanceGuid.ToString() },
                        { "type", component.GetType().Name },
                        { "name", component.NickName },
                        { "description", component.Description }
                    };
                    
                    // 如果是 IGH_Component，收集輸入和輸出參數信息
                    if (component is IGH_Component ghComponent)
                    {
                        var inputs = new List<Dictionary<string, object>>();
                        foreach (var param in ghComponent.Params.Input)
                        {
                            inputs.Add(new Dictionary<string, object>
                            {
                                { "name", param.Name },
                                { "nickname", param.NickName },
                                { "description", param.Description },
                                { "type", param.GetType().Name },
                                { "dataType", param.TypeName }
                            });
                        }
                        componentInfo["inputs"] = inputs;
                        
                        var outputs = new List<Dictionary<string, object>>();
                        foreach (var param in ghComponent.Params.Output)
                        {
                            outputs.Add(new Dictionary<string, object>
                            {
                                { "name", param.Name },
                                { "nickname", param.NickName },
                                { "description", param.Description },
                                { "type", param.GetType().Name },
                                { "dataType", param.TypeName }
                            });
                        }
                        componentInfo["outputs"] = outputs;
                    }
                    
                    // 如果是 GH_Panel，獲取其文本值
                    if (component is GH_Panel panel)
                    {
                        componentInfo["value"] = panel.UserText;
                    }
                    
                    // 如果是 GH_NumberSlider，獲取其值和範圍
                    if (component is GH_NumberSlider slider)
                    {
                        componentInfo["value"] = (double)slider.CurrentValue;
                        componentInfo["minimum"] = (double)slider.Slider.Minimum;
                        componentInfo["maximum"] = (double)slider.Slider.Maximum;
                    }
                    
                    result = componentInfo;
                }
                catch (Exception ex)
                {
                    exception = ex;
                    RhinoApp.WriteLine($"Error in GetComponentInfo: {ex.Message}");
                }
            }));
            
            // 等待 UI 線程操作完成
            while (result == null && exception == null)
            {
                Thread.Sleep(10);
            }
            
            // 如果有異常，拋出
            if (exception != null)
            {
                throw exception;
            }
            
            return result;
        }
        
        /// <summary>
        /// 獲取 Python 腳本組件的內容
        /// </summary>
        /// <param name="command">包含組件 ID 的命令</param>
        /// <returns>腳本內容</returns>
        public static object GetPythonScriptContent(Command command)
        {
            string idStr = command.GetParameter<string>("id");
            
            if (string.IsNullOrEmpty(idStr))
            {
                throw new ArgumentException("Component ID is required");
            }
            
            object result = null;
            Exception exception = null;
            
            // 在 UI 線程上執行
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    // 獲取 Grasshopper 文檔
                    var doc = Grasshopper.Instances.ActiveCanvas?.Document;
                    if (doc == null)
                    {
                        throw new InvalidOperationException("No active Grasshopper document");
                    }
                    
                    // 將字符串 ID 轉換為 Guid
                    Guid id;
                    if (!Guid.TryParse(idStr, out id))
                    {
                        throw new ArgumentException("Invalid component ID format");
                    }
                    
                    // 查找組件
                    IGH_DocumentObject component = doc.FindObject(id, true);
                    if (component == null)
                    {
                        throw new ArgumentException($"Component with ID {idStr} not found");
                    }
                    
                    // Get component type information
                    var componentType = component.GetType();
                    RhinoApp.WriteLine($"GetPythonScriptContent: Found component of type {componentType.FullName}");
                    
                    // Check if this is a Python script component
                    if (component.NickName == "Py3" || componentType.Name.Contains("Script") || componentType.Name.Contains("Python"))
                    {
                        string scriptContent = null;
                        
                        // Log all available methods and properties for debugging
                        RhinoApp.WriteLine("=== Available Methods ===");
                        var methods = componentType.GetMethods(BindingFlags.Public | BindingFlags.Instance);
                        foreach (var method in methods.Where(m => m.Name.ToLower().Contains("source") || m.Name.ToLower().Contains("script") || m.Name.ToLower().Contains("code")))
                        {
                            RhinoApp.WriteLine($"  Method: {method.Name} - Returns: {method.ReturnType.Name} - Params: {method.GetParameters().Length}");
                        }
                        
                        RhinoApp.WriteLine("=== Available Properties ===");
                        var properties = componentType.GetProperties(BindingFlags.Public | BindingFlags.Instance);
                        foreach (var prop in properties.Where(p => p.Name.ToLower().Contains("source") || p.Name.ToLower().Contains("script") || p.Name.ToLower().Contains("code") || p.Name.ToLower().Contains("text")))
                        {
                            RhinoApp.WriteLine($"  Property: {prop.Name} - Type: {prop.PropertyType.Name} - CanRead: {prop.CanRead} - CanWrite: {prop.CanWrite}");
                        }
                        
                        // Try various methods to get the script content
                        // Method 1: TryGetSource (the correct method for RhinoCodePluginGH.Components.Python3Component)
                        var tryGetSourceMethod = componentType.GetMethod("TryGetSource", new Type[] { typeof(string).MakeByRefType() });
                        if (tryGetSourceMethod != null)
                        {
                            try
                            {
                                object[] parameters = new object[] { null };
                                bool success = (bool)tryGetSourceMethod.Invoke(component, parameters);
                                if (success && parameters[0] != null)
                                {
                                    scriptContent = parameters[0] as string;
                                    if (!string.IsNullOrEmpty(scriptContent))
                                    {
                                        RhinoApp.WriteLine("  Script retrieved using TryGetSource(out string)");
                                    }
                                }
                                else
                                {
                                    RhinoApp.WriteLine($"  TryGetSource returned success={success}, content length={parameters[0]?.ToString()?.Length ?? 0}");
                                }
                            }
                            catch (Exception ex)
                            {
                                RhinoApp.WriteLine($"  TryGetSource failed: {ex.Message}");
                            }
                        }
                        
                        // Method 2: GetSource (no parameters) - fallback
                        if (string.IsNullOrEmpty(scriptContent))
                        {
                            var getSourceMethod = componentType.GetMethod("GetSource", new Type[0]);
                            if (getSourceMethod != null)
                            {
                                try
                                {
                                    scriptContent = getSourceMethod.Invoke(component, null) as string;
                                    if (!string.IsNullOrEmpty(scriptContent))
                                    {
                                        RhinoApp.WriteLine("  Script retrieved using GetSource()");
                                    }
                                }
                                catch (Exception ex)
                                {
                                    RhinoApp.WriteLine($"  GetSource() failed: {ex.Message}");
                                }
                            }
                        }
                        
                        // Method 3: GetSource with parameters - fallback
                        if (string.IsNullOrEmpty(scriptContent))
                        {
                            var getSourceMethodWithParams = componentType.GetMethod("GetSource", new Type[] { typeof(bool) });
                            if (getSourceMethodWithParams != null)
                            {
                                try
                                {
                                    scriptContent = getSourceMethodWithParams.Invoke(component, new object[] { true }) as string;
                                    if (!string.IsNullOrEmpty(scriptContent))
                                    {
                                        RhinoApp.WriteLine("  Script retrieved using GetSource(bool)");
                                    }
                                }
                                catch (Exception ex)
                                {
                                    RhinoApp.WriteLine($"  GetSource(bool) failed: {ex.Message}");
                                }
                            }
                        }
                        
                        // Method 4: Properties
                        if (string.IsNullOrEmpty(scriptContent))
                        {
                            string[] propNames = { "Code", "ScriptSource", "Text", "ScriptText", "Source", "Script", "SourceCode", "CodeText" };
                            foreach (var propName in propNames)
                            {
                                var prop = componentType.GetProperty(propName, BindingFlags.Public | BindingFlags.Instance);
                                if (prop != null && prop.CanRead)
                                {
                                    try
                                    {
                                        var value = prop.GetValue(component) as string;
                                        if (!string.IsNullOrEmpty(value))
                                        {
                                            scriptContent = value;
                                            RhinoApp.WriteLine($"  Script retrieved using {propName} property");
                                            break;
                                        }
                                        else
                                        {
                                            RhinoApp.WriteLine($"  Property {propName} returned empty/null");
                                        }
                                    }
                                    catch (Exception ex)
                                    {
                                        RhinoApp.WriteLine($"  Property {propName} failed: {ex.Message}");
                                    }
                                }
                            }
                        }
                        
                        // Method 5: Try to access internal/private fields and properties
                        if (string.IsNullOrEmpty(scriptContent))
                        {
                            RhinoApp.WriteLine("=== Trying private/internal members ===");
                            var allProperties = componentType.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                            foreach (var prop in allProperties.Where(p => p.Name.ToLower().Contains("source") || p.Name.ToLower().Contains("script") || p.Name.ToLower().Contains("code")))
                            {
                                if (prop.CanRead)
                                {
                                    try
                                    {
                                        var value = prop.GetValue(component) as string;
                                        if (!string.IsNullOrEmpty(value))
                                        {
                                            scriptContent = value;
                                            RhinoApp.WriteLine($"  Script retrieved using private/internal {prop.Name} property");
                                            break;
                                        }
                                    }
                                    catch (Exception ex)
                                    {
                                        RhinoApp.WriteLine($"  Private property {prop.Name} failed: {ex.Message}");
                                    }
                                }
                            }
                        }
                        
                        if (!string.IsNullOrEmpty(scriptContent))
                        {
                            result = new
                            {
                                id = component.InstanceGuid.ToString(),
                                type = componentType.Name,
                                name = component.NickName,
                                script = scriptContent
                            };
                        }
                        else
                        {
                            // Return detailed error information
                            var availableMethods = string.Join(", ", methods.Where(m => m.Name.ToLower().Contains("source") || m.Name.ToLower().Contains("script")).Select(m => m.Name));
                            var availableProps = string.Join(", ", properties.Where(p => p.Name.ToLower().Contains("source") || p.Name.ToLower().Contains("script")).Select(p => p.Name));
                            
                            throw new InvalidOperationException($"Could not retrieve script content from component. Available methods: [{availableMethods}]. Available properties: [{availableProps}]. Component type: {componentType.FullName}");
                        }
                    }
                    else
                    {
                        throw new ArgumentException($"Component is not a Python script component. Type: {componentType.Name}");
                    }
                }
                catch (Exception ex)
                {
                    exception = ex;
                    RhinoApp.WriteLine($"Error in GetPythonScriptContent: {ex.Message}");
                }
            }));
            
            // 等待 UI 線程操作完成
            while (result == null && exception == null)
            {
                Thread.Sleep(10);
            }
            
            // 如果有異常，拋出
            if (exception != null)
            {
                throw exception;
            }
            
            return result;
        }
        
        /// <summary>
        /// 設置 Python 腳本組件的內容
        /// </summary>
        /// <param name="command">包含組件 ID 和腳本內容的命令</param>
        /// <returns>操作結果</returns>
        public static object SetPythonScriptContent(Command command)
        {
            string idStr = command.GetParameter<string>("id");
            string script = command.GetParameter<string>("script");
            
            if (string.IsNullOrEmpty(idStr))
            {
                throw new ArgumentException("Component ID is required");
            }
            
            if (script == null) // Allow empty script
            {
                throw new ArgumentException("Script content is required");
            }
            
            object result = null;
            Exception exception = null;
            
            // 在 UI 線程上執行
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    // 獲取 Grasshopper 文檔
                    var doc = Grasshopper.Instances.ActiveCanvas?.Document;
                    if (doc == null)
                    {
                        throw new InvalidOperationException("No active Grasshopper document");
                    }
                    
                    // 將字符串 ID 轉換為 Guid
                    Guid id;
                    if (!Guid.TryParse(idStr, out id))
                    {
                        throw new ArgumentException("Invalid component ID format");
                    }
                    
                    // 查找組件
                    IGH_DocumentObject component = doc.FindObject(id, true);
                    if (component == null)
                    {
                        throw new ArgumentException($"Component with ID {idStr} not found");
                    }
                    
                    // Get component type information
                    var componentType = component.GetType();
                    RhinoApp.WriteLine($"SetPythonScriptContent: Found component of type {componentType.FullName}");
                    
                    // Check if this is a Python script component
                    if (component.NickName == "Py3" || componentType.Name.Contains("Script") || componentType.Name.Contains("Python"))
                    {
                        bool scriptSet = false;
                        
                        // Ensure script has Python 3 language specifier if not already present
                        string fullScript = script;
                        if (!script.StartsWith("#!"))
                        {
                            fullScript = "#! python 3\n\n" + script;
                        }
                        
                        // Try various methods to set the script
                        // Method 1: SetSource
                        var setSourceMethod = componentType.GetMethod("SetSource", new Type[] { typeof(string) });
                        if (setSourceMethod != null)
                        {
                            try
                            {
                                setSourceMethod.Invoke(component, new object[] { fullScript });
                                RhinoApp.WriteLine("  Script set using SetSource");
                                scriptSet = true;
                            }
                            catch (Exception ex)
                            {
                                RhinoApp.WriteLine($"  SetSource failed: {ex.Message}");
                            }
                        }
                        
                        // Method 2: Properties
                        if (!scriptSet)
                        {
                            string[] propNames = { "Code", "ScriptSource", "Text", "ScriptText", "Source", "Script" };
                            foreach (var propName in propNames)
                            {
                                var prop = componentType.GetProperty(propName);
                                if (prop != null && prop.CanWrite)
                                {
                                    try
                                    {
                                        prop.SetValue(component, fullScript);
                                        RhinoApp.WriteLine($"  Script set using {propName} property");
                                        scriptSet = true;
                                        break;
                                    }
                                    catch { }
                                }
                            }
                        }
                        
                        // Try to sync parameters
                        var syncMethod = componentType.GetMethod("SetParametersFromScript") ??
                                        componentType.GetMethod("SyncParametersFromScript");
                        if (syncMethod != null)
                        {
                            try
                            {
                                syncMethod.Invoke(component, null);
                                RhinoApp.WriteLine("  Parameters synced");
                            }
                            catch { }
                        }
                        
                        // Expire solution to recompute
                        if (component is IGH_ActiveObject activeObj)
                        {
                            activeObj.ExpireSolution(true);
                        }
                        
                        if (scriptSet)
                        {
                            result = new
                            {
                                id = component.InstanceGuid.ToString(),
                                type = componentType.Name,
                                name = component.NickName,
                                success = true
                            };
                        }
                        else
                        {
                            throw new InvalidOperationException("Could not set script content on component");
                        }
                    }
                    else
                    {
                        throw new ArgumentException($"Component is not a Python script component. Type: {componentType.Name}");
                    }
                }
                catch (Exception ex)
                {
                    exception = ex;
                    RhinoApp.WriteLine($"Error in SetPythonScriptContent: {ex.Message}");
                }
            }));
            
            // 等待 UI 線程操作完成
            while (result == null && exception == null)
            {
                Thread.Sleep(10);
            }
            
            // 如果有異常，拋出
            if (exception != null)
            {
                throw exception;
            }
            
            return result;
        }
        
        /// <summary>
        /// 獲取 Python 腳本組件的錯誤和警告信息
        /// </summary>
        /// <param name="command">包含組件 ID 的命令</param>
        /// <returns>錯誤和警告信息</returns>
        public static object GetPythonScriptErrors(Command command)
        {
            string idStr = command.GetParameter<string>("id");
            
            if (string.IsNullOrEmpty(idStr))
            {
                throw new ArgumentException("Component ID is required");
            }
            
            object result = null;
            Exception exception = null;
            
            // 在 UI 線程上執行
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    // 獲取 Grasshopper 文檔
                    var doc = Grasshopper.Instances.ActiveCanvas?.Document;
                    if (doc == null)
                    {
                        throw new InvalidOperationException("No active Grasshopper document");
                    }
                    
                    // 將字符串 ID 轉換為 Guid
                    Guid id;
                    if (!Guid.TryParse(idStr, out id))
                    {
                        throw new ArgumentException("Invalid component ID format");
                    }
                    
                    // 查找組件
                    IGH_DocumentObject component = doc.FindObject(id, true);
                    if (component == null)
                    {
                        throw new ArgumentException($"Component with ID {idStr} not found");
                    }
                    
                    // Get component type information
                    var componentType = component.GetType();
                    RhinoApp.WriteLine($"GetPythonScriptErrors: Found component of type {componentType.FullName}");
                    
                    // Check if this is a Python script component
                    if (component.NickName == "Py3" || componentType.Name.Contains("Script") || componentType.Name.Contains("Python"))
                    {
                        var messages = new List<string>();
                        var warnings = new List<string>();
                        var errors = new List<string>();
                        
                        // Try to get runtime messages using various methods
                        
                        // Method 1: Try RuntimeMessages property/method with different message levels
                        try
                        {
                            // Check if component implements IGH_ActiveObject
                            if (component is IGH_ActiveObject activeObject)
                            {
                                // Try different message levels to get all messages
                                var messageLevels = new[] { 
                                    GH_RuntimeMessageLevel.Error, 
                                    GH_RuntimeMessageLevel.Warning, 
                                    GH_RuntimeMessageLevel.Remark,
                                    GH_RuntimeMessageLevel.Blank
                                };
                                
                                foreach (var level in messageLevels)
                                {
                                    try
                                    {
                                        var runtimeMessages = activeObject.RuntimeMessages(level);
                                        if (runtimeMessages != null && runtimeMessages.Count > 0)
                                        {
                                            foreach (string message in runtimeMessages)
                                            {
                                                if (!messages.Contains(message)) // Avoid duplicates
                                                {
                                                    messages.Add(message);
                                                    
                                                    // Categorize based on level and content
                                                    if (level == GH_RuntimeMessageLevel.Error || 
                                                        message.ToLower().Contains("error") || 
                                                        message.ToLower().Contains("exception") || 
                                                        message.ToLower().Contains("failed"))
                                                    {
                                                        errors.Add(message);
                                                    }
                                                    else if (level == GH_RuntimeMessageLevel.Warning || 
                                                            message.ToLower().Contains("warning") || 
                                                            message.ToLower().Contains("warn"))
                                                    {
                                                        warnings.Add(message);
                                                    }
                                                }
                                            }
                                            RhinoApp.WriteLine($"  Retrieved {runtimeMessages.Count} {level} messages via IGH_ActiveObject");
                                        }
                                    }
                                    catch (Exception levelEx)
                                    {
                                        RhinoApp.WriteLine($"  Error accessing {level} messages: {levelEx.Message}");
                                    }
                                }
                                
                                if (messages.Count > 0)
                                {
                                    RhinoApp.WriteLine($"  Total retrieved {messages.Count} runtime messages via IGH_ActiveObject");
                                }
                                else
                                {
                                    RhinoApp.WriteLine("  No runtime messages found via IGH_ActiveObject");
                                }
                            }
                        }
                        catch (Exception ex)
                        {
                            RhinoApp.WriteLine($"  Error accessing runtime messages via IGH_ActiveObject: {ex.Message}");
                        }
                        
                        // Method 2: Try GH_Component RuntimeMessages if it's a GH_Component
                        if (messages.Count == 0)
                        {
                            try
                            {
                                // Use reflection to call RuntimeMessages(GH_RuntimeMessageLevel) method
                                var runtimeMessagesMethod = componentType.GetMethod("RuntimeMessages", new Type[] { typeof(GH_RuntimeMessageLevel) });
                                if (runtimeMessagesMethod != null)
                                {
                                    // Try different message levels via reflection
                                    var messageLevels = new[] { 
                                        GH_RuntimeMessageLevel.Error, 
                                        GH_RuntimeMessageLevel.Warning, 
                                        GH_RuntimeMessageLevel.Remark,
                                        GH_RuntimeMessageLevel.Blank
                                    };
                                    
                                    foreach (var level in messageLevels)
                                    {
                                        try
                                        {
                                            var runtimeMessages = runtimeMessagesMethod.Invoke(component, new object[] { level }) as System.Collections.IList;
                                            if (runtimeMessages != null && runtimeMessages.Count > 0)
                                            {
                                                foreach (var message in runtimeMessages)
                                                {
                                                    string messageStr = message.ToString();
                                                    if (!messages.Contains(messageStr)) // Avoid duplicates
                                                    {
                                                        messages.Add(messageStr);
                                                        // Try to categorize messages
                                                        if (level == GH_RuntimeMessageLevel.Error ||
                                                            messageStr.ToLower().Contains("error") || 
                                                            messageStr.ToLower().Contains("exception") || 
                                                            messageStr.ToLower().Contains("failed"))
                                                        {
                                                            errors.Add(messageStr);
                                                        }
                                                        else if (level == GH_RuntimeMessageLevel.Warning ||
                                                                messageStr.ToLower().Contains("warning") || 
                                                                messageStr.ToLower().Contains("warn"))
                                                        {
                                                            warnings.Add(messageStr);
                                                        }
                                                    }
                                                }
                                                RhinoApp.WriteLine($"  Retrieved {runtimeMessages.Count} {level} messages via reflection");
                                            }
                                        }
                                        catch (Exception levelEx)
                                        {
                                            RhinoApp.WriteLine($"  Error accessing {level} messages via reflection: {levelEx.Message}");
                                        }
                                    }
                                    
                                    if (messages.Count > 0)
                                    {
                                        RhinoApp.WriteLine($"  Total retrieved {messages.Count} runtime messages via reflection");
                                    }
                                    else
                                    {
                                        RhinoApp.WriteLine("  No runtime messages found via reflection");
                                    }
                                }
                                else
                                {
                                    RhinoApp.WriteLine("  RuntimeMessages method not found via reflection");
                                }
                            }
                            catch (Exception ex)
                            {
                                RhinoApp.WriteLine($"  Error accessing runtime messages via reflection: {ex.Message}");
                            }
                        }
                        
                        // Method 3: Try to access any error-related properties
                        if (messages.Count == 0)
                        {
                            RhinoApp.WriteLine("=== Searching for error-related properties ===");
                            var properties = componentType.GetProperties(BindingFlags.Public | BindingFlags.Instance);
                            foreach (var prop in properties.Where(p => p.Name.ToLower().Contains("error") || 
                                                                      p.Name.ToLower().Contains("message") || 
                                                                      p.Name.ToLower().Contains("runtime") ||
                                                                      p.Name.ToLower().Contains("exception")))
                            {
                                if (prop.CanRead)
                                {
                                    try
                                    {
                                        var value = prop.GetValue(component);
                                        if (value != null)
                                        {
                                            RhinoApp.WriteLine($"  Property {prop.Name}: {value}");
                                            
                                            // If it's a collection, try to enumerate it
                                            if (value is System.Collections.IEnumerable enumerable && !(value is string))
                                            {
                                                foreach (var item in enumerable)
                                                {
                                                    if (item != null)
                                                    {
                                                        messages.Add(item.ToString());
                                                    }
                                                }
                                            }
                                            else
                                            {
                                                string valueStr = value.ToString();
                                                if (!string.IsNullOrEmpty(valueStr) && valueStr != prop.PropertyType.Name)
                                                {
                                                    messages.Add(valueStr);
                                                }
                                            }
                                        }
                                    }
                                    catch (Exception ex)
                                    {
                                        RhinoApp.WriteLine($"  Error accessing property {prop.Name}: {ex.Message}");
                                    }
                                }
                            }
                        }
                        
                        // Check if component is in error state
                        bool hasErrors = false;
                        bool hasWarnings = false;
                        
                        // Try to check component state/color for error indication
                        try
                        {
                            if (component.Attributes != null)
                            {
                                // Check if we can determine error state from attributes
                                var attrType = component.Attributes.GetType();
                                RhinoApp.WriteLine($"Component attributes type: {attrType.FullName}");
                                
                                // Look for color or state properties that might indicate errors
                                var colorProps = attrType.GetProperties().Where(p => p.Name.ToLower().Contains("color") || 
                                                                                   p.Name.ToLower().Contains("state") ||
                                                                                   p.Name.ToLower().Contains("error")).ToList();
                                foreach (var prop in colorProps)
                                {
                                    if (prop.CanRead)
                                    {
                                        try
                                        {
                                            var value = prop.GetValue(component.Attributes);
                                            RhinoApp.WriteLine($"  Attribute {prop.Name}: {value}");
                                        }
                                        catch { }
                                    }
                                }
                            }
                        }
                        catch (Exception ex)
                        {
                            RhinoApp.WriteLine($"  Error checking component attributes: {ex.Message}");
                        }
                        
                        // Determine overall status
                        hasErrors = errors.Count > 0 || messages.Any(m => m.ToLower().Contains("error") || m.ToLower().Contains("exception") || m.ToLower().Contains("failed"));
                        hasWarnings = warnings.Count > 0 || messages.Any(m => m.ToLower().Contains("warning") || m.ToLower().Contains("warn"));
                        
                        result = new
                        {
                            id = component.InstanceGuid.ToString(),
                            type = componentType.Name,
                            name = component.NickName,
                            hasErrors = hasErrors,
                            hasWarnings = hasWarnings,
                            allMessages = messages,
                            errors = errors,
                            warnings = warnings,
                            messageCount = messages.Count,
                            status = hasErrors ? "error" : (hasWarnings ? "warning" : "ok")
                        };
                    }
                    else
                    {
                        throw new ArgumentException($"Component is not a Python script component. Type: {componentType.Name}");
                    }
                }
                catch (Exception ex)
                {
                    exception = ex;
                    RhinoApp.WriteLine($"Error in GetPythonScriptErrors: {ex.Message}");
                }
            }));
            
            // 等待 UI 線程操作完成
            while (result == null && exception == null)
            {
                Thread.Sleep(10);
            }
            
            // 如果有異常，拋出
            if (exception != null)
            {
                throw exception;
            }
            
            return result;
        }
        
        private static IGH_DocumentObject CreateComponentByName(string name)
        {
            var obj = Grasshopper.Instances.ComponentServer.ObjectProxies
                .FirstOrDefault(p => p.Desc.Name.Equals(name, StringComparison.OrdinalIgnoreCase));
                
            if (obj != null)
            {
                return obj.CreateInstance();
            }
            else
            {
                throw new ArgumentException($"Component with name {name} not found");
            }
        }
    }
}
