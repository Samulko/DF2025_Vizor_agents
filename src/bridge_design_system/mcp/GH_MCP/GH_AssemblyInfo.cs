using System;
using System.Drawing;
using Grasshopper.Kernel;

namespace VizorAgents.GH_MCP
{
    public class MCPAssemblyInfo : GH_AssemblyInfo
    {
        public override string Name => "VizorAgents MCP Bridge";
        public override Bitmap Icon => null; // You can add an icon here
        public override string Description => "HTTP MCP Bridge for AI Agent communication with Grasshopper";
        public override Guid Id => new Guid("A1B2C3D4-E5F6-7890-ABCD-EF1234567890");
        public override string AuthorName => "VizorAgents";
        public override string AuthorContact => "contact@vizor-agents.com";
    }
}