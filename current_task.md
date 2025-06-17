# **Refactoring Plan: Creating an Autonomous Agent System**

## **🎯 CORE ISSUE**

The current agent architecture is brittle because the **Triage Agent is responsible for managing the Geometry Agent's state**. This creates unnecessary complexity, leads to custom-built tools that fight the framework's design, and makes the system hard to maintain.

The solution is to **refactor the system to make the Geometry Agent autonomous and stateful**, aligning with `smolagents` best practices.

## **🔍 BRUTAL REALITY CHECK**

### **What the Current System Does**

The Triage Agent acts as a puppeteer. It uses a suite of complex tools (`get_most_recent_component`, `search_geometry_agent_memory`) to inspect the Geometry Agent's memory, construct a hyper-specific task, delegate it, and then track the result itself. This is functional but inefficient and not robust.

### **What a Better System Should Do**

The Triage Agent should act as a manager. It delegates high-level, conversational tasks. The Geometry Agent, as the specialist, should be fully responsible for understanding the context, managing its own memory, and executing the task. This is simpler, more robust, and the intended pattern of the `smolagents` framework.

### **The Fundamental Limitation of the Current Approach**

You have built a system of dependencies that makes change difficult. Every new memory requirement needs a new tool on the Triage Agent. The "session boundary" problem had to be solved with an external cache, which is a symptom of this flawed architecture.

## **📋 PRACTICAL REFACTORING APPROACH**

### **Focus: Implement a Clean Separation of Concerns**

Instead of patching the old system, we will refactor it based on a simple principle: **the agent that does the work is the agent that manages the memory of that work.**

1. **Make the Geometry Agent Stateful** \- It will track its own components and session history.  
2. **Simplify the Triage Agent** \- It will become a pure delegator, with no knowledge of the Geometry Agent's internal workings.  
3. **Update the Interaction Model** \- Delegation will be conversational, not programmatic.  
4. **Revise System Prompts** \- Prompts will reflect the new, autonomous roles.

   ## **🛠️ REALISTIC REFACTORING DESIGN**

   ### **Phase 1: Make the Geometry Agent Stateful**

Modify `MCPGeometryAgent` in `triage_agent_smolagents.py`. It should manage its own state, including the session-specific cache.

1. \# Inside MCPGeometryAgent class in triage\_agent\_smolagents.py  
2.   
3. class MCPGeometryAgent(ToolCallingAgent):  
4.     def \_\_init\_\_(self):  
5.         \# ... existing setup ...  
6.           
7.         \# The agent now owns its state. This cache is reset with each new instance.  
8.         self.internal\_component\_cache \= \[\] \# List to store \[{id, type, timestamp}\]  
9.   
10.         \# ... rest of the initialization ...  
11.   
12.     def run(self, task: str) \-\> Any:  
13.         \# ... logic to resolve context from self.memory.steps and self.internal\_component\_cache ...  
14.           
15.         result \= super().run(task)  
16.           
17.         \# After a successful tool call that creates a component, the agent tracks it internally.  
18.         self.\_track\_component\_in\_state(result)  
19.           
20.         return result  
21.   
22.     def \_track\_component\_in\_state(self, result\_from\_mcp: str):  
23.         \# Internal method to parse a result from an MCP tool call (like add\_python3\_script)  
24.         \# and update self.internal\_component\_cache.  
25.         component\_id \= self.\_extract\_id\_from\_result(result\_from\_mcp)  
26.         if component\_id:  
27.             component\_info \= {  
28.                 "id": component\_id,  
29.                 "type": self.\_determine\_component\_type(result\_from\_mcp),  
30.                 "timestamp": datetime.now().isoformat()  
31.             }  
32.             self.internal\_component\_cache.append(component\_info)  
33.             logger.info(f"Geometry Agent internally tracked new component: {component\_id}")  
34.   
    

**What this achieves:** The Geometry Agent is now self-reliant. It handles the "session boundary" problem internally.

### **Phase 2: Simplify the Triage Agent**

Modify `create_triage_system` in `triage_agent_smolagents.py`. Remove all the custom memory-inspection tools.

35. \# In triage\_agent\_smolagents.py  
36.   
37. def create\_triage\_system(...):  
38.     \# ...  
39.       
40.     \# OLD: A complex set of tools for the Triage Agent to inspect memory  
41.     \# manager\_tools \= \[material\_tool, structural\_tool\] \+ \_create\_coordination\_tools() \+ \_create\_geometry\_memory\_tools()  
42.   
43.     \# NEW: The Triage Agent only needs simple coordination tools.  
44.     \# The \_create\_geometry\_memory\_tools function is deleted entirely.  
45.     manager\_tools \= \[material\_tool, structural\_tool\] \+ \_create\_coordination\_tools()  
46.   
47.     manager \= CodeAgent(  
48.         tools=manager\_tools,  
49.         managed\_agents=\[geometry\_agent\],  
50.         \# ...  
51.     )  
52.   
53.     \# The custom prompt is simplified, as it no longer needs to explain the memory tools.  
54.     custom\_prompt \= get\_simplified\_triage\_system\_prompt()  
55.     \# ...  
    

