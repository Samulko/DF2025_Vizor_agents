# Current Task: Implement Shared Component Registry [ACTIVE]

## Task Description

**Problem**: While conversation memory works for short sessions, component ID tracking is fragmented between agents. Triage agent knows "created spiral staircase" but geometry agent holds the actual component ID (`226f38c6-3044-401a-8a13-12e785e21571`). This causes reference resolution to fail in longer sessions with multiple components.

**Goal**: Implement a centralized Component Registry that both agents can access to track, store, and resolve component references across the entire session.

## Previous Task [RESOLVED]
**Problem**: Triage agent conversation context loss.  
**Solution**: Added conversation memory to both agents - WORKS for short sessions.

## Architecture Understanding: What Are CodeAgents?

**CodeAgents are execution engines** from the SmolaGents framework:
- **Purpose**: Execute LLM-generated Python code with access to tools
- **Fresh per request**: Created new for each interaction to avoid memory leaks
- **Tool access**: Get MCP tools (add_python3_script, etc.) + custom tools
- **Memory separation**: Conversation history stored in parent agents (TriageAgent, GeometryAgentSTDIO)
- **Why fresh**: Prevents tool reference corruption and async/sync conflicts

**Current Flow**:
1. User: "create spiral staircase"
2. TriageAgent → creates fresh CodeAgent → delegates to GeometryAgentSTDIO  
3. GeometryAgentSTDIO → creates fresh CodeAgent → uses MCP tools → stores component ID in its memory
4. User: "make it wider"
5. TriageAgent → knows "staircase exists" but not component ID
6. Must rely on geometry agent's memory + context clues

## Success Criteria

- [ ] Centralized component registry accessible to all agents
- [ ] Component registration when geometry is created
- [ ] Reference resolution for "it", "the staircase", "the beam"
- [ ] Registry survives agent restarts/fresh CodeAgent creation
- [ ] Scalable to 50+ components in long design sessions
- [ ] Performance impact < 100ms per interaction
- [ ] Graceful fallback to current approach if registry fails

## Relevant Files

- **Primary**: Create `src/bridge_design_system/state/component_registry.py` [NEW]
- **Integration**: `src/bridge_design_system/agents/triage_agent.py` [MODIFY]
- **Integration**: `src/bridge_design_system/agents/geometry_agent_stdio.py` [MODIFY]
- **Main entry**: `src/bridge_design_system/main.py` [MODIFY to initialize registry]
- **Tests**: `tests/test_component_registry.py` [NEW]

## Root Cause Analysis

1. **Memory Fragmentation**: Component IDs trapped in geometry agent memory
2. **Lossy Context**: Triage passes text summaries, loses structured data
3. **Reference Ambiguity**: "the beam" unclear with multiple beams
4. **No Persistence**: Fresh CodeAgents can't access previous component state
5. **Scaling Failure**: Token limits exceeded with 50+ components in conversation history

## Implementation Plan

### Phase 1: Core Component Registry [PENDING]

- [ ] **Task 1.1**: Create ComponentRegistry class
  - **Status**: PENDING
  - **Details**: Thread-safe registry with component CRUD operations
  - **Files**: `src/bridge_design_system/state/component_registry.py`
  - **Key features**: 
    - Store component metadata (id, type, name, location, created_time)
    - Recent components deque for "it" resolution
    - Type-based lookup for "the beam", "the staircase"
    - Spatial indexing for "the beam on the left"

- [ ] **Task 1.2**: Registry initialization and lifecycle
  - **Status**: PENDING
  - **Details**: Initialize registry in main.py, pass to agents
  - **Files**: `src/bridge_design_system/main.py`, agent constructors
  - **Key features**:
    - Singleton pattern for global access
    - Clean shutdown/reset capability
    - Thread-safe for concurrent access

- [ ] **Task 1.3**: Reference resolution engine
  - **Status**: PENDING
  - **Details**: Natural language to component ID mapping
  - **Files**: `component_registry.py` + helper functions
  - **Key features**:
    - "it" → most recent component
    - "the staircase" → most recent staircase-type component  
    - "the red beam" → property-based search
    - Confidence scoring for ambiguous references

### Phase 2: Agent Integration [PENDING]

- [ ] **Task 2.1**: Geometry agent registration
  - **Status**: PENDING
  - **Details**: Auto-register components when created/modified
  - **Files**: `geometry_agent_stdio.py` - hook into MCP tool responses
  - **Key features**:
    - Extract component ID from MCP responses
    - Register with type inference (spiral_staircase, beam, etc.)
    - Update registry on modifications

