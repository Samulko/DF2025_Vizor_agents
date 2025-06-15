# Current Task: Refactor Agent Architecture Using Smolagents Best Practices

## Context & Background

**Problem**: Current agent architecture violates smolagents best practices and creates unnecessary complexity:

1. **Over-abstraction**: `BaseAgent` wraps smolagents unnecessarily, contradicting minimalist philosophy
2. **Inconsistent patterns**: Mixing `CodeAgent` (TriageAgent) and `ToolCallingAgent` (GeometryAgentJSON) without proper architecture
3. **Duplicate functionality**: Each agent reimplements conversation history, memory management, and error handling
4. **Complex initialization**: Two-step initialization (init + initialize_agent) is confusing and fragile
5. **Custom error handling**: Using custom `AgentError` enum instead of smolagents' built-in exception hierarchy

**Root Cause**: Architecture doesn't follow smolagents patterns, creating 30% more LLM calls and maintenance overhead

**Solution**: Implement smolagents best practices with factory pattern, ManagedAgent coordination, and proper error handling

## 🎯 **SMOLAGENTS BEST PRACTICES TO IMPLEMENT**

### Key Patterns from Analysis:
1. **Factory Pattern**: Replace inheritance hierarchy with factory methods
2. **ManagedAgent Pattern**: Use smolagents' built-in multi-agent coordination  
3. **Memory Separation**: Centralize conversation management in orchestrator
4. **Proper Error Handling**: Use smolagents' exception hierarchy
5. **Production Patterns**: Add monitoring, logging, and security

### Expected Benefits:
- **30% fewer LLM calls** (smolagents efficiency)
- **Reduced complexity** (eliminate custom abstractions)
- **Better error handling** (use smolagents patterns)
- **Improved maintainability** (standardized patterns)
- **Production readiness** (monitoring, security)

## 📋 **IMPLEMENTATION PLAN**

### Phase 1: Replace BaseAgent with AgentFactory (HIGH PRIORITY)

**Goal**: Replace complex inheritance with factory pattern

#### 1.1 Create AgentFactory Module
- **File**: `src/bridge_design_system/agents/agent_factory.py`
- **Purpose**: Factory functions for creating specialized agents
- **Features**:
  - `create_code_agent()` - For Python-based tasks (structural, material analysis)
  - `create_tool_calling_agent()` - For MCP/JSON integration (geometry)
  - Unified configuration (model, security, monitoring)
  - Built-in error handling using smolagents exceptions

**Template**:
```python
def create_agent(agent_type="code", model_type="hf", tools=None, **kwargs):
    """Factory method for creating different agent types"""
    
    # Model selection
    if model_type == "hf":
        model = InferenceClientModel(**kwargs.get('model_kwargs', {}))
    elif model_type == "openai":
        model = LiteLLMModel(model_id="gpt-4", **kwargs.get('model_kwargs', {}))
    
    # Agent type selection
    if agent_type == "code":
        return CodeAgent(tools=tools or [], model=model, **kwargs)
    elif agent_type == "tool_calling":
        return ToolCallingAgent(tools=tools or [], model=model, **kwargs)
```

#### 1.2 Agent Configuration Template
- **File**: `src/bridge_design_system/agents/agent_templates.py`
- **Purpose**: Standardized configuration templates for different agent types
- **Features**:
  - Security settings (sandboxing, authorized imports)
  - Tool loading and validation
  - Model configuration per agent type
  - Production monitoring setup

### Phase 2: Refactor TriageAgent to ManagedAgent Pattern (HIGH PRIORITY)

**Goal**: Use smolagents' built-in multi-agent coordination

#### 2.1 Simplify TriageAgent
- Remove custom BaseAgent inheritance
- Use smolagents `ManagedAgent` pattern for coordination
- Centralize conversation history and memory management
- Implement proper error recovery using smolagents exceptions

**Template**:
```python
# Create specialized agents
geometry_agent = create_agent(
    agent_type="tool_calling",
    tools=mcp_tools + memory_tools,
    model=model,
    name="geometry",
    description="Creates 3D geometry in Rhino Grasshopper"
)

structural_agent = create_agent(
    agent_type="code", 
    tools=structural_tools,
    model=model,
    name="structural",
    description="Performs structural analysis"
)

# Create manager agent with hierarchical delegation
triage_agent = CodeAgent(
    tools=coordination_tools,
    model=model,
    managed_agents=[geometry_agent, structural_agent]
)
```

#### 2.2 Memory and State Management
- Move conversation history to TriageAgent only
- Use memory tools consistently across all agents
- Implement state separation between agents
- Add component registry integration at triage level

### Phase 3: Refactor GeometryAgent (MEDIUM PRIORITY)

**Goal**: Standardize on ToolCallingAgent, remove custom abstractions

