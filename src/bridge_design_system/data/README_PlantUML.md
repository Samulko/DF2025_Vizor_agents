# Material Agent PlantUML Diagrams

This directory contains PlantUML diagrams that visualize the architecture and workflow of the Material Agent system.

## Diagrams Overview

### 1. Material Agent Architecture (`@startuml Material Agent Architecture`)
- **Purpose**: Shows the overall system architecture and component relationships
- **Key Elements**:
  - Material Agent main class
  - Tools (CalculateDistance, CalculateAngles, SaveCategorizedData)
  - Data Processing components
  - External dependencies (CodeAgent, ModelProvider, SmolAgents)
- **Use Case**: Understanding the system structure and dependencies

### 2. Material Agent Workflow (`@startuml Material Agent Workflow`)
- **Purpose**: Illustrates the step-by-step process flow
- **Key Elements**:
  - Data loading from catalog
  - Shape analysis and classification logic
  - Triangle type determination (obtuse, right, equilateral, isosceles, scalene)
  - Data saving and agent analysis
- **Use Case**: Understanding the processing logic and decision points

### 3. Material Agent Data Flow (`@startuml Material Agent Data Flow`)
- **Purpose**: Shows how data moves through the system
- **Key Elements**:
  - Input data (found_material_catalog.json)
  - Processing engine components
  - Output data (material_categories.json)
  - Analysis results and statistics
- **Use Case**: Understanding data transformation and storage

### 4. Material Agent Class Structure (`@startuml Material Agent Class Structure`)
- **Purpose**: Detailed class relationships and methods
- **Key Elements**:
  - Class hierarchies and relationships
  - Method signatures and access modifiers
  - Data structures (CatalogData, CategorizedData)
- **Use Case**: Understanding the object-oriented design

## How to View the Diagrams

### Option 1: Online PlantUML Editor
1. Go to [PlantUML Online Editor](http://www.plantuml.com/plantuml/uml/)
2. Copy the content from `material_agent_diagram.puml`
3. Paste into the editor
4. The diagram will render automatically

### Option 2: VS Code Extension
1. Install the "PlantUML" extension in VS Code
2. Open `material_agent_diagram.puml`
3. Use `Ctrl+Shift+P` and run "PlantUML: Preview Current Diagram"

### Option 3: Command Line
```bash
# Install PlantUML (requires Java)
java -jar plantuml.jar material_agent_diagram.puml

# Or using npm
npm install -g plantuml
plantuml material_agent_diagram.puml
```

## Diagram Sections Explained

### Architecture Diagram
- **Material Agent System**: Main package containing all components
- **Tools**: Mathematical calculation functions decorated with `@tool`
- **Data Processing**: Core logic for shape analysis and categorization
- **Data Storage**: Input and output data structures
- **External Dependencies**: SmolAgents framework integration

### Workflow Diagram
- **Decision Points**: Shows the logic for triangle classification
- **Processing Loop**: Iterates through all catalog objects
- **Data Persistence**: Saves results to JSON file
- **Agent Analysis**: Uses LLM for detailed geometric analysis

### Data Flow Diagram
- **Input**: Raw material catalog with vertex data
- **Processing**: Mathematical analysis and shape classification
- **Output**: Categorized data with statistics
- **Results**: Shape types and analysis insights

### Class Structure Diagram
- **Public Methods**: Functions accessible to external code
- **Private Methods**: Internal helper functions
- **Data Classes**: Structures for input/output data
- **Relationships**: How classes interact and depend on each other

## Key Concepts Illustrated

1. **Tool-Based Architecture**: Functions decorated with `@tool` provide mathematical capabilities
2. **Data-Driven Processing**: Catalog data drives the analysis workflow
3. **Classification Logic**: Mathematical rules determine shape types
4. **LLM Integration**: CodeAgent provides intelligent analysis capabilities
5. **Modular Design**: Separate components for different responsibilities

## Usage in Development

These diagrams help developers understand:
- How to extend the system with new shape types
- Where to add new analysis tools
- How data flows through the system
- Which components interact with each other
- The overall architecture for maintenance and debugging 