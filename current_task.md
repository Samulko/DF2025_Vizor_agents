# **Implement Triage Agent as Orchestrator and Parser Architecture**

## **CORE OBJECTIVE**

Transform the agent system to use the TriageAgent as both orchestrator AND parser, implementing proper separation of concerns where GeometryAgent generates simple text descriptions and TriageAgent translates them into structured data for SysLogicAgent.

## **🎯 ARCHITECTURAL VISION**

### **The Correct Architecture: Separation of Concerns**

1. **GeometryAgent (ToolCallingAgent)**: 
   - **Single Responsibility**: Execute MCP tools and return simple descriptive text
   - **No Complex Output**: Remove structured JSON generation requirements
   - **Plain Text Response**: "Created beam ID abc123, type I-beam, length 5.2m, center at (1,2,3)"

2. **TriageAgent (CodeAgent)**:
   - **Orchestrator Role**: Manages workflow between agents
   - **Parser Role**: Translates text → structured JSON → clean data for specialists
   - **Data Translator**: Ensures each agent receives data in its expected format

3. **SysLogicAgent (CodeAgent)**:
   - **Specialist Role**: Receives clean, structured data only
   - **Focus**: Structural validation and material tracking
   - **No Parsing**: Should never handle messy input from other agents

## **🛠️ IMPLEMENTATION PLAN**

### **Phase 1: Simplify Geometry Agent Output** ⭐ **HIGH PRIORITY**

**Files to modify**:
- `system_prompts/geometry_agent.md`

**Objective**: Remove complex JSON generation requirements and focus on tool execution + simple text descriptions.

**Key Changes**:
1. **Remove entire structured output sections** from geometry_agent.md
2. **Add simple instruction**: "Execute geometry commands using available tools. After execution, describe what you did in plain text, listing properties (ID, type, length, center point, direction) of created/modified elements."
3. **Remove JSON formatting requirements** - let GeometryAgent be a simple ToolCallingAgent

**Expected Outcome**: GeometryAgent returns natural text like "Created I-beam component_123 with length 5200mm at center point (1000, 2000, 0)"

### **Phase 2: Implement Orchestration and Parsing in TriageAgent** ⭐ **CRITICAL**

**Files to modify**:
- `src/bridge_design_system/agents/triage_agent_smolagents.py`
- `system_prompts/triage_agent.md`

**Objective**: Transform TriageAgent into a three-step orchestrator: delegate → parse → delegate.

**Key Implementation in `TriageSystemWrapper.handle_design_request()`**:

```python
def handle_design_request(self, request: str, gaze_id: Optional[str] = None) -> ResponseCompatibilityWrapper:
    try:
        # Step 1: Delegate to GeometryAgent for simple text description
        geometry_agent = self._get_geometry_agent()
        if not geometry_agent:
            raise ValueError("Geometry agent not available")
            
        geometry_text_result = geometry_agent.run(
            task=request,
            additional_args={"gazed_object_id": gaze_id} if gaze_id else None
        )

        # Step 2: TriageAgent parses text into structured JSON
        parsing_task = (
            "Parse the following text describing geometric elements. "
            "Extract all element properties and format into valid JSON "
            "following ElementData contract v1.0 with 'elements' array. "
            f"Text to parse:\n\n{geometry_text_result}"
        )
        
        # Use TriageAgent's own LLM to perform parsing
        parsed_json_result = self.manager.run(parsing_task)
        element_data = self._extract_json_from_response(parsed_json_result)

        # Step 3: Pass clean structured data to SysLogicAgent
        syslogic_agent = self._get_syslogic_agent()
        if syslogic_agent and element_data:
            syslogic_result = syslogic_agent.run(
                task="update material stock and validate structural integrity",
                additional_args={"elements": element_data}
            )
        else:
            syslogic_result = "SysLogic processing skipped - no structural elements"

        # Step 4: Combine and return comprehensive response
        final_response = {
            "geometry_outcome": geometry_text_result,
            "parsed_elements": element_data,
            "syslogic_analysis": syslogic_result,
            "workflow_status": "completed_successfully"
        }
        
        return ResponseCompatibilityWrapper(final_response, success=True)

    except Exception as e:
        return ResponseCompatibilityWrapper(
            {"error": str(e), "workflow_status": "failed"}, 
            success=False
        )
```

**Helper Methods to Implement**:

```python
def _extract_json_from_response(self, llm_response: str) -> Dict[str, Any]:
    """Extract clean JSON from LLM response text."""
    try:
        # Find JSON block in response
        json_match = re.search(r'```json\n(.*?)\n```', llm_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
            else:
                return {}
        
        return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError):
        return {}

def _get_geometry_agent(self):
    """Get geometry agent from managed agents."""
    for managed_agent in self.manager.managed_agents:
        if hasattr(managed_agent, 'name') and 'geometry' in managed_agent.name.lower():
            return managed_agent.agent if hasattr(managed_agent, 'agent') else managed_agent
    return self.manager.managed_agents[0] if self.manager.managed_agents else None

def _get_syslogic_agent(self):
    """Get syslogic agent from managed agents."""
    for managed_agent in self.manager.managed_agents:
        if hasattr(managed_agent, 'name') and 'syslogic' in managed_agent.name.lower():
            return managed_agent.agent if hasattr(managed_agent, 'agent') else managed_agent
    return self.manager.managed_agents[1] if len(self.manager.managed_agents) > 1 else None
```

### **Phase 3: Update SysLogic Agent for Clean Data Input** ⭐ **MEDIUM PRIORITY**

**Files to modify**:
- `system_prompts/SysLogic_agent.md`
- `src/bridge_design_system/agents/syslogic_agent_smolagents.py` (if needed)

