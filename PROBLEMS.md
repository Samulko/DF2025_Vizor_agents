# PROBLEMS.md - Context Continuity for Claude

> **Purpose**: This file provides context for Claude when sessions reset, tracking ongoing problems, solutions in progress, and current system state.

---

## 🎯 **Current Main Problem: JSON Agent Context Explosion**

### **Critical Issue: Exponential Context Growth** 🚨
The JSON Agent architecture **successfully fixed MCP integration** but introduced a **catastrophic context management problem** that makes it unsuitable for multi-turn conversations.

**Evidence from Production Run:**
- **Start**: ~10,000 tokens
- **End**: ~46,000 tokens (4.6x growth in just 4 steps!)
- **Timeout**: 76+ seconds due to massive context size
- **API Cost**: $0.50+ per request with exponential scaling

### **Root Causes of Context Explosion:**

1. **System Prompt Duplication**: 
   - ~2,000 token system prompt embedded in EVERY request
   - ToolCallingAgent doesn't accept `system_prompt` parameter
   - "Fix" creates exponential token growth

2. **Recursive Context Building**:
   ```
   CONVERSATION CONTEXT:
   Previous task 1: CONVERSATION CONTEXT:
   Previous task 1: Human: hey can you please...
   ```
   - Context builds on itself recursively
   - Each interaction includes previous context
   - Creates exponential growth pattern

3. **AgentResponse Serialization**:
   - Conversation history stores full `AgentResponse` objects
   - Complete message content makes each entry huge
   - Memory accumulates faster than conversation

4. **Double-Layer Context**:
   - Triage agent builds conversation context
   - Geometry agent builds its own context on top
   - Result: nested context explosion

### **Performance Impact:**
- **Scalability**: 5-10 iterations = 200K+ tokens (system failure)
- **Cost**: Exponential API cost scaling
- **Latency**: Timeouts and degraded performance
- **UX**: Unusable for real bridge design sessions

### **Functional vs Context Comparison**

#### ✅ **JSON Agent Functional Success**:
- **Zero JSON parsing errors**: Native tool calling eliminates CodeAgent confusion
- **Perfect MCP integration**: All 6 tools working flawlessly via MCPAdapt
- **Clean execution**: Component creation, editing, memory storage all working
- **Correct architecture**: Follows GeometryAgentSTDIO pattern exactly

#### ❌ **JSON Agent Context Failure**:
- **Exponential token growth**: 10K → 46K tokens in 4 steps
- **System prompt duplication**: 2K tokens repeated in every request
- **Recursive context**: Each interaction embeds previous conversations
- **Double context layers**: Triage + Geometry context building

### **Required Solutions**: Context Management Overhaul

#### **Immediate Fixes (Critical Priority)**:
1. **System Prompt Optimization**:
   - Remove system prompt embedding from conversation context
   - Use model-level system prompt or single-shot context inclusion
   - Target: Eliminate 2K token duplication per request

2. **Context Truncation Strategy**:
   - Limit conversation history to last 2-3 relevant interactions
   - Implement intelligent context selection (not recursive inclusion)
   - Target: Maximum 5K token context window

3. **Response Summarization**:
   - Store conversation summaries, not full AgentResponse objects
   - Extract only essential information (component IDs, key decisions)
   - Target: <200 tokens per historical interaction

#### **Architecture Changes (Medium Priority)**:
1. **Memory-First Architecture**:
   - Use memory tools as primary persistence mechanism
   - Conversation context only for immediate task context
   - Eliminate recursive context building

2. **Hierarchical Context Management**:
   - Short-term: Current task + last interaction only
   - Medium-term: Component registry for cross-task persistence
   - Long-term: Memory tools for project-level context

3. **Context Window Management**:
   - Sliding window with intelligent relevance selection
   - Dynamic context pruning based on task type
   - Emergency context truncation when approaching limits

---

## 📋 **Current Implementation Status**

### **Phase 1: JSON Agent MCP Integration** ✅
- [x] Fixed JSON parsing errors with ToolCallingAgent
- [x] Implemented MCPAdapt pattern for reliable MCP connection
- [x] Fixed memory recall metadata pollution in memory_tools.py
- [x] Confirmed functional success: geometry creation, editing, memory storage
- [x] Verified architecture follows GeometryAgentSTDIO pattern

