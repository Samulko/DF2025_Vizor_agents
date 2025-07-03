using System;
using System.Collections.Generic;
using GH_MCP.Commands;
using GrasshopperMCP.Models;
using GrasshopperMCP.Commands;
using Grasshopper.Kernel;
using Rhino;
using System.Linq;

namespace GH_MCP.Commands
{
    /// <summary>
    /// Grasshopper 命令註冊表，用於註冊和執行命令
    /// </summary>
    public static class GrasshopperCommandRegistry
    {
        // 命令處理器字典，鍵為命令類型，值為處理命令的函數
        private static readonly Dictionary<string, Func<Command, object>> CommandHandlers = new Dictionary<string, Func<Command, object>>();

        /// <summary>
        /// 初始化命令註冊表
        /// </summary>
        public static void Initialize()
        {
            try
            {
                RhinoApp.WriteLine("GH_MCP: Starting command registry initialization...");
                
                // 清空现有的命令处理器
                CommandHandlers.Clear();
                RhinoApp.WriteLine("GH_MCP: Cleared existing command handlers.");
                
                // 註冊幾何命令
                RhinoApp.WriteLine("GH_MCP: Registering geometry commands...");
                RegisterGeometryCommands();
                
                // 註冊組件命令
                RhinoApp.WriteLine("GH_MCP: Registering component commands...");
                RegisterComponentCommands();
                
                // 註冊文檔命令
                RhinoApp.WriteLine("GH_MCP: Registering document commands...");
                RegisterDocumentCommands();
                
                // 註冊意圖命令
                RhinoApp.WriteLine("GH_MCP: Registering intent commands...");
                RegisterIntentCommands();
                
                // 显示所有已注册的命令
                RhinoApp.WriteLine($"GH_MCP: Command registry initialized with {CommandHandlers.Count} commands:");
                foreach (var command in CommandHandlers.Keys)
                {
                    RhinoApp.WriteLine($"  - {command}");
                }
            }
            catch (Exception ex)
            {
                RhinoApp.WriteLine($"GH_MCP: ERROR during command registry initialization: {ex.Message}");
                RhinoApp.WriteLine($"GH_MCP: Stack trace: {ex.StackTrace}");
            }
        }

        /// <summary>
        /// 註冊幾何命令
        /// </summary>
        private static void RegisterGeometryCommands()
        {
            // 創建點
            RegisterCommand("create_point", GeometryCommandHandler.CreatePoint);
            
            // 創建曲線
            RegisterCommand("create_curve", GeometryCommandHandler.CreateCurve);
            
            // 創建圓
            RegisterCommand("create_circle", GeometryCommandHandler.CreateCircle);
        }

        /// <summary>
        /// 註冊組件命令
        /// </summary>
        private static void RegisterComponentCommands()
        {
            // 添加組件
            RegisterCommand("add_component", ComponentCommandHandler.AddComponent);
            
            // 連接組件
            RegisterCommand("connect_components", ConnectionCommandHandler.ConnectComponents);
            
            // 設置組件值
            RegisterCommand("set_component_value", ComponentCommandHandler.SetComponentValue);
            
            // 獲取組件信息
            RegisterCommand("get_component_info", ComponentCommandHandler.GetComponentInfo);
            
            // 獲取 Python 腳本內容
            RegisterCommand("get_python_script_content", ComponentCommandHandler.GetPythonScriptContent);
            
            // 設置 Python 腳本內容
            RegisterCommand("set_python_script_content", ComponentCommandHandler.SetPythonScriptContent);
            
            // 獲取 Python 腳本錯誤信息
            RegisterCommand("get_python_script_errors", ComponentCommandHandler.GetPythonScriptErrors);
            
            // 獲取所有連接
            RegisterCommand("get_connections", ConnectionCommandHandler.GetConnections);
        }

