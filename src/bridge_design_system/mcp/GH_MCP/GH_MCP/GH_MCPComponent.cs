using System;
using System.Collections.Generic;
using System.Drawing;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using GH_MCP.Commands;
using GrasshopperMCP.Models;
using Grasshopper.Kernel;
using Rhino;
using Newtonsoft.Json;
using System.IO;

namespace GrasshopperMCP
{
    /// <summary>
    /// Grasshopper MCP 組件，用於與 Python 伺服器通信
    /// </summary>
    public class GrasshopperMCPComponent : GH_Component
    {
        private static TcpListener listener;
        private static bool isRunning = false;
        private static int grasshopperPort = 8081;
        private static string grasshopperAddress = "0.0.0.0";
        
        /// <summary>
        /// 初始化 GrasshopperMCPComponent 類的新實例
        /// </summary>
        public GrasshopperMCPComponent()
            : base("Grasshopper MCP", "MCP", "Machine Control Protocol for Grasshopper", "Params", "Util")
        {
        }
        
        /// <summary>
        /// 註冊輸入參數
        /// </summary>
        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddBooleanParameter("Enabled", "E", "Enable or disable the MCP server", GH_ParamAccess.item, false);
            pManager.AddIntegerParameter("Port", "P", "Port to listen on", GH_ParamAccess.item, grasshopperPort);
            pManager.AddTextParameter("Address", "A", "Bind address (0.0.0.0 for all interfaces, 127.0.0.1 for localhost only)", GH_ParamAccess.item, "0.0.0.0");
        }
        