### **Phase 2: Context Management Crisis** 🚨
- [x] **Identified critical context explosion issue**: 10K → 46K tokens in 4 steps
- [x] **Root cause analysis complete**: System prompt duplication + recursive context
- [x] **Performance impact documented**: Timeouts, exponential costs, UX failure
- [ ] **URGENT: Implement context truncation strategy**
- [ ] **URGENT: Fix system prompt embedding approach**
- [ ] **URGENT: Implement response summarization**

### **Phase 3: Architecture Fixes** 📋
- [ ] Implement memory-first persistence strategy
- [ ] Design hierarchical context management
- [ ] Add intelligent context window management
- [ ] Create context size monitoring and alerting
- [ ] Implement emergency context truncation

---

## 🔧 **System Architecture Overview**

### **Current Working Components** ✅
- **Triage Agent**: Working, coordinates between agents
- **Multi-Agent System**: 4 agents (triage, geometry, material, structural) 
- **Model Configuration**: Gemini 2.5 Flash working for all agents
- **TCP Bridge**: C# component working (`GH_MCPComponent.cs`)
- **MCP Tools**: 49 tools available but only 6 currently enabled in bridge.py

### **MCP Integration Stack**:
```
smolagents → STDIO MCP Server → TCP Client → TCP Bridge → Grasshopper
          (grasshopper_mcp.bridge)  (communication.py)  (GH_MCPComponent.cs)
           6 enabled tools         JSON over TCP       C# TCP server
```

### **File Structure**:
- **Bridge**: `/src/bridge_design_system/mcp/grasshopper_mcp/bridge.py` (6/49 tools enabled)
- **JSON Geometry Agent**: `/src/bridge_design_system/agents/geometry_agent_json.py` (✅ working but context issues)
- **STDIO Geometry Agent**: `/src/bridge_design_system/agents/geometry_agent_stdio.py` (reference pattern)
- **Triage Agent**: `/src/bridge_design_system/agents/triage_agent.py` (✅ using JSON agent)

---

## 🚨 **Known Issues & Workarounds**

### **Issue 1: Context Explosion (CRITICAL)** 🚨
- **Problem**: JSON Agent context grows exponentially (10K → 46K tokens in 4 steps)
- **Root Cause**: System prompt duplication + recursive context building
- **Impact**: System unusable for multi-turn conversations, timeouts, cost explosion
- **Status**: **URGENT** - Blocks production deployment
- **Workaround**: Manually reset conversation every 2-3 interactions
- **Solution**: Implement context truncation and system prompt optimization

### **Issue 2: System Prompt Integration** 🔄
- **Problem**: ToolCallingAgent doesn't accept system_prompt parameter
- **Current**: Embedding 2K token system prompt in every request context
- **Impact**: Major contributor to context explosion
- **Status**: Contributing to Issue 1
- **Solution**: Find alternative approach (model config, single inclusion, etc.)

### **Issue 3: AgentResponse Serialization** ⚠️
- **Problem**: Full AgentResponse objects stored in conversation history
- **Impact**: Each interaction grows context by 1K+ tokens
- **Status**: Contributing to Issue 1
- **Solution**: Store summaries instead of full responses

### **Issue 4: Limited MCP Tools** ✅
- **Problem**: Only 6/49 MCP tools currently enabled in bridge.py
- **Status**: Working as intended for current scope
- **Tools Available**: `add_python3_script`, `get_python3_script`, `edit_python3_script`, `get_python3_script_errors`, `get_component_info_enhanced`, `get_all_components_enhanced`
- **Solution**: Re-enable tools as needed for geometry operations

---

## 🧪 **Testing Status**

### **Working Tests** ✅
- `test_simple_working_solution.py`: Proves MCP integration works
- System startup test: All 4 agents initialize correctly
- Basic task execution: Triage agent coordinates successfully

### **Tests Needed** 📝
- MCPClient lifecycle management
- Persistent connection across multiple tasks
- Auto-reconnection on connection failure
- Fallback to dummy tools when MCP unavailable
- Integration test with full geometry workflow

---

## 📈 **Performance Metrics**

