# Agent Visualization System - Design Plan

## Overview

A hybrid visualization system for the AR-assisted bridge design multi-agent system, combining an enhanced CLI interface with a real-time React-based agent interaction visualizer. This provides both efficient development workflow and intuitive understanding of agent coordination.

## Architecture Vision

```
┌─ Enhanced CLI (Primary Interface) ─┐    ┌─ React Agent Visualizer ─┐
│ Bridge Designer Chat               │    │  2D Agent Network Observer │
│ ├─ Rich text formatting           │    │  ├─ Agent node diagram     │
│ ├─ Agent status indicators        │    │  ├─ Communication flows    │
│ ├─ Real-time progress updates     │◄──►│  ├─ Status animations      │
│ ├─ Design state display           │    │  ├─ Message timeline       │
│ └─ Command shortcuts              │    │  └─ Performance metrics    │
└───────────────────────────────────┘    └───────────────────────────┘
           │                                         ▲
           │          WebSocket/HTTP API             │
           └─────────────────────────────────────────┘
```

## Design Goals

### Primary Objectives
- **Enhanced Development Experience**: Rich CLI for efficient bridge design workflow
- **Visual Agent Understanding**: Clear 2D visualization of multi-agent coordination
- **Observation & Debugging**: Real-time monitoring of agent interactions
- **Low Latency**: Sub-100ms updates for responsive agent state changes

### Secondary Objectives  
- **Educational Value**: Clear demonstration of multi-agent system behavior
- **Debugging Support**: Visual debugging of agent communication patterns
- **Simple Implementation**: 2D focus for rapid development and deployment
- **Performance Monitoring**: Visual agent performance metrics

## Technical Specifications

### Enhanced CLI System

#### Core Features
```python
# Enhanced CLI Components
class EnhancedCLI:
    - Rich console formatting (colors, panels, progress bars)
    - Real-time agent status display
    - Design state visualization (ASCII art bridge representations)
    - Command shortcuts and autocomplete
    - Live agent activity indicators
    - Conversation history with search
    - Export capabilities (logs, design states)
```

#### Status Broadcasting System
```python
# Agent Status Broadcaster
class AgentStatusBroadcaster:
    def broadcast_agent_status(self, agent_name, status, message, metadata):
        """
        Broadcast agent state changes to visualization system
        
        Args:
            agent_name: 'triage' | 'geometry' | 'material' | 'structural'
            status: 'idle' | 'thinking' | 'active' | 'delegating' | 'error'
            message: Human-readable status message
            metadata: Additional context (tools used, time elapsed, etc.)
        """
```

### React Agent Visualizer (2D Observer)

#### Agent Representation Design
```typescript
interface AgentVisual {
  // Visual Properties
  shape: 'circle' | 'square' | 'triangle' | 'hexagon';
  color: string;
  size: number; // radius in pixels
  position: { x: number; y: number };
  
  // State Properties
  status: 'idle' | 'thinking' | 'active' | 'delegating' | 'error';
  opacity: number;
  borderStyle: 'none' | 'solid' | 'dashed' | 'pulsing';
  glowEffect: boolean;
  
  // Animation Properties
  pulseSpeed: number;
  rippleEffect: boolean;
}
```

#### Agent Design Language (2D Layout)
```
Agent Visual Identity:
├─ Triage Agent (Central Coordinator)
│  ├─ Shape: Hexagon (coordination hub)
│  ├─ Color: Indigo (#4F46E5)
│  ├─ Size: 60px radius
│  └─ Position: Center (400, 300)
│
├─ Geometry Agent (3D Operations)
│  ├─ Shape: Triangle (geometric operations)
│  ├─ Color: Green (#059669)
│  ├─ Size: 40px radius
│  └─ Position: Top-right (600, 150)
│
├─ Material Agent (Resource Management)
│  ├─ Shape: Square (structured data)
│  ├─ Color: Red (#DC2626)
│  ├─ Size: 40px radius
│  └─ Position: Bottom-left (200, 450)
│
└─ Structural Agent (Engineering Analysis)
   ├─ Shape: Circle (analysis completeness)
   ├─ Color: Brown (#7C2D12)
   ├─ Size: 40px radius
   └─ Position: Bottom-right (600, 450)
```