        /// <summary>
        /// 註冊文檔命令
        /// </summary>
        private static void RegisterDocumentCommands()
        {
            try
            {
                // 獲取文檔信息
                RegisterCommand("get_document_info", DocumentCommandHandler.GetDocumentInfo);
                
                // 清空文檔
                RegisterCommand("clear_document", DocumentCommandHandler.ClearDocument);
                
                // 保存文檔
                RegisterCommand("save_document", DocumentCommandHandler.SaveDocument);
                
                // 加載文檔
                RegisterCommand("load_document", DocumentCommandHandler.LoadDocument);
                
                // 獲取群組中的組件 - 添加详细日志
                RhinoApp.WriteLine("GH_MCP: About to register get_components_in_group command...");
                RegisterCommand("get_components_in_group", DocumentCommandHandler.GetComponentsInGroup);
                RhinoApp.WriteLine("GH_MCP: Successfully registered get_components_in_group command.");
                
                RhinoApp.WriteLine("GH_MCP: Document commands registration completed.");
            }
            catch (Exception ex)
            {
                RhinoApp.WriteLine($"GH_MCP: ERROR during document commands registration: {ex.Message}");
                RhinoApp.WriteLine($"GH_MCP: Stack trace: {ex.StackTrace}");
            }
        }

        /// <summary>
        /// 註冊意圖命令
        /// </summary>
        private static void RegisterIntentCommands()
        {
            // 創建模式
            RegisterCommand("create_pattern", IntentCommandHandler.CreatePattern);
            
            // 獲取可用模式
            RegisterCommand("get_available_patterns", IntentCommandHandler.GetAvailablePatterns);
            
            RhinoApp.WriteLine("GH_MCP: Intent commands registered.");
        }

        /// <summary>
        /// 註冊命令處理器
        /// </summary>
        /// <param name="commandType">命令類型</param>
        /// <param name="handler">處理函數</param>
        public static void RegisterCommand(string commandType, Func<Command, object> handler)
        {
            if (string.IsNullOrEmpty(commandType))
                throw new ArgumentNullException(nameof(commandType));
                
            if (handler == null)
                throw new ArgumentNullException(nameof(handler));
                
            CommandHandlers[commandType] = handler;
            RhinoApp.WriteLine($"GH_MCP: Registered command handler for '{commandType}'");
        }

        /// <summary>
        /// 執行命令
        /// </summary>
        /// <param name="command">要執行的命令</param>
        /// <returns>命令執行結果</returns>
        public static Response ExecuteCommand(Command command)
        {
            if (command == null)
            {
                return Response.CreateError("Command is null");
            }
            
            if (string.IsNullOrEmpty(command.Type))
            {
                return Response.CreateError("Command type is null or empty");
            }
            
            // 添加调试信息
            RhinoApp.WriteLine($"GH_MCP: Executing command '{command.Type}'");
            RhinoApp.WriteLine($"GH_MCP: Registry contains {CommandHandlers.Count} commands:");
            foreach (var registeredCommand in CommandHandlers.Keys)
            {
                RhinoApp.WriteLine($"  - '{registeredCommand}' (exact match: {registeredCommand == command.Type})");
            }
            
            if (CommandHandlers.TryGetValue(command.Type, out var handler))
            {
                try
                {
                    RhinoApp.WriteLine($"GH_MCP: Found handler for '{command.Type}', executing...");
                    var result = handler(command);
                    RhinoApp.WriteLine($"GH_MCP: Command '{command.Type}' executed successfully.");
                    return Response.Ok(result);
                }
                catch (Exception ex)
                {
                    RhinoApp.WriteLine($"GH_MCP: Error executing command '{command.Type}': {ex.Message}");
                    return Response.CreateError($"Error executing command '{command.Type}': {ex.Message}");
                }
            }
            
            RhinoApp.WriteLine($"GH_MCP: No handler found for command '{command.Type}'");
            return Response.CreateError($"No handler registered for command type '{command.Type}'");
        }

        /// <summary>
        /// 獲取所有已註冊的命令類型
        /// </summary>
        /// <returns>命令類型列表</returns>
        public static List<string> GetRegisteredCommandTypes()
        {
            return CommandHandlers.Keys.ToList();
        }
    }
}
