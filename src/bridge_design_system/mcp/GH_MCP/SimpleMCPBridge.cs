using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System.Net;
using System.Net.Http;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using System.Linq;
using System.Reflection;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Parameters;
using Grasshopper.Kernel.Special;
using Grasshopper.Kernel.Types;
using GH_IO.Serialization;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace VizorAgents.GH_MCP
{
    /// <summary>
    /// Simplified MCP Bridge Component - Client that polls MCP server for commands
    /// </summary>
    public class SimpleMCPBridge : GH_Component
    {
        private static readonly HttpClient _httpClient = new HttpClient() { Timeout = TimeSpan.FromSeconds(5) };
        private Timer _pollTimer;
        private bool _isConnected;
        private string _serverUrl = "http://localhost:8001";
        private readonly List<string> _logs = new List<string>();
        private readonly List<string> _commands = new List<string>();
        private readonly Dictionary<string, IGH_DocumentObject> _components = new Dictionary<string, IGH_DocumentObject>();
        private int _componentCounter = 0;

        public SimpleMCPBridge()
            : base("Simple MCP Bridge", "SMCP", "HTTP polling bridge for MCP command execution", "Params", "Util")
        {
        }

        public override Guid ComponentGuid => new Guid("C8D9E0F1-A2B3-4C5D-6E7F-8A9B0C1D2E3F");

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddBooleanParameter("Connect", "C", "Connect to MCP server", GH_ParamAccess.item, false);
            pManager.AddTextParameter("Server", "S", "MCP server URL", GH_ParamAccess.item, "http://localhost:8001");
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Status", "S", "Connection status", GH_ParamAccess.item);
            pManager.AddTextParameter("Log", "L", "Bridge log messages", GH_ParamAccess.list);
            pManager.AddTextParameter("Commands", "C", "Received commands", GH_ParamAccess.list);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            bool connect = false;
            string serverUrl = "";
            
            DA.GetData(0, ref connect);
            DA.GetData(1, ref serverUrl);

            if (!string.IsNullOrEmpty(serverUrl))
            {
                _serverUrl = serverUrl;
            }

            if (connect && !_isConnected)
            {
                StartPolling();
            }
            else if (!connect && _isConnected)
            {
                StopPolling();
            }

            DA.SetData(0, _isConnected ? $"Connected to {_serverUrl}" : "Not connected");
            DA.SetDataList(1, new List<string>(_logs));
            DA.SetDataList(2, new List<string>(_commands));
        }

        private void StartPolling()
        {
            try
            {
                _isConnected = true;
                _pollTimer = new Timer(PollServer, null, 0, 1000); // Poll every second
                AddLog($"Connected to MCP server at {_serverUrl}");
            }
            catch (Exception ex)
            {
                AddLog($"Failed to start polling: {ex.Message}");
                _isConnected = false;
            }
        }

        private void StopPolling()
        {
            try
            {
                _pollTimer?.Dispose();
                _pollTimer = null;
                _isConnected = false;
                AddLog("Disconnected from MCP server");
            }
            catch (Exception ex)
            {
                AddLog($"Error stopping: {ex.Message}");
            }
        }

        private void PollServer(object state)
        {
            if (!_isConnected) return;

            // Execute polling on UI thread to avoid all cross-thread issues
            Rhino.RhinoApp.InvokeOnUiThread(new Action(async () =>
            {
                try
                {
                    var response = await _httpClient.GetAsync($"{_serverUrl}/grasshopper/pending_commands");
                    
                    if (response.IsSuccessStatusCode)
                    {
                        var content = await response.Content.ReadAsStringAsync();
                        var commands = JsonConvert.DeserializeObject<List<Dictionary<string, object>>>(content);
                        
                        if (commands?.Any() == true)
                        {
                            AddLog($"📥 Processing {commands.Count} commands on UI thread");
                            
                            foreach (var command in commands)
                            {
                                await ExecuteCommandOnUIThread(command);
                            }
                            
                            // Update the component
                            this.ExpireSolution(true);
                        }
                    }
                }
                catch (Exception ex)
                {
                    // Only log connection errors once in a while to avoid spam
                    if (_logs.Count == 0 || !_logs.Last().Contains("Poll error"))
                    {
                        AddLog($"⚠️ Poll error: {ex.Message}");
                    }
                }
            }));
        }

        private async Task ExecuteCommandOnUIThread(Dictionary<string, object> command)
        {
            string commandType = null;
            string commandId = null;
            
            try
            {
                commandType = command["type"]?.ToString();
                commandId = command["id"]?.ToString();
                var parameters = command["parameters"] as JObject;

                // Enhanced logging based on reference implementation
                AddCommand($"{commandType} (ID: {commandId})");
                AddLog($"Executing command: {commandType} with {parameters?.Count ?? 0} parameters");

                // Validate required fields
                if (string.IsNullOrEmpty(commandType))
                {
                    throw new ArgumentException("Command type is null or empty");
                }
                
                if (string.IsNullOrEmpty(commandId))
                {
                    throw new ArgumentException("Command ID is null or empty");
                }

                switch (commandType)
                {
                    case "add_component":
                        await HandleAddComponent(commandId, parameters);
                        break;
                        
                    case "add_python3_script":
                        await HandleAddPython3ScriptOnUI(commandId, parameters);
                        break;
                        
                    case "clear_document":
                        await HandleClearDocumentOnUI(commandId);
                        break;
                        
                    case "get_python_script_content":
                    case "get_python3_script":
                        await HandleGetPythonScriptContent(commandId, parameters);
                        break;
                        
                    case "set_python_script_content":
                    case "edit_python3_script":
                        await HandleSetPythonScriptContent(commandId, parameters);
                        break;
                        
                    case "get_python_script_errors":
                    case "get_python3_script_errors":
                        await HandleGetPythonScriptErrors(commandId, parameters);
                        break;
                        
                    case "get_document_info":
                        await HandleGetDocumentInfo(commandId, parameters);
                        break;
                        
                    case "get_all_components":
                        await HandleGetAllComponents(commandId, parameters);
                        break;
                        
                    case "get_all_components_enhanced":
                        await HandleGetAllComponents(commandId, parameters);
                        break;
                        
                    default:
                        var errorMsg = $"No handler registered for command type '{commandType}'";
                        AddLog($"❌ {errorMsg}");
                        
                        // List available commands for debugging
                        var availableCommands = new[] { 
                            "add_component", "add_python3_script", "clear_document", 
                            "get_python_script_content", "get_python3_script", 
                            "set_python_script_content", "edit_python3_script",
                            "get_python_script_errors", "get_python3_script_errors",
                            "get_document_info", "get_all_components", "get_all_components_enhanced"
                        };
                        
                        await ReportResult(commandId, false, new { 
                            error = errorMsg,
                            available_commands = availableCommands,
                            received_command = commandType
                        });
                        break;
                }
                
                AddLog($"✅ Command {commandType} completed successfully");
            }
            catch (ArgumentException ex)
            {
                var errorMsg = $"Invalid command arguments for '{commandType}': {ex.Message}";
                AddLog($"❌ {errorMsg}");
                await ReportResult(commandId ?? "unknown", false, new { 
                    error = errorMsg,
                    exception_type = "ArgumentException"
                });
            }
            catch (InvalidOperationException ex)
            {
                var errorMsg = $"Operation failed for '{commandType}': {ex.Message}";
                AddLog($"❌ {errorMsg}");
                await ReportResult(commandId ?? "unknown", false, new { 
                    error = errorMsg,
                    exception_type = "InvalidOperationException"
                });
            }
            catch (Exception ex)
            {
                var errorMsg = $"Unexpected error executing '{commandType}': {ex.Message}";
                AddLog($"❌ {errorMsg}");
                AddLog($"Stack trace: {ex.StackTrace}");
                
                await ReportResult(commandId ?? "unknown", false, new { 
                    error = errorMsg,
                    exception_type = ex.GetType().Name,
                    stack_trace = ex.StackTrace?.Split('\n').Take(5).ToArray() // First 5 lines only
                });
            }
        }

        private async Task HandleAddComponent(string commandId, JObject parameters)
        {
            try
            {
                var componentType = parameters["component_type"]?.ToString();
                var x = parameters["x"]?.Value<double>() ?? 0;
                var y = parameters["y"]?.Value<double>() ?? 0;
                var script = parameters["script"]?.ToString();

                AddLog($"🔧 Creating component: {componentType} at ({x}, {y})");

                // We're already on UI thread, so execute directly
                var document = this.OnPingDocument();
                if (document == null)
                {
                    throw new InvalidOperationException("Cannot access document");
                }

                IGH_DocumentObject component = null;
                
                // Create component based on type
                switch (componentType?.ToLower())
                {
                    case "point":
                    case "pt":
                        component = new Param_Point();
                        break;
                    case "number":
                    case "num":
                        component = new GH_NumberSlider();
                        break;
                    case "panel":
                        component = new GH_Panel();
                        break;
                    case "py3":
                    case "python3":
                    case "python script":
                        component = CreatePythonComponentEmpty();
                        break;
                    default:
                        throw new ArgumentException($"Unknown component type: {componentType}");
                }

                if (component == null)
                {
                    throw new InvalidOperationException($"Failed to create component of type: {componentType}");
                }

                // Set up the component
                component.CreateAttributes();
                component.Attributes.Pivot = new System.Drawing.PointF((float)x, (float)y);

                // Add to document
                document.AddObject(component, false);
                
                // Track component
                var componentId = $"comp_{++_componentCounter}";
                _components[componentId] = component;
                
                // Schedule solution
                document.ScheduleSolution(10);
                
                AddLog($"✅ Added {componentType} at ({x}, {y})");

                var result = new { component_id = componentId, type = componentType };
                await ReportResult(commandId, true, result);
            }
            catch (Exception ex)
            {
                AddLog($"❌ Failed to add component: {ex.Message}");
                await ReportResult(commandId, false, new { error = ex.Message });
            }
        }

        private async Task HandleAddPython3ScriptOnUI(string commandId, JObject parameters)
        {
            try
            {
                var x = parameters["x"]?.Value<double>() ?? 100;
                var y = parameters["y"]?.Value<double>() ?? 100;
                var script = parameters["script"]?.ToString() ?? "";
                var name = parameters["name"]?.ToString() ?? "Python Script";

                AddLog($"🐍 Creating Python3 script: {name} at ({x}, {y}) with {script.Length} chars");

                // Get the current document - we're already on UI thread
                var document = this.OnPingDocument();
                if (document == null)
                {
                    throw new InvalidOperationException("Cannot access document");
                }

                // Create Python component WITHOUT script first
                var component = CreatePythonComponentEmpty();
                if (component == null)
                {
                    throw new InvalidOperationException("Failed to create Python component");
                }

                // Set up the component
                component.CreateAttributes();
                component.Attributes.Pivot = new System.Drawing.PointF((float)x, (float)y);
                
                // Set name if provided
                if (!string.IsNullOrEmpty(name))
                {
                    component.NickName = name;
                }

                // Add to document FIRST
                document.AddObject(component, false);
                
                // Track component
                var componentId = $"comp_{++_componentCounter}";
                _components[componentId] = component;
                
                // NOW set the script AFTER component is in document
                if (!string.IsNullOrEmpty(script))
                {
                    bool scriptResult = SetComponentScript(component, script);
                    if (!scriptResult)
                    {
                        AddLog("⚠️ Warning: Could not set script content");
                    }
                    else
                    {
                        AddLog($"✅ Script set successfully on component {componentId}");
                    }
                }
                
                // Schedule solution LAST to execute the script
                document.ScheduleSolution(10);
                
                AddLog($"✅ Python script component created successfully");

                // Return success result
                var result = new { 
                    component_id = componentId, 
                    type = "Python3",
                    name = name,
                    script_length = script?.Length ?? 0,
                    script_preview = script?.Length > 50 ? script.Substring(0, 50) + "..." : script
                };
                
                await ReportResult(commandId, true, result);
            }
            catch (Exception ex)
            {
                AddLog($"❌ Failed to add Python script: {ex.Message}");
                await ReportResult(commandId, false, new { error = ex.Message });
            }
        }


        private async Task HandleClearDocumentOnUI(string commandId)
        {
            try
            {
                AddLog("🧹 Clearing MCP-created components...");
                
                var document = this.OnPingDocument();
                if (document == null)
                {
                    throw new InvalidOperationException("Cannot access document");
                }

                // Only remove components we created via MCP commands
                var toRemove = new List<IGH_DocumentObject>();
                
                foreach (var kvp in _components)
                {
                    if (document.Objects.Contains(kvp.Value))
                    {
                        toRemove.Add(kvp.Value);
                    }
                }
                
                foreach (var obj in toRemove)
                {
                    document.RemoveObject(obj, false);
                }
                
                _components.Clear();
                document.ScheduleSolution(10);
                
                AddLog($"✅ Cleared {toRemove.Count} MCP-created components");
                
                var result = new { cleared = true, removed_count = toRemove.Count };
                await ReportResult(commandId, true, result);
            }
            catch (Exception ex)
            {
                AddLog($"❌ Failed to clear: {ex.Message}");
                await ReportResult(commandId, false, new { error = ex.Message });
            }
        }

        private IGH_DocumentObject CreatePythonComponentEmpty()
        {
            try
            {
                AddLog("=== Creating Python 3 Component ===");
                AddLog("Looking for Py3 component specifically...");
                
                IGH_ObjectProxy pythonProxy = null;
                
                // Strategy 1: Look in the Maths/Script category specifically
                AddLog("Searching in Maths/Script category");
                var mathsScriptComponents = Grasshopper.Instances.ComponentServer.ObjectProxies
                    .Where(p => p.Desc.Category == "Maths" && p.Desc.SubCategory == "Script")
                    .ToList();
                
                foreach (var comp in mathsScriptComponents)
                {
                    AddLog($"Found: '{comp.Desc.Name}' (GUID: {comp.Guid})");
                    
                    // Check if this is the unified Script component or a Python 3 specific one
                    if (comp.Desc.Name == "Script" || 
                        (comp.Desc.Name.Contains("Python") && comp.Desc.Name.Contains("3")))
                    {
                        pythonProxy = comp;
                        AddLog($"Selected: {comp.Desc.Name}");
                        break;
                    }
                }
                
                // Strategy 2: Look for components by their display name/nickname "Py3"
                if (pythonProxy == null)
                {
                    AddLog("Searching all components for Py3 nickname");
                    
                    var allComponents = Grasshopper.Instances.ComponentServer.ObjectProxies.ToList();
                    AddLog($"Total components available: {allComponents.Count}");
                    
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
                                AddLog($"Component: {proxy.Desc.Name}, NickName: {instance.NickName}");
                                
                                // Check if this creates the "Py3" component we need
                                if (instance.NickName == "Py3" || 
                                    instance.NickName == "Python 3" ||
                                    (proxy.Desc.Name.Contains("Python") && 
                                     !proxy.Desc.Name.Contains("2") && 
                                     (proxy.Desc.Name.Contains("3") || !proxy.Desc.Name.Contains("Legacy"))))
                                {
                                    pythonProxy = proxy;
                                    AddLog("*** THIS IS THE PY3 COMPONENT! ***");
                                    break;
                                }
                            }
                        }
                        catch (Exception ex)
                        {
                            AddLog($"Error checking {proxy.Desc.Name}: {ex.Message}");
                        }
                    }
                }
                
                // Strategy 3: Try known GUIDs for Python components
                if (pythonProxy == null)
                {
                    AddLog("Trying known component GUIDs");
                    
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
                                AddLog($"Found component with GUID {guid}: NickName: {testComponent.NickName}");
                                
                                if (testComponent.NickName == "Py3")
                                {
                                    AddLog("*** THIS IS THE PY3 COMPONENT! ***");
                                    return testComponent;
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
                IGH_DocumentObject component = null;
                if (pythonProxy != null)
                {
                    component = pythonProxy.CreateInstance();
                    AddLog($"Created component: {pythonProxy.Desc.Name}");
                }
                
                // Last resort - use any Python component that's NOT IronPython 2
                if (component == null)
                {
                    AddLog("Last resort: finding any non-legacy Python component");
                    pythonProxy = Grasshopper.Instances.ComponentServer.ObjectProxies
                        .FirstOrDefault(p => p.Desc.Name.Contains("Python") && 
                                           !p.Desc.Name.Contains("Legacy") && 
                                           !p.Desc.Name.Contains("IronPython"));
                    
                    if (pythonProxy != null)
                    {
                        component = pythonProxy.CreateInstance();
                        AddLog($"Using fallback: {pythonProxy.Desc.Name}");
                    }
                    else
                    {
                        AddLog("ERROR: No Python component found in Grasshopper");
                        return null;
                    }
                }
                
                // Return the component WITHOUT setting script
                return component;
            }
            catch (Exception ex)
            {
                AddLog($"Error creating Python component: {ex.Message}");
                return null;
            }
        }
        
        private bool SetComponentScript(IGH_DocumentObject component, string script)
        {
            try
            {
                if (string.IsNullOrEmpty(script))
                {
                    return false;
                }

                var componentType = component.GetType();
                AddLog($"Setting script on: {componentType.FullName}");
                bool scriptSet = false;
                
                // Use EXACT format from reference implementation: "#! python 3\n\n"
                string fullScript = script;
                if (!script.StartsWith("#!"))
                {
                    fullScript = "#! python 3\n\n" + script;  // Reference implementation format
                }
                
                // Try different SetSource method signatures based on reference
                var setSourceMethods = componentType.GetMethods().Where(m => m.Name == "SetSource").ToArray();
                
                // Method 1: SetSource with silent flag (preferred - avoids popup)
                var setSourceSilentMethod = setSourceMethods.FirstOrDefault(m => 
                    m.GetParameters().Length == 2 && 
                    m.GetParameters()[0].ParameterType == typeof(string) &&
                    m.GetParameters()[1].ParameterType == typeof(bool));
                
                if (setSourceSilentMethod != null)
                {
                    try
                    {
                        setSourceSilentMethod.Invoke(component, new object[] { fullScript, true }); // Silent = true
                        AddLog($"✅ Script set using SetSource(string, bool) with silent=true");
                        scriptSet = true;
                    }
                    catch (Exception ex)
                    {
                        AddLog($"SetSource(string, bool) failed: {ex.Message}");
                    }
                }
                
                // Method 2: Standard SetSource as fallback
                if (!scriptSet)
                {
                    var setSourceMethod = componentType.GetMethod("SetSource", new Type[] { typeof(string) });
                    if (setSourceMethod != null)
                    {
                        try
                        {
                            setSourceMethod.Invoke(component, new object[] { fullScript });
                            AddLog($"✅ Script set using SetSource(string)");
                            scriptSet = true;
                        }
                        catch (Exception ex)
                        {
                            AddLog($"SetSource(string) failed: {ex.Message}");
                        }
                    }
                }
                
                // Method 3: Properties as last resort
                if (!scriptSet)
                {
                    AddLog("Trying property-based script setting");
                    string[] propNames = { "Code", "ScriptSource", "Text", "ScriptText", "Source" };
                    foreach (var propName in propNames)
                    {
                        var prop = componentType.GetProperty(propName);
                        if (prop != null && prop.CanWrite)
                        {
                            try
                            {
                                prop.SetValue(component, fullScript);
                                AddLog($"✅ Script set using {propName} property");
                                scriptSet = true;
                                break;
                            }
                            catch (Exception ex)
                            {
                                AddLog($"{propName} property failed: {ex.Message}");
                            }
                        }
                    }
                }
                
                // Enhanced error handling based on reference implementation
                if (scriptSet)
                {
                    // Try to sync parameters - reference implementation approach
                    var syncMethod = componentType.GetMethod("SetParametersFromScript") ??
                                    componentType.GetMethod("SyncParametersFromScript");
                    if (syncMethod != null)
                    {
                        try
                        {
                            syncMethod.Invoke(component, null);
                            AddLog("✅ Parameters synced successfully");
                        }
                        catch (Exception ex)
                        {
                            AddLog($"⚠️ Parameter sync failed: {ex.Message}");
                            // Don't fail the whole operation for sync issues
                        }
                    }
                    
                    AddLog($"✅ Script successfully set on component (length: {script.Length})");
                }
                else
                {
                    AddLog("❌ ERROR: Could not set script content with any method");
                    // Log available methods for debugging
                    var availableMethods = string.Join(", ", setSourceMethods.Select(m => 
                        $"{m.Name}({string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name))})"));
                    AddLog($"Available SetSource methods: {availableMethods}");
                }
                
                return scriptSet;
            }
            catch (Exception ex)
            {
                AddLog($"❌ EXCEPTION in SetComponentScript: {ex.Message}");
                AddLog($"Stack trace: {ex.StackTrace}");
                return false;
            }
        }

        private async Task HandleGetPythonScriptContent(string commandId, JObject parameters)
        {
            try
            {
                var componentId = parameters["component_id"]?.ToString() ?? parameters["id"]?.ToString();
                if (string.IsNullOrEmpty(componentId))
                {
                    await ReportResult(commandId, false, new { error = "Missing component ID" });
                    return;
                }

                if (!_components.ContainsKey(componentId))
                {
                    await ReportResult(commandId, false, new { error = "Component not found" });
                    return;
                }

                var component = _components[componentId];
                var script = GetPythonScript(component);
                
                await ReportResult(commandId, true, new { 
                    script = script ?? "",
                    component_id = componentId,
                    name = component.Name
                });
            }
            catch (Exception ex)
            {
                AddLog($"Error getting Python script: {ex.Message}");
                await ReportResult(commandId, false, new { error = ex.Message });
            }
        }

        private async Task HandleSetPythonScriptContent(string commandId, JObject parameters)
        {
            try
            {
                var componentId = parameters["component_id"]?.ToString() ?? parameters["id"]?.ToString();
                var script = parameters["script"]?.ToString();
                
                if (string.IsNullOrEmpty(componentId))
                {
                    await ReportResult(commandId, false, new { error = "Missing component ID" });
                    return;
                }

                if (!_components.ContainsKey(componentId))
                {
                    await ReportResult(commandId, false, new { error = "Component not found" });
                    return;
                }

                AddLog($"📝 Setting script on component {componentId} (length: {script?.Length ?? 0})");

                // We're already on UI thread, so execute directly
                var component = _components[componentId] as IGH_DocumentObject;
                if (component == null)
                {
                    throw new InvalidOperationException("Component not found in tracked components");
                }

                bool scriptResult = SetComponentScript(component, script);
                if (!scriptResult)
                {
                    throw new InvalidOperationException("Failed to set script content");
                }
                
                // Schedule solution to update the component
                var document = this.OnPingDocument();
                document?.ScheduleSolution(10);
                
                AddLog($"✅ Updated script for component {componentId}");
                
                var result = new { 
                    component_id = componentId,
                    script_updated = true,
                    script_length = script?.Length ?? 0
                };

                await ReportResult(commandId, true, result);
            }
            catch (Exception ex)
            {
                AddLog($"❌ Error setting Python script: {ex.Message}");
                await ReportResult(commandId, false, new { error = ex.Message });
            }
        }

        private async Task HandleGetPythonScriptErrors(string commandId, JObject parameters)
        {
            try
            {
                var componentId = parameters["component_id"]?.ToString() ?? parameters["id"]?.ToString();
                if (string.IsNullOrEmpty(componentId))
                {
                    await ReportResult(commandId, false, new { error = "Missing component ID" });
                    return;
                }

                if (!_components.ContainsKey(componentId))
                {
                    await ReportResult(commandId, false, new { error = "Component not found" });
                    return;
                }

                var component = _components[componentId] as GH_Component;
                if (component == null)
                {
                    await ReportResult(commandId, false, new { error = "Component is not a GH_Component" });
                    return;
                }

                var errors = GetPythonScriptErrors(component);
                
                await ReportResult(commandId, true, new { 
                    component_id = componentId,
                    errors = errors,
                    has_errors = errors.Count > 0
                });
            }
            catch (Exception ex)
            {
                AddLog($"Error getting Python script errors: {ex.Message}");
                await ReportResult(commandId, false, new { error = ex.Message });
            }
        }

        private async Task HandleGetDocumentInfo(string commandId, JObject parameters)
        {
            try
            {
                var document = this.OnPingDocument();
                if (document == null)
                {
                    await ReportResult(commandId, false, new { error = "Cannot access document" });
                    return;
                }

                var components = new List<object>();
                
                foreach (var obj in document.Objects)
                {
                    var component = obj as GH_Component;
                    if (component != null)
                    {
                        components.Add(new {
                            id = FindComponentId(component),
                            name = component.Name,
                            nickname = component.NickName,
                            type = component.GetType().Name,
                            x = component.Attributes?.Pivot.X ?? 0,
                            y = component.Attributes?.Pivot.Y ?? 0,
                            enabled = !component.Locked
                        });
                    }
                }

                await ReportResult(commandId, true, new { 
                    components = components,
                    total_objects = document.ObjectCount,
                    document_name = document.DisplayName
                });
            }
            catch (Exception ex)
            {
                AddLog($"Error getting document info: {ex.Message}");
                await ReportResult(commandId, false, new { error = ex.Message });
            }
        }

        private async Task HandleGetAllComponents(string commandId, JObject parameters)
        {
            try
            {
                var document = this.OnPingDocument();
                if (document == null)
                {
                    await ReportResult(commandId, false, new { error = "Cannot access document" });
                    return;
                }

                var components = new List<object>();
                
                foreach (var obj in document.Objects)
                {
                    components.Add(new {
                        id = FindComponentId(obj),
                        name = obj.Name,
                        nickname = obj.NickName,
                        type = obj.GetType().Name,
                        x = obj.Attributes?.Pivot.X ?? 0,
                        y = obj.Attributes?.Pivot.Y ?? 0
                    });
                }

                await ReportResult(commandId, true, new { 
                    components = components,
                    count = components.Count
                });
            }
            catch (Exception ex)
            {
                AddLog($"Error getting all components: {ex.Message}");
                await ReportResult(commandId, false, new { error = ex.Message });
            }
        }

        private string GetPythonScript(IGH_DocumentObject component)
        {
            try
            {
                var type = component.GetType();
                
                // Try common property names for Python scripts
                var scriptProperties = new[] { "Code", "Script", "PythonScript", "CodeInput" };
                
                foreach (var propName in scriptProperties)
                {
                    var prop = type.GetProperty(propName, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                    if (prop != null && prop.CanRead)
                    {
                        var value = prop.GetValue(component);
                        if (value != null)
                        {
                            return value.ToString();
                        }
                    }
                }
                
                return "";
            }
            catch (Exception ex)
            {
                AddLog($"Failed to get Python script: {ex.Message}");
                return "";
            }
        }

        private List<string> GetPythonScriptErrors(GH_Component component)
        {
            var errors = new List<string>();
            
            try
            {
                // Check component runtime messages using proper access
                try
                {
                    // Try to access runtime messages via reflection since it might be a method
                    var type = component.GetType();
                    var messagesProperty = type.GetProperty("RuntimeMessages", BindingFlags.Public | BindingFlags.Instance);
                    if (messagesProperty != null && messagesProperty.CanRead)
                    {
                        var messages = messagesProperty.GetValue(component);
                        if (messages != null && messages is IEnumerable enumerable)
                        {
                            foreach (var message in enumerable)
                            {
                                // Use reflection to get message properties
                                var msgType = message.GetType();
                                var levelProp = msgType.GetProperty("Level");
                                var textProp = msgType.GetProperty("Text");
                                
                                if (levelProp != null && textProp != null)
                                {
                                    var level = levelProp.GetValue(message);
                                    var text = textProp.GetValue(message);
                                    
                                    if (level != null && text != null)
                                    {
                                        var levelName = level.ToString();
                                        if (levelName.Contains("Error") || levelName.Contains("Warning"))
                                        {
                                            errors.Add($"[{levelName}] {text}");
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                catch
                {
                    // If runtime messages access fails, continue with other methods
                }
                
                // Try to get more detailed error information using reflection
                var errorProperties = new[] { "Errors", "Messages", "RuntimeErrors", "ScriptErrors" };
                
                foreach (var propName in errorProperties)
                {
                    try
                    {
                        var prop = component.GetType().GetProperty(propName, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                        if (prop != null && prop.CanRead)
                        {
                            var value = prop.GetValue(component);
                            if (value != null)
                            {
                                if (value is IEnumerable enumerable && !(value is string))
                                {
                                    foreach (var item in enumerable)
                                    {
                                        if (item != null)
                                        {
                                            errors.Add(item.ToString());
                                        }
                                    }
                                }
                                else if (value is string singleError && !string.IsNullOrEmpty(singleError))
                                {
                                    errors.Add(singleError);
                                }
                            }
                        }
                    }
                    catch
                    {
                        // Continue with next property if this one fails
                    }
                }
            }
            catch (Exception ex)
            {
                errors.Add($"Error retrieving script errors: {ex.Message}");
            }
            
            return errors;
        }

        private string FindComponentId(IGH_DocumentObject component)
        {
            // Find the ID we assigned to this component
            foreach (var kvp in _components)
            {
                if (kvp.Value == component)
                {
                    return kvp.Key;
                }
            }
            
            // If not found, create a new ID
            var newId = $"comp_{++_componentCounter}";
            _components[newId] = component;
            return newId;
        }

        private async Task ReportResult(string commandId, bool success, object result)
        {
            try
            {
                // Enhanced result reporting based on reference implementation
                var payload = new
                {
                    command_id = commandId,
                    success = success,
                    data = success ? result : null,
                    error = success ? null : result?.ToString(),
                    timestamp = DateTime.UtcNow.ToString("O"),
                    // Additional debugging info for failed operations
                    debug_info = success ? null : new
                    {
                        component_count = _components.Count,
                        last_log_entries = _logs.Skip(Math.Max(0, _logs.Count - 3)).ToArray()
                    }
                };

                var json = JsonConvert.SerializeObject(payload, Formatting.Indented);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                var response = await _httpClient.PostAsync($"{_serverUrl}/grasshopper/command_result", content);
                
                if (!response.IsSuccessStatusCode)
                {
                    AddLog($"⚠️ Failed to report result: HTTP {response.StatusCode}");
                }
            }
            catch (Exception ex)
            {
                AddLog($"⚠️ Error reporting result: {ex.Message}");
            }
        }

        private void AddLog(string message)
        {
            var logEntry = $"[{DateTime.Now:HH:mm:ss}] {message}";
            _logs.Add(logEntry);
            
            // Keep only last 50 messages
            if (_logs.Count > 50)
            {
                _logs.RemoveAt(0);
            }
        }

        private void AddCommand(string command)
        {
            var cmdEntry = $"[{DateTime.Now:HH:mm:ss}] {command}";
            _commands.Add(cmdEntry);
            
            // Keep only last 30 commands
            if (_commands.Count > 30)
            {
                _commands.RemoveAt(0);
            }
        }

        public override void RemovedFromDocument(GH_Document document)
        {
            StopPolling();
            base.RemovedFromDocument(document);
        }
    }
}