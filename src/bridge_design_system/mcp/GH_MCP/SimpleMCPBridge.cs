using System;
using System.Collections.Generic;
using System.Text;
using System.Net;
using System.Net.Http;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using System.Linq;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Parameters;
using Grasshopper.Kernel.Special;
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

        private async void PollServer(object state)
        {
            if (!_isConnected) return;

            try
            {
                var response = await _httpClient.GetAsync($"{_serverUrl}/grasshopper/pending_commands");
                
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    var commands = JsonConvert.DeserializeObject<List<Dictionary<string, object>>>(content);
                    
                    if (commands?.Any() == true)
                    {
                        foreach (var command in commands)
                        {
                            await ExecuteCommand(command);
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
                    AddLog($"Poll error: {ex.Message}");
                }
            }
        }

        private async Task ExecuteCommand(Dictionary<string, object> command)
        {
            try
            {
                var commandType = command["type"]?.ToString();
                var commandId = command["id"]?.ToString();
                var parameters = command["parameters"] as JObject;

                AddCommand($"{commandType}: {parameters}");

                switch (commandType)
                {
                    case "add_component":
                        await HandleAddComponent(commandId, parameters);
                        break;
                        
                    case "clear_document":
                        await HandleClearDocument(commandId);
                        break;
                        
                    default:
                        AddLog($"Unknown command: {commandType}");
                        break;
                }
            }
            catch (Exception ex)
            {
                AddLog($"Command error: {ex.Message}");
            }
        }

        private async Task HandleAddComponent(string commandId, JObject parameters)
        {
            var componentType = parameters["component_type"]?.ToString();
            var x = parameters["x"]?.Value<double>() ?? 0;
            var y = parameters["y"]?.Value<double>() ?? 0;

            try
            {
                // Get the current document
                var document = this.OnPingDocument();
                if (document == null)
                {
                    AddLog("Cannot access document");
                    return;
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
                    default:
                        AddLog($"Unknown component type: {componentType}");
                        return;
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
                
                AddLog($"Added {componentType} at ({x}, {y})");

                // Report success
                await ReportResult(commandId, true, new { component_id = componentId });
            }
            catch (Exception ex)
            {
                AddLog($"Failed to add component: {ex.Message}");
                await ReportResult(commandId, false, new { error = ex.Message });
            }
        }

        private async Task HandleClearDocument(string commandId)
        {
            try
            {
                var document = this.OnPingDocument();
                if (document != null)
                {
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
                    
                    AddLog($"Cleared {toRemove.Count} MCP-created components");
                    await ReportResult(commandId, true, new { cleared = true, removed_count = toRemove.Count });
                }
            }
            catch (Exception ex)
            {
                AddLog($"Failed to clear: {ex.Message}");
                await ReportResult(commandId, false, new { error = ex.Message });
            }
        }

        private async Task ReportResult(string commandId, bool success, object result)
        {
            try
            {
                var payload = new
                {
                    command_id = commandId,
                    success = success,
                    result = result,
                    timestamp = DateTime.UtcNow.ToString("O")
                };

                var json = JsonConvert.SerializeObject(payload);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                await _httpClient.PostAsync($"{_serverUrl}/grasshopper/command_result", content);
            }
            catch
            {
                // Ignore reporting errors
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