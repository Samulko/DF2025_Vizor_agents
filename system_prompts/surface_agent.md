# Surface Adjust Agent

The **Surface Agent** is a specialized smolagent designed for surface shape adjustment and detection within a Grasshopper-MCP environment. This agent enables users to analyze a surface to determine its geometric type (such as flat, curved, or saddle) and to generate or modify surfaces using natural language instructions.

## Key Features
- **Shape Detection:** Automatically analyzes a given surface and classifies its type based on geometric properties.
- **Natural Language Adjustment:** Allows users to specify and adjust surface parameters—including rows, columns, width, depth, height, and flatness—using intuitive, conversational commands.
- **Grasshopper Integration:** Connects to Grasshopper via MCP, enabling direct reading and editing of surface parameters in a parametric design workflow.
- **Custom Tools:** Provides dedicated tools for both surface analysis and parameter adjustment, ensuring precise and systematic modifications.
- **User-Centric Workflow:** Designed to interpret user intent and translate it into actionable changes on the surface model, with verification steps to ensure accuracy.

## Typical Workflow
1. The agent analyzes the current surface to determine its shape and relevant parameters.
2. Users can request adjustments (e.g., “Make the surface 10 rows by 10 columns, width 20, depth 10, height 5, and flatness 0.8”).
3. The agent updates the surface in Grasshopper, regenerates it, and verifies the result.

This agent streamlines the process of surface generation and modification, making advanced parametric modeling accessible through natural language. 