#### 3.1 Simplify GeometryAgent  
- Remove custom wrapper classes
- Use AgentFactory to create ToolCallingAgent directly
- Integrate MCP tools using smolagents patterns
- Remove duplicate conversation/memory management

#### 3.2 Tool Integration
- Standardize MCP tool loading
- Implement proper fallback tool patterns
- Add tool health monitoring
- Use smolagents tool decoration patterns

**Tool Template**:
```python
@tool
def create_geometry(geometry_type: str, **params) -> dict:
    """Create geometry using MCP tools.
    
    Args:
        geometry_type: Type of geometry to create
        **params: Geometry parameters
    
    Returns:
        Result from geometry creation
    """
    # All imports within function for Hub sharing
    import json
    # Implementation here
    return result
```

### Phase 4: Add Production Features (LOW PRIORITY)

**Goal**: Production-ready monitoring and security

#### 4.1 Security and Sandboxing
- Configure execution environments (local/docker/e2b)
- Set up proper import restrictions
- Add input validation and sanitization
- Implement rate limiting

**Security Template**:
```python
# Production agent with E2B sandboxing
agent = CodeAgent(
    tools=validated_tools,
    model=model,
    executor_type="e2b",
    executor_kwargs={"api_key": os.environ["E2B_API_KEY"]},
    additional_authorized_imports=["requests", "pandas", "numpy.*"]
)
```

#### 4.2 Monitoring and Logging
- Add OpenTelemetry instrumentation
- Implement structured logging
- Add performance metrics
- Create agent health dashboards

**Monitoring Template**:
```python
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

SmolagentsInstrumentor().instrument()

# Agent with comprehensive monitoring
agent = CodeAgent(
    tools=tools,
    model=model,
    max_steps=10,
    stream_outputs=True  # Real-time monitoring
)
```

## ✅ **ACTION ITEMS - EXECUTE IN ORDER**

### Phase 1 Tasks:
- [ ] **Create `agent_factory.py`** - Factory methods for creating agents
- [ ] **Create `agent_templates.py`** - Standardized configuration templates  
- [ ] **Update error handling** - Switch to smolagents exception hierarchy
- [ ] **Add security configurations** - Sandboxing and import restrictions

### Phase 2 Tasks:
- [ ] **Refactor `triage_agent.py`** - Remove BaseAgent inheritance
- [ ] **Implement ManagedAgent pattern** - Use smolagents coordination
- [ ] **Centralize memory management** - Move to triage level only
- [ ] **Add proper error recovery** - Use smolagents patterns

### Phase 3 Tasks:
- [ ] **Simplify `geometry_agent_json.py`** - Remove custom wrappers
- [ ] **Standardize MCP integration** - Use factory patterns
- [ ] **Add tool health monitoring** - Connection status checks
- [ ] **Implement fallback patterns** - Graceful degradation

### Phase 4 Tasks:
- [ ] **Add OpenTelemetry instrumentation** - Production monitoring
- [ ] **Configure execution environments** - Docker/E2B sandboxing
- [ ] **Implement rate limiting** - Prevent abuse
- [ ] **Create health dashboards** - Agent performance metrics

## 🧪 **TESTING STRATEGY**

### Migration Strategy:
- Keep existing agents working during transition
- Test each phase independently  
- Gradual rollout with feature flags
- Comprehensive testing at each phase

### Test Scenarios:
1. **Factory Pattern**: Create agents using factory methods
2. **ManagedAgent**: Test hierarchical task delegation
3. **Error Handling**: Verify smolagents exception handling
4. **Security**: Test sandboxing and import restrictions
5. **Performance**: Compare efficiency vs current implementation

### Success Criteria:
- [ ] **30% fewer LLM calls** (measured via logging)
- [ ] **Reduced code complexity** (lines of code, cyclomatic complexity)
- [ ] **Better error handling** (proper exception hierarchy)
- [ ] **Production readiness** (monitoring, security)
- [ ] **Maintainable architecture** (clear separation of concerns)

## 🔧 **IMPLEMENTATION TEMPLATES**

### 1. Agent Factory Implementation
```python
# src/bridge_design_system/agents/agent_factory.py
from typing import List, Optional, Dict, Any
from smolagents import CodeAgent, ToolCallingAgent, Tool
from ..config.model_config import ModelProvider

class AgentFactory:
    """Factory for creating specialized agents following smolagents patterns."""
    
    @staticmethod
    def create_geometry_agent(tools: List[Tool], **kwargs) -> ToolCallingAgent:
        """Create ToolCallingAgent for MCP geometry operations."""
        model = ModelProvider.get_model("geometry", temperature=0.1)
        return ToolCallingAgent(
            tools=tools,
            model=model,
            max_steps=kwargs.get('max_steps', 10)
        )
    
    @staticmethod  
    def create_structural_agent(tools: List[Tool], **kwargs) -> CodeAgent:
        """Create CodeAgent for Python-based structural analysis."""
        model = ModelProvider.get_model("structural")
        return CodeAgent(
            tools=tools,
            model=model,
            max_steps=kwargs.get('max_steps', 10),
            additional_authorized_imports=["numpy", "scipy", "pandas"]
        )
```