#### Communication Flow Visualization (2D)
```typescript
interface CommunicationFlow {
  id: string;
  from: AgentType;
  to: AgentType;
  message: string;
  timestamp: number;
  
  // 2D Visual properties
  animation: {
    type: 'line-pulse' | 'moving-dot' | 'arrow-flow';
    duration: number;
    color: string;
    strokeWidth: number;
    dashPattern?: number[];
  };
  
  // Line geometry
  path: {
    startX: number;
    startY: number;
    endX: number;
    endY: number;
    curve?: 'straight' | 'arc' | 'bezier';
  };
  
  // Metadata
  toolUsed?: string;
  responseTime?: number;
  success: boolean;
}
```

## Implementation Phases

### Phase 0: MCP Integration with Official Specification (Current)
**Objective**: Implement official MCP streamable-http transport for Grasshopper integration

#### Key Findings from Smolagents Research
Based on official smolagents documentation analysis:

**Supported MCP Transports:**
1. **stdio** - `StdioServerParameters` (subprocess-based)
2. **SSE (HTTP+SSE)** - Legacy HTTP transport ⚠️ **DEPRECATED**  
3. **streamable-http** - **RECOMMENDED** modern HTTP transport ✅

**Official Integration Pattern:**
```python
# Recommended approach for our Grasshopper bridge
with MCPClient({
    "url": "http://localhost:8000/mcp", 
    "transport": "streamable-http"
}) as tools:
    agent = CodeAgent(tools=tools, model=model)
```

#### Updated MCP Strategy
- ✅ **Use streamable-http transport** - Official recommended approach
- ✅ **Leverage smolagents MCPClient directly** - No custom adapters needed
- ✅ **Create official MCP server** with streamable-http endpoint
- ✅ **Simpler architecture** - Less custom code, more standard implementation

#### Deliverables
- [ ] Official MCP server with streamable-http transport
- [ ] Update GeometryAgent to use smolagents MCPClient directly
- [ ] Remove custom HTTP adapter implementations
- [ ] Create C# Grasshopper HTTP client for streamable-http endpoint
- [ ] Integration testing with official MCP specification

### Phase 1: Enhanced CLI Foundation (Week 1)
**Objective**: Create rich CLI experience with status broadcasting

#### Deliverables
- [ ] Enhanced CLI with Rich library integration
- [ ] Agent status broadcasting system
- [ ] Real-time design state display
- [ ] WebSocket server for visualization connection
- [ ] Command shortcuts and improved UX

#### Technical Tasks
```python
# 1. Official MCP Implementation (Phase 0)
src/bridge_design_system/mcp/
├── streamable_http_server.py    # Official MCP streamable-http server
├── smolagents_integration.py   # Direct MCPClient usage
└── grasshopper_mcp/
    ├── streamable_http_bridge.py  # Official MCP bridge
    └── GH_MCP/                     # C# HTTP client update

# 2. Enhanced CLI Implementation (Phase 1)
src/bridge_design_system/cli/
├── enhanced_interface.py      # Rich-based CLI interface
├── status_broadcaster.py     # WebSocket status broadcasting
├── design_visualizer.py      # ASCII/text design visualization
└── command_processor.py      # Enhanced command handling

# 3. Agent Integration
src/bridge_design_system/agents/base_agent.py
└── Add status broadcasting to all agent operations

# 4. API Layer
src/bridge_design_system/api/
├── websocket_server.py       # Real-time status API
└── rest_endpoints.py         # RESTful API for visualization
```

### Phase 2: React Agent Visualizer (Week 2)
**Objective**: Create 2D agent network observation interface

