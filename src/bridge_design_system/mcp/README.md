# Grasshopper MCP Bridge Server

A Model Context Protocol (MCP) server for Grasshopper integration.

## Features

- 40+ Grasshopper tools via MCP protocol
- Supports both core Grasshopper components and Vizor AR components
- STDIO transport for seamless integration with Claude Desktop and other MCP clients
- FastMCP framework for robust server implementation

## Installation

This package is designed to be installed as a local dependency:

```bash
uv pip install -e .
```

## Usage

Run the MCP server:

```bash
python -m grasshopper_mcp.bridge
```

Or using the entry point:

```bash
grasshopper-mcp
```

## MCP Tools

The server provides tools for:
- Adding Grasshopper components (sliders, panels, math operations)
- Connecting components
- Document management (save, load, clear)
- Component queries and manipulation
- Vizor AR components for mixed reality applications

## Integration

This server works with:
- Claude Desktop (via MCP configuration)
- smolagents framework
- Any MCP-compatible client