        /// <summary>
        /// 註冊輸出參數
        /// </summary>
        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Status", "S", "Server status", GH_ParamAccess.item);
            pManager.AddTextParameter("LastCommand", "C", "Last received command", GH_ParamAccess.item);
        }
        
        /// <summary>
        /// 解決組件
        /// </summary>
        protected override void SolveInstance(IGH_DataAccess DA)
        {
            bool enabled = false;
            int port = grasshopperPort;
            string address = "0.0.0.0";
            
            // 獲取輸入參數
            if (!DA.GetData(0, ref enabled)) return;
            if (!DA.GetData(1, ref port)) return;
            if (!DA.GetData(2, ref address)) return;
            
            // 更新端口和地址
            grasshopperPort = port;
            grasshopperAddress = address;
            
            // 根據啟用狀態啟動或停止伺服器
            if (enabled && !isRunning)
            {
                Start();
                if (isRunning)
                {
                    DA.SetData(0, $"Running on {grasshopperAddress}:{grasshopperPort}");
                }
                else
                {
                    DA.SetData(0, $"Failed to start - {grasshopperAddress}:{grasshopperPort} may be in use");
                }
            }
            else if (!enabled && isRunning)
            {
                Stop();
                DA.SetData(0, "Stopped");
            }
            else if (enabled && isRunning)
            {
                DA.SetData(0, $"Running on {grasshopperAddress}:{grasshopperPort}");
            }
            else
            {
                DA.SetData(0, "Stopped");
            }
            
            // 設置最後接收的命令
            DA.SetData(1, LastCommand);
        }
        
        /// <summary>
        /// 組件 GUID
        /// </summary>
        public override Guid ComponentGuid => new Guid("12345678-1234-1234-1234-123456789012");
        
        /// <summary>
        /// 暴露圖標
        /// </summary>
        protected override Bitmap Icon => null;
        
        /// <summary>
        /// 最後接收的命令
        /// </summary>
        public static string LastCommand { get; private set; } = "None";
        
        /// <summary>
        /// 啟動 MCP 伺服器
        /// </summary>
        public static void Start()
        {
            if (isRunning) return;
            
            try
            {
                // 停止任何現有的監聽器
                if (listener != null)
                {
                    try
                    {
                        listener.Stop();
                        listener = null;
                    }
                    catch { }
                }
                
                // 初始化命令註冊表
                GrasshopperCommandRegistry.Initialize();
                
                // 解析綁定地址
                IPAddress bindIPAddress;
                if (!IPAddress.TryParse(grasshopperAddress, out bindIPAddress))
                {
                    RhinoApp.WriteLine($"Invalid bind address '{grasshopperAddress}', using 0.0.0.0 (all interfaces)");
                    bindIPAddress = IPAddress.Any;
                }
                
                // 啟動 TCP 監聽器 - User configurable bind address
                isRunning = true;
                listener = new TcpListener(bindIPAddress, grasshopperPort);
                listener.Start();
                
                string bindDescription = GetBindDescription(bindIPAddress);
                RhinoApp.WriteLine($"GrasshopperMCPBridge started on {grasshopperAddress}:{grasshopperPort} ({bindDescription})");
                
                // 開始接收連接
                Task.Run(ListenerLoop);
            }
            catch (SocketException ex)
            {
                isRunning = false;
                if (ex.SocketErrorCode == SocketError.AddressAlreadyInUse)
                {
                    RhinoApp.WriteLine($"Address {grasshopperAddress}:{grasshopperPort} is already in use. Please use a different address/port or close the other application.");
                }
                else
                {
                    RhinoApp.WriteLine($"Failed to start TCP listener on {grasshopperAddress}:{grasshopperPort}: {ex.Message}");
                }
            }
        }
        
        /// <summary>
        /// 停止 MCP 伺服器
        /// </summary>
        public static void Stop()
        {
            if (!isRunning) return;
            
            isRunning = false;
            listener.Stop();
            RhinoApp.WriteLine("GrasshopperMCPBridge stopped.");
        }
        
        /// <summary>
        /// 獲取綁定地址描述
        /// </summary>
        private static string GetBindDescription(IPAddress address)
        {
            if (address.Equals(IPAddress.Any))
                return "all interfaces - accessible from WSL, localhost, and network";
            else if (address.Equals(IPAddress.Loopback))
                return "localhost only - not accessible from WSL";
            else
                return $"specific interface {address}";
        }
        
        /// <summary>
        /// 監聽循環，處理傳入的連接
        /// </summary>
        private static async Task ListenerLoop()
        {
            try
            {
                while (isRunning)
                {
                    // 等待客戶端連接
                    var client = await listener.AcceptTcpClientAsync();
                    RhinoApp.WriteLine("GrasshopperMCPBridge: Client connected.");
                    
                    // 處理客戶端連接
                    _ = Task.Run(() => HandleClient(client));
                }
            }
            catch (Exception ex)
            {
                if (isRunning)
                {
                    RhinoApp.WriteLine($"GrasshopperMCPBridge error: {ex.Message}");
                    isRunning = false;
                }
            }
        }
        
        /// <summary>
        /// 處理客戶端連接
        /// </summary>
        /// <param name="client">TCP 客戶端</param>
        private static async Task HandleClient(TcpClient client)
        {
            using (client)
            using (var stream = client.GetStream())
            using (var reader = new StreamReader(stream, Encoding.UTF8))
            using (var writer = new StreamWriter(stream, Encoding.UTF8) { AutoFlush = true })
            {
                try
                {
                    // 讀取命令
                    string commandJson = await reader.ReadLineAsync();
                    if (string.IsNullOrEmpty(commandJson))
                    {
                        return;
                    }
                    
                    // 更新最後接收的命令
                    LastCommand = commandJson;
                    
                    // 解析命令
                    Command command = JsonConvert.DeserializeObject<Command>(commandJson);
                    RhinoApp.WriteLine($"GrasshopperMCPBridge: Received command: {command.Type}");
                    
                    // 執行命令
                    Response response = GrasshopperCommandRegistry.ExecuteCommand(command);
                    
                    // 發送響應
                    string responseJson = JsonConvert.SerializeObject(response);
                    await writer.WriteLineAsync(responseJson);
                    
                    RhinoApp.WriteLine($"GrasshopperMCPBridge: Command {command.Type} executed with result: {(response.Success ? "Success" : "Error")}");
                }
                catch (Exception ex)
                {
                    RhinoApp.WriteLine($"GrasshopperMCPBridge error handling client: {ex.Message}");
                    
                    // 發送錯誤響應
                    Response errorResponse = Response.CreateError($"Server error: {ex.Message}");
                    string errorResponseJson = JsonConvert.SerializeObject(errorResponse);
                    await writer.WriteLineAsync(errorResponseJson);
                }
            }
        }
    }
}