**Objective**: Remove complex text parsing logic and expect clean structured data.

**Key Changes to SysLogic Prompt**:
1. **Update input expectations**: "You will receive clean, structured element data via additional_args['elements']"
2. **Remove text parsing instructions**: No more regex patterns or fallback parsing
3. **Focus on core mission**: Structural validation and material management only
4. **Simplify workflow**: Assume data is already validated and structured

**Example Updated Instructions**:
```markdown
## Input Processing
You receive structured element data through `additional_args['elements']` in this format:
```json
{
  "data_type": "element_collection",
  "elements": [
    {
      "id": "component_123",
      "type": "beam",
      "length_mm": 5200,
      "material": "steel",
      "center_point": [1000, 2000, 0]
    }
  ]
}
```

Extract element lengths directly: `[elem["length_mm"] for elem in elements["elements"]]`
No text parsing required - data is pre-validated by orchestrator.
```

### **Phase 4: Update System Prompts for New Workflow** ⭐ **MEDIUM PRIORITY**

**Files to modify**:
- `system_prompts/triage_agent.md`

**Objective**: Update TriageAgent prompt to reflect its new orchestrator-parser role.

**Key Additions to Triage Prompt**:
```markdown
## Orchestrator-Parser Role

You have a dual responsibility:
1. **Orchestrate** workflows between specialized agents
2. **Parse and translate** data between agents to ensure clean communication

### Three-Step Workflow:
1. **Delegate to GeometryAgent**: Send user request, receive descriptive text
2. **Parse Response**: Convert text to structured JSON using your LLM capabilities  
3. **Delegate to SysLogicAgent**: Send clean structured data for validation

### Parsing Guidelines:
- Extract element properties: ID, type, length, center point, direction
- Format as ElementData contract v1.0 with "elements" array
- Validate JSON structure before passing to specialists
- Handle parsing errors gracefully with fallback responses

### Data Quality Assurance:
You are responsible for ensuring specialists receive clean, structured data.
Never pass raw text from one agent to another - always parse and validate first.
```

### **Phase 5: Testing and Validation** ⭐ **HIGH PRIORITY**

**Objective**: Verify the complete orchestrator-parser workflow functions correctly.

**Test Scenarios**:
1. **Simple Geometry Creation**: "Create a 5m steel beam"
   - Verify GeometryAgent returns descriptive text
   - Verify TriageAgent parses text to JSON correctly
   - Verify SysLogicAgent receives clean structured data

2. **Complex Multi-Element Design**: "Create a truss with 3 beams and 2 columns"
   - Test multiple element parsing
   - Verify material tracking across elements
   - Confirm structural validation logic

3. **Error Handling**: Test with malformed geometry responses
   - Verify graceful parsing failures
   - Confirm fallback responses
   - Test error propagation to user

4. **Gaze Integration**: Test with gazed object IDs
   - Verify context passing to GeometryAgent
   - Confirm gaze data doesn't interfere with parsing
   - Test gaze-based modification workflows

## **📁 CURRENT SYSTEM STRENGTHS TO PRESERVE**

### **✅ Keep These Working Patterns**
1. **ManagedAgent Architecture**: Current smolagents integration is correct
2. **MCP Integration**: Persistent connections and tool wrapping work well
3. **Component Registry**: Cross-agent state management is solid
4. **Error Handling**: Comprehensive try-catch and fallback logic
5. **Memory Tools**: Native smolagents memory system integration
6. **Factory Pattern**: Agent creation and configuration approach

### **✅ Maintain These Capabilities**
1. **Gaze Integration**: Context-aware object selection
2. **Material Tracking**: Inventory management and optimization
3. **Structural Validation**: Engineering analysis and feasibility checks
4. **Monitor Integration**: Real-time status updates to LCARS interface
5. **Multi-Model Support**: Different LLMs for different agent types

## **🚀 IMPLEMENTATION PRIORITY ORDER**

### **Phase 1 (Immediate)**: Simplify Geometry Agent
- Remove complex output requirements from geometry_agent.md
- Focus on simple tool execution + descriptive text

### **Phase 2 (Critical)**: Implement Orchestrator-Parser
- Add three-step workflow to TriageSystemWrapper
- Implement parsing and data translation logic
- Add helper methods for JSON extraction and agent discovery

### **Phase 3 (Follow-up)**: Update SysLogic Agent
- Remove text parsing complexity from SysLogic prompts
- Expect clean structured data input only

### **Phase 4 (Polish)**: Update Documentation
- Revise triage_agent.md for new orchestrator-parser role
- Update system architecture documentation

### **Phase 5 (Validation)**: Comprehensive Testing
- Test complete workflow end-to-end
- Verify error handling and edge cases
- Confirm backwards compatibility

## **💡 KEY ARCHITECTURAL BENEFITS**

### **Clear Separation of Concerns**
- **GeometryAgent**: Simple tool execution, no complex formatting
- **TriageAgent**: Smart orchestration and data transformation  
- **SysLogicAgent**: Focused structural analysis, no parsing overhead

### **Improved Reliability**
- Structured data contracts eliminate parsing fragility
- TriageAgent LLM handles complex text-to-JSON transformation
- Specialists receive guaranteed clean input format

### **Enhanced Maintainability**
- Each agent has single, well-defined responsibility
- Data transformation centralized in one intelligent location
- Easier debugging and error isolation

### **Scalability for Future Agents**
- New specialists can expect clean structured input
- TriageAgent handles all inter-agent communication complexity
- Consistent data contracts across the system

This architecture transforms the system from fragile text-based communication to robust structured data exchange while preserving all existing capabilities and smolagents best practices.