### 2. Simplified Triage Agent
```python
# src/bridge_design_system/agents/triage_agent.py
from smolagents import CodeAgent
from .agent_factory import AgentFactory

class TriageAgent:
    """Simplified triage agent using smolagents ManagedAgent pattern."""
    
    def __init__(self):
        # Create specialized agents using factory
        self.geometry_agent = AgentFactory.create_geometry_agent(
            tools=self._load_mcp_tools() + memory_tools
        )
        
        self.structural_agent = AgentFactory.create_structural_agent(
            tools=structural_tools + memory_tools
        )
        
        # Create manager agent with delegation
        self.manager = CodeAgent(
            tools=coordination_tools,
            model=ModelProvider.get_model("triage"),
            managed_agents=[self.geometry_agent, self.structural_agent]
        )
    
    def run(self, task: str) -> Any:
        """Execute task using managed agents."""
        return self.manager.run(task)
```

### 3. Production Security Config
```python
# src/bridge_design_system/agents/agent_templates.py
from typing import Dict, Any

class ProductionConfig:
    """Production-ready agent configurations."""
    
    @staticmethod
    def get_secure_config() -> Dict[str, Any]:
        """Get security configuration for production."""
        return {
            "executor_type": "e2b",
            "executor_kwargs": {"api_key": os.environ["E2B_API_KEY"]},
            "additional_authorized_imports": [
                "json", "datetime", "pathlib", "typing", 
                "dataclasses", "enum", "math", "re"
            ],
            "max_steps": 10
        }
    
    @staticmethod
    def get_monitoring_config() -> Dict[str, Any]:
        """Get monitoring configuration."""
        return {
            "stream_outputs": True,
            "enable_logging": True,
            "log_level": "INFO"
        }
```

## 🚨 **RISK MITIGATION**

### Technical Risks:
- **Breaking existing workflows** - Keep current agents as fallback during migration
- **Performance degradation** - Benchmark each phase before deployment
- **Integration issues** - Test with existing MCP and component registry systems
- **Security vulnerabilities** - Implement proper sandboxing from day one

### Mitigation Strategies:
- **Feature flags** - Enable new architecture gradually
- **A/B testing** - Compare performance with current implementation
- **Rollback plan** - Quick revert to current architecture if needed
- **Comprehensive testing** - Unit, integration, and end-to-end tests

## 📈 **EXPECTED OUTCOMES**

### Immediate Benefits:
- **Simplified codebase** - Remove custom abstractions
- **Better error handling** - Use smolagents exception hierarchy
- **Standardized patterns** - Follow established smolagents practices

### Long-term Benefits:
- **30% efficiency improvement** - Fewer LLM calls through proper patterns
- **Production readiness** - Monitoring, security, and scalability
- **Maintainability** - Clear separation of concerns and standardized interfaces
- **Community alignment** - Follow established open-source patterns

## 🔄 **MIGRATION TIMELINE**

### Week 1: Foundation (Phase 1)
- Implement agent factory and templates
- Update error handling to use smolagents exceptions
- Add basic security configurations

### Week 2: Core Refactor (Phase 2)  
- Refactor TriageAgent to use ManagedAgent pattern
- Centralize memory and state management
- Test integration with existing systems

### Week 3: Geometry Agent (Phase 3)
- Simplify GeometryAgent using factory patterns
- Standardize MCP tool integration
- Add health monitoring and fallback patterns

### Week 4: Production Features (Phase 4)
- Add comprehensive monitoring and logging
- Configure production security (sandboxing)
- Performance testing and optimization

### Week 5: Testing & Deployment
- End-to-end testing of new architecture
- Performance comparison with current system
- Gradual rollout to production

## 📝 **SUCCESS METRICS**

### Performance Metrics:
- **LLM Call Reduction**: Target 30% fewer calls
- **Response Time**: Maintain or improve current latency  
- **Error Rate**: Reduce to <5% for standard operations
- **Memory Usage**: Optimize through proper state separation

### Code Quality Metrics:
- **Lines of Code**: Reduce through elimination of duplication
- **Cyclomatic Complexity**: Simplify through factory patterns
- **Test Coverage**: Maintain >80% coverage
- **Documentation**: Update to reflect new patterns

### Production Metrics:
- **Uptime**: 99.9% availability
- **Security**: Zero vulnerabilities in security audit
- **Monitoring**: Complete observability of agent operations
- **Scalability**: Support 10x current load