### **Current Performance**:
- **Agent Initialization**: ~3-4 seconds (all 4 agents)
- **First Task Execution**: ~2-3 seconds (clean JSON execution)
- **Context Growth**: 10K → 46K tokens in 4 steps (4.6x exponential growth)
- **Timeout Threshold**: ~76 seconds when context becomes too large
- **API Cost**: $0.50+ per request when context explodes

### **Target Performance** (Post-Context-Fix):
- **Context Size**: Maximum 5K tokens (95% reduction)
- **Task Execution**: Consistent 2-5 seconds regardless of conversation length
- **API Cost**: <$0.05 per request (90% cost reduction)
- **Scalability**: Support 20+ turn conversations without degradation

---

## 🎯 **Next Actions for New Claude Session**

### **URGENT Priority (Context Crisis)**:
1. **Fix System Prompt Embedding**: Remove from `_build_conversation_context_with_system_prompt()`
2. **Implement Context Truncation**: Limit conversation history to last 2 interactions
3. **Fix Recursive Context**: Prevent context-in-context building
4. **Add Context Size Monitoring**: Track token usage and warn before explosion

### **High Priority (Architecture)**:
1. **Implement Response Summarization**: Store <200 token summaries instead of full responses
2. **Memory-First Persistence**: Use memory tools as primary state management
3. **Context Window Management**: Dynamic pruning based on relevance
4. **Emergency Context Reset**: Auto-reset when approaching token limits

### **Testing Priority**:
1. **Context Size Tests**: Verify 5K token limit maintained across 10+ interactions
2. **Performance Tests**: Confirm consistent 2-5 second response times
3. **Cost Analysis**: Validate <$0.05 per request target
4. **UX Testing**: Multi-turn bridge design conversations

---

## 💡 **Key Insights for Context**

### **Architecture Decision**: TCP Bridge (Proven) ✅
- Same architecture that worked with Claude Desktop
- Direct JSON over TCP socket, no HTTP complexity
- Fast execution, immediate request-response pattern
- Visual monitoring in Grasshopper bridge component

### **Model Configuration**: Gemini 2.5 Flash ✅
- Cost-efficient: 21x cheaper than Claude
- Working for all 4 agents
- Optimal price-performance ratio for production

### **Critical Files to Monitor**:
- `/src/bridge_design_system/agents/geometry_agent_json.py` - Context explosion source (URGENT FIX)
- `/src/bridge_design_system/agents/triage_agent.py` - Recursive context building (URGENT FIX)
- `/src/bridge_design_system/tools/memory_tools.py` - Fixed metadata issue (✅ working)
- `/src/bridge_design_system/mcp/grasshopper_mcp/bridge.py` - MCP tool definitions (✅ working)

---

## 📞 **Contact Points for User**

### **Commands to Test System**:
```bash
# Test system functionality
uv run python -m bridge_design_system.main --test

# Run interactive system
uv run python -m bridge_design_system.main

# Test working MCP pattern
uv run python test_simple_working_solution.py
```

### **Key Questions to Ask User**:
1. "Should I prioritize fixing context explosion over new features?"
2. "Is the system usable with manual conversation resets every 2-3 interactions?"
3. "What's the acceptable API cost per bridge design session?"
4. "Should I revert to CodeAgent temporarily while fixing context issues?"

---

## 🐛 **System Prompt Integration Problem**

### **Issue**: System prompts are loaded but not used
- **GeometryAgentSTDIO** loads system prompt from file but **doesn't pass it to CodeAgent**
- **TriageAgent** also loads system prompt but **doesn't pass it to its CodeAgent**
- **Root cause**: Neither CodeAgent nor ToolCallingAgent accept `system_prompt` as a parameter

### **Impact**:
- Domain-specific guidance from system prompts is not reaching the LLM
- Agents may not follow intended behaviors and constraints
- System prompt files exist but serve no purpose currently

### **Solution**:
- Embed system prompts in the task context when building conversation context
- This is already partially done in `_build_conversation_context()` methods
- Need to ensure system prompts are consistently included in all agent types

---

**Last Updated**: 2025-06-15 17:41 UTC  
**Status**: JSON Agent MCP integration ✅ COMPLETE | Context explosion 🚨 CRITICAL  
**Next Phase**: URGENT - Fix context management to prevent system failure