- [ ] **Task 2.2**: Triage agent context enhancement
  - **Status**: PENDING
  - **Details**: Use registry for reference resolution before delegation
  - **Files**: `triage_agent.py` - enhance context building
  - **Key features**:
    - Resolve user references to component IDs
    - Pass structured component context to geometry agent
    - Fallback to conversation memory if registry lookup fails

- [ ] **Task 2.3**: Geometry agent context consumption
  - **Status**: PENDING
  - **Details**: Use provided component IDs for targeted operations
  - **Files**: `geometry_agent_stdio.py` - use component context
  - **Key features**:
    - Prefer provided component IDs over memory lookup
    - Handle multiple component references
    - Graceful degradation if component not found

### Phase 3: Advanced Features [PENDING]

- [ ] **Task 3.1**: Spatial reference resolution
  - **Status**: PENDING
  - **Details**: Handle "the beam on the left", "the nearest column"
  - **Files**: `component_registry.py` - spatial indexing
  - **Key features**:
    - Store component locations/bounding boxes
    - Spatial relationship queries
    - Relative position understanding

- [ ] **Task 3.2**: Component relationships
  - **Status**: PENDING
  - **Details**: Track dependencies "the beam connected to the column"
  - **Files**: `component_registry.py` - relationship graph
  - **Key features**:
    - Parent/child relationships
    - Connection tracking
    - Cascading modifications

- [ ] **Task 3.3**: Registry persistence
  - **Status**: PENDING
  - **Details**: Save/load registry for session recovery
  - **Files**: `component_registry.py` - serialization
  - **Key features**:
    - JSON serialization of registry state
    - Session recovery after crashes
    - Export for external analysis

### Phase 4: Testing & Validation [PENDING]

- [ ] **Task 4.1**: Unit tests for registry
  - **Status**: PENDING
  - **Details**: Test core registry operations
  - **Files**: `tests/test_component_registry.py`

- [ ] **Task 4.2**: Integration tests
  - **Status**: PENDING
  - **Details**: Test full workflow with registry
  - **Files**: `tests/test_registry_integration.py`

- [ ] **Task 4.3**: Performance benchmarks
  - **Status**: PENDING
  - **Details**: Measure impact on interaction latency
  - **Files**: `tests/test_registry_performance.py`

- [ ] **Task 4.4**: Long session simulation
  - **Status**: PENDING
  - **Details**: Test with 50+ components over 200+ interactions
  - **Files**: Manual testing script

## Progress Tracking

- **Tasks Completed**: 0/14
- **Phase 1 Progress**: 0/3 tasks [PENDING] (core registry)
- **Phase 2 Progress**: 0/3 tasks [PENDING] (agent integration)  
- **Phase 3 Progress**: 0/3 tasks [PENDING] (advanced features)
- **Phase 4 Progress**: 0/5 tasks [PENDING] (testing)
- **Overall Progress**: 0% [NOT STARTED]

## Constraints

- **Backward Compatibility**: Must not break existing conversation memory system
- **Performance**: Registry lookup < 10ms, registration < 50ms
- **Memory Efficiency**: Registry size < 100MB for 1000 components
- **Thread Safety**: Multiple agents accessing registry concurrently
- **Graceful Degradation**: System works if registry fails

## Technical Design

### ComponentRegistry Class Structure
```python
class ComponentRegistry:
    def __init__(self):
        self.components: Dict[str, ComponentInfo] = {}
        self.recent_components: deque = deque(maxlen=20)
        self.type_index: Dict[str, List[str]] = {}
        self.spatial_index: SpatialIndex = SpatialIndex()
        self._lock = threading.Lock()
    
    def register_component(self, component_id: str, metadata: ComponentInfo)
    def get_component(self, component_id: str) -> ComponentInfo
    def resolve_reference(self, user_input: str) -> List[str]
    def find_by_type(self, component_type: str) -> List[str]
    def find_recent(self, limit: int = 5) -> List[str]
```

### Integration Points
1. **Geometry Agent**: Hook into MCP tool responses to auto-register
2. **Triage Agent**: Use registry in `_build_conversation_context_for_geometry()`
3. **Main Entry**: Initialize shared registry instance
4. **CLI**: Optional registry status commands

---

## Task Status

**Last Updated**: 2025-06-13 15:30 UTC  
**Status**: 🚧 ACTIVE - PLANNING COMPLETE  
**Issue**: Component ID fragmentation across agents in longer sessions  
**Solution**: Centralized Component Registry with natural language reference resolution

**Next Steps**: Start Phase 1 implementation with ComponentRegistry class