#### Deliverables
- [ ] React application with SVG/Canvas 2D rendering
- [ ] 2D agent node representations with shapes and colors
- [ ] Real-time WebSocket connection to CLI
- [ ] Basic agent state animations (pulse, glow, ripple)
- [ ] Communication flow visualization with animated lines

#### Technical Architecture
```typescript
// React App Structure
agent-visualizer/
├── src/
│   ├── components/
│   │   ├── AgentNetworkCanvas.tsx    # Main 2D canvas/SVG
│   │   ├── AgentNode.tsx             # Individual 2D agent visualization
│   │   ├── CommunicationFlow.tsx     # 2D line animations
│   │   ├── StatusPanel.tsx           # Agent status sidebar
│   │   ├── MessageTimeline.tsx       # Communication history
│   │   └── PerformanceMetrics.tsx    # Performance monitoring
│   │
│   ├── hooks/
│   │   ├── useWebSocket.ts           # WebSocket connection management
│   │   ├── useAgentStatus.ts         # Agent state management
│   │   └── use2DAnimations.ts        # 2D animation helpers
│   │
│   ├── types/
│   │   ├── Agent.ts                  # Agent type definitions
│   │   └── Communication.ts          # Communication type definitions
│   │
│   └── utils/
│       ├── 2dPositioning.ts          # 2D layout calculations
│       └── svgHelpers.ts             # SVG manipulation utilities
│
└── package.json
    ├── Dependencies: React, framer-motion (for animations)
    ├── Dev Dependencies: TypeScript, Vite
    └── Build: Static files for easy deployment
```

### Phase 3: Advanced Interactions (Week 3)
**Objective**: Enhanced visualization features and interactivity

#### Deliverables
- [ ] Interactive agent details on hover/click
- [ ] Communication history timeline
- [ ] Performance metrics visualization
- [ ] Design state integration
- [ ] Export capabilities (screenshots, logs)

#### Advanced Features
```typescript
// Advanced Visualization Features
interface AdvancedFeatures {
  // Interactive Elements
  agentInspection: {
    onHover: () => void;          // Show agent details
    onClick: () => void;          // Open agent control panel
    contextMenu: MenuItem[];      // Right-click options
  };
  
  // Timeline Visualization
  communicationHistory: {
    timelineView: boolean;        // Show message history
    playbackControls: boolean;    // Replay interactions
    filterOptions: FilterType[];  // Filter by agent/type
  };
  
  // Performance Monitoring
  metrics: {
    responseTime: number[];       // Agent response times
    messageCount: number;         // Messages per agent
    errorRate: number;           // Error percentage
    utilizationRate: number;     // Agent busy percentage
  };
  
  // Design Integration
  designState: {
    bridgeProgress: number;       // Overall progress %
    currentStep: string;          // Current design step
    geometryPreview: boolean;     // Show geometry state
    materialStatus: MaterialStock; // Material availability
  };
}
```

### Phase 4: Integration & Polish (Week 4)
**Objective**: Full integration and production readiness

#### Deliverables
- [ ] Seamless CLI + Visualizer workflow
- [ ] Performance optimization
- [ ] Error handling and recovery
- [ ] Documentation and user guide
- [ ] Deployment automation

## Visual Design Specifications

### Color Palette
```css
/* Agent Colors */
--triage-color: #4F46E5;      /* Indigo - coordination */
--geometry-color: #059669;    /* Green - creation */
--material-color: #DC2626;    /* Red - resources */
--structural-color: #7C2D12;  /* Brown - analysis */

/* Status Colors */
--idle-color: #6B7280;        /* Gray - inactive */
--thinking-color: #F59E0B;    /* Amber - processing */
--active-color: #3B82F6;      /* Blue - working */
--error-color: #EF4444;       /* Red - error state */

/* Communication Colors */
--message-flow: #8B5CF6;      /* Purple - data flow */
--success-flow: #10B981;      /* Green - success */
--error-flow: #F87171;        /* Red - error */
```