**What this achieves:** The Triage Agent is now simpler, lighter, and adheres to its role as a pure manager. Its code and prompts become much cleaner.

### **Phase 3: Update the Delegation Flow**

This is a change in *how* the agents are used. The logic is no longer about inspecting memory but about conversational delegation.

**OLD** PATTERN (in Triage **Agent's mind):**

1. User: "modify the curve"  
2. Triage: Call `get_most_recent_component("curve")` \-\> returns `curve_001`.  
3. Triage: Construct task: `"Modify` component curve\_001 `to be an arch."`  
4. Triage: Delegate `geometry_agent(task=...)`.

**NEW PATTERN (in Triage Agent's mind):**

1. User: "modify the curve"  
2. Triage: Delegate `geometry_agent(task="modify the curve")`.  
3. Geometry Agent receives the task, searches its *own* memory for the most recent curve, finds `curve_001`, and executes the modification.

**What this achieves:** The interaction is more natural and robust. The reasoning is correctly placed within the specialized agent.

## **🎯 HONEST SUCCESS CRITERIA**

### **What Success Looks Like**

1. ✅ **Code is Simpler** \- The `triage_agent_smolagents.py` file is significantly smaller. The complex memory tools are gone.  
2. ✅ **Logic is Encapsulated** \- The Geometry Agent contains all logic related to geometry components and their history.  
3. ✅ **System is More Robust** \- The "session boundary" issue is handled gracefully inside the agent that is re-initialized with each session.  
4. ✅ **Prompts are Clearer** \- System prompts are shorter and describe roles, not complex procedures.

   ### **What Success Does NOT Change**

This refactoring is architectural. It does not change the fundamental limitations of the environment:

1. ❌ It won't make the LLM better at understanding ambiguous instructions.  
2. ❌ It won't fix bugs in Grasshopper or the MCP connection.

   ## **📊 REFACTORING VALUE ASSESSMENT**

   ### **Realistic Value: High**

* ✅ **Maintainability**: **High impact**. The code becomes radically simpler to understand, debug, and extend.  
* ✅ **Robustness**: **High impact**. Eliminates brittle dependencies between agents and handles session state correctly.  
* ✅ **Framework Alignment**: **High impact**. The system now uses `smolagents` as intended, making it easier to adopt new features from the library in the future.

  ## **🛠️ IMPLEMENTATION PLAN**

  ### **Phase 1: Refactor the Geometry Agent (Est: 2-3 hours)**

1. Modify the `MCPGeometryAgent` class.  
2. Add the `self.internal_component_cache` instance variable.  
3. Implement the internal `_track_component_in_state` method.  
4. Add logic to the `run` method to consult its internal state/memory when it receives a follow-up task.

   ### **Phase 2: Refactor the Triage Agent & Prompts (Est: 2 hours)**

1. Delete the `_create_geometry_memory_tools` function and all its associated tools from `triage_agent_smolagents.py`.  
2. Simplify the `create_triage_system` function to remove the tool additions.  
3. Rewrite the `triage_agent.md` and `geometry_agent.md` system prompts to reflect the new autonomous roles.

   ### **Phase 3: Validate with Mock Testing (Est: 2 hours)**

1. Implement the mock tests from the "Updated Testing Plan" document.  
2. Run these tests to confirm that the new architecture works as expected in a controlled environment.

   ## **🔍 WHAT THIS FIX REVEALS**

   ### **Questions This Refactoring Answers**

1. Is a simpler, decentralized architecture more robust? **Yes.**  
2. Can an agent be responsible for its own conversational memory and session state? **Yes.**  
3. Does this solve the core issue of "forgetting" in a clean, maintainable way? **Yes.**

   ## **💯 HONEST ASSESSMENT**

   ### **Why This Approach is Better**

1. **It is the right architecture.** It follows established software design principles (separation of concerns, encapsulation).  
2. **It reduces code debt.** It removes custom, complex code in favor of simple, direct patterns.  
3. **It builds confidence.** A successful refactoring proves the system's logic is sound before tackling real-world integration challenges.

   ### **What Comes Next**

After this refactoring is complete and validated with mock tests, the system will be in a much stronger position for the next, necessary phase: **manual, human-in-the-loop testing** with the actual Grasshopper environment.

## **🎯 FINAL REALITY**

This refactoring is a critical, necessary step. It moves the system from a complex, hard-to-maintain prototype to a robust, well-architected foundation. By doing this work now, you make all future development and testing simpler and more effective.