### Animation Specifications
```css
/* Agent State Animations */
.agent-idle {
  opacity: 0.4;
  transform: scale(1.0);
}

.agent-thinking {
  opacity: 0.8;
  animation: gentle-pulse 2s ease-in-out infinite;
  border: 2px solid var(--thinking-color);
}

.agent-active {
  opacity: 1.0;
  animation: active-glow 1s ease-in-out infinite alternate;
  border: 3px solid var(--active-color);
  box-shadow: 0 0 20px var(--active-color);
}

/* Communication Flow Animations */
.message-flow {
  animation: flow-particles 1.5s ease-out;
}

@keyframes flow-particles {
  0% { transform: translateX(0) scale(0); opacity: 0; }
  50% { transform: translateX(50%) scale(1); opacity: 1; }
  100% { transform: translateX(100%) scale(0); opacity: 0; }
}
```

## Performance Requirements

### Response Time Targets
- Agent status updates: < 50ms
- Visualization frame rate: 60 FPS
- WebSocket message latency: < 100ms
- UI responsiveness: < 200ms for all interactions

### Resource Constraints
- React app bundle size: < 5MB
- Memory usage: < 200MB for visualization
- CPU usage: < 10% on modern machines
- Network bandwidth: < 1KB/s for status updates

## Development Environment Setup

### Prerequisites
```bash
# Python dependencies (already in pyproject.toml)
uv pip install rich fastapi uvicorn websockets

# Node.js dependencies for 2D React app
cd agent-visualizer
npm install react @types/react framer-motion
npm install -D typescript vite @types/node
```

### Development Workflow
```bash
# Terminal 1: Enhanced CLI
cd bridge-design-system
uv venv && .venv\Scripts\activate
python -m bridge_design_system.main --interactive --visualizer

# Terminal 2: React Development Server  
cd agent-visualizer
npm run dev

# Terminal 3: WebSocket Bridge (if needed)
python -m bridge_design_system.api.websocket_server
```

## Testing Strategy

### Unit Tests
- [ ] Agent status broadcasting accuracy
- [ ] WebSocket connection stability
- [ ] React component rendering
- [ ] Animation performance

### Integration Tests
- [ ] CLI + Visualizer synchronization
- [ ] Agent delegation visualization accuracy
- [ ] Error state handling
- [ ] Performance under load

### User Experience Tests
- [ ] Intuitive agent identification
- [ ] Clear communication flow understanding
- [ ] Responsive interactions
- [ ] Error recovery

## Future Extensions

### AR Integration Readiness
- 2D to 3D coordinate system migration path  
- Component architecture designed for future 3D upgrade
- Voice command integration points
- Gesture recognition hooks

### Advanced Analytics
- Agent performance analytics dashboard
- Communication pattern analysis
- Design workflow optimization insights
- Bottleneck identification

### Collaboration Features
- Multi-user visualization
- Shared design sessions
- Remote agent monitoring
- Team coordination tools

## Success Metrics

### Functional Metrics
- [ ] All agent states visualized accurately
- [ ] Real-time updates with < 100ms latency
- [ ] Zero message loss in communication flows
- [ ] Error states clearly indicated

### User Experience Metrics
- [ ] Intuitive understanding of agent roles (user testing)
- [ ] Efficient debugging capability (developer feedback)
- [ ] Improved development workflow (time savings)
- [ ] Educational value (system comprehension)

### Technical Metrics
- [ ] Smooth 2D animations (60 FPS)
- [ ] < 2MB total bundle size (2D focus)
- [ ] < 100MB memory footprint
- [ ] 99% uptime for visualization service

## Conclusion

This agent visualization system will transform the development and understanding of the bridge design multi-agent system. By providing both enhanced CLI efficiency and intuitive visual feedback, it creates an optimal environment for AR-assisted bridge design development and future user interactions.

The modular architecture ensures that visualization can evolve independently while maintaining tight integration with the core agent system, setting the foundation for seamless AR integration in future phases.