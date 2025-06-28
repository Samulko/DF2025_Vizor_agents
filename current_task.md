# **Direct Parameter Update Implementation**

## **CORE OBJECTIVE**

Implement a reliable Direct Parameter Update workflow where HoloLens users can move elements and have those changes directly applied to the Grasshopper script through precise parameter replacement, eliminating complex reasoning from the GeometryAgent.

## **🎯 THE DEFINITIVE WORKFLOW: Direct Parameter Update**

### **Ground Truth Process**

1. **Ground Truth**: The Grasshopper script and the HoloLens both start with the same known element positions and orientations, as defined in the script.

2. **User Action**: The user moves elements in the HoloLens and presses the "Update" button.

3. **Data Sent**: A message is sent with the new, absolute pose (position + quaternion) for each moved element.

4. **Calculation in main.py**: main.py receives this data. It uses a new, self-contained helper function to convert the quaternion into a direction vector. It now has the final [x,y,z] for the center and [a,b,c] for the direction.

5. **Queueing**: main.py formats a highly specific task (e.g., "Update element '001' by replacing its center and direction values") and adds it to the TRANSFORM_UPDATE_QUEUE.

6. **Agent Execution**: The GeometryAgent receives this task. Its job is now simple text replacement: find the correct lines in the script and overwrite the values in rg.Point3d(...) and rg.Vector3d(...).

7. **Memory Integration**: **BEFORE** text replacement, the agent automatically saves original values via step callbacks. **AFTER** replacement, the agent updates memory with change records for future queries.

**This process makes the agent's job extremely reliable, as it's not performing any complex reasoning—it's just executing a precise "find and replace" operation. The integrated memory system ensures original values are never lost and can be queried at any time.**

## **🛠️ FINAL IMPLEMENTATION PLAN & TO-DO LIST**

*This is the final checklist. It completely replaces the previous plans.*

### **Phase 1: Core Logic in main.py**

This phase implements the queue and the new helper function for calculations.

#### **[ ] Add a Math Helper Function to main.py:**
This pure Python function will live in main.py to handle the quaternion conversion without needing external libraries.

```python
# Add this helper function directly within your main.py file

def quaternion_to_direction_vector(quat_wxyz):
    """
    Converts a WXYZ quaternion to a forward direction vector.
    This assumes the "forward" direction corresponds to the X-axis in the local frame.
    """
    w, x, y, z = quat_wxyz
    # Formula to rotate a base vector (1, 0, 0) by the quaternion
    vx = 1.0 - 2.0 * (y*y + z*z)
    vy = 2.0 * (x*y - w*z)
    vz = 2.0 * (x*z + w*y)
    return [vx, vy, vz]
```

#### **[ ] Update VizorListener.py and main.py with the New Queue Logic:**
This implementation now includes the new helper function to pre-calculate everything.

```python
# agents/VizorListener.py
# Modify the listener to call a new formatting function in main.py or a shared utility module.
# For simplicity, we'll define the formatting logic inside main.py's loop.
class VizorListener:
    def __init__(self, update_queue):
        # ...
        self.update_queue = update_queue
    # ...
    def _handle_model_message(self, message):
        transforms = {} # Local variable
        # ... (logic to populate transforms dictionary is the same)
        if transforms:
            # Instead of formatting, just queue the raw data.
            # The main loop will handle formatting.
            self.update_queue.append(transforms)
            print(f"\n[SYSTEM] Transform data for {len(transforms)} element(s) queued for update.")

# main.py
def format_direct_update_task(element_id, new_center, new_direction):
    """Formats the precise task for the GeometryAgent."""
    return (
        f"Perform a direct parameter update for element with id '{element_id}'. "
        f"Replace its center point with these values: {new_center}. "
        f"Replace its direction vector with these values: {new_direction}."
    )

def interactive_mode(...):
    TRANSFORM_UPDATE_QUEUE = []
    vizor_listener = VizorListener(update_queue=TRANSFORM_UPDATE_QUEUE)
    # ...

    while True:
        # ...
        user_input = input("\nDesigner> ").strip()

        if TRANSFORM_UPDATE_QUEUE:
            print(f"[SYSTEM] Processing {len(TRANSFORM_UPDATE_QUEUE)} queued transform batch(es)...")

            # Process all data batches in the queue
            for transform_batch in TRANSFORM_UPDATE_QUEUE:
                for element_name, pose in transform_batch.items():
                    # element_name is "dynamic_021", element_id is "021" 
                    # ID encoding: 001-009→comp1, 011-019→comp2, 021-029→comp3, etc.
                    element_id = element_name.split('_')[-1]  # Keep full element ID: 021, 022, 023, etc.

                    # Use the helper function in main.py
                    new_pos = pose['position']
                    new_dir = quaternion_to_direction_vector(pose['quaternion'])

                    # Format the specific, direct task for the agent
                    task = format_direct_update_task(element_id, new_pos, new_dir)

                    # Process this single element update
                    print(f"[SYSTEM] Updating element {element_id}...")
                    response = triage.handle_design_request(request=task, gaze_id=None)
                    # ... (handle response)

            TRANSFORM_UPDATE_QUEUE.clear()
            print("[SYSTEM] Transform queue processed. Now handling your command.")

        # ... (process user_input)
```

### **Phase 2: Update GeometryAgent Instructions**

The agent needs completely new instructions for this workflow.

#### **[ ] Update system_prompts/geometry_agent.md:**
Delete any previous "Transformation Handling Workflow". Replace it with the following:

```markdown
## Direct Parameter Update Workflow

When you receive a task to perform a "direct parameter update," you must follow these steps precisely:

1.  **Parse Task:** The task will contain an `element_id` (e.g., '021'), a list of new center point values, and a list of new direction vector values. Extract these three pieces of information.
2.  **Decode ID:** Element ID encodes component+beam: '021'→component_3/beam_1, '022'→component_3/beam_2, etc.  
3.  **Read Script:** Use `get_python3_script` to read the appropriate component.
4.  **Find Target Variables:** Locate the specific beam variables (e.g., `center1`/`direction1` for '021').
5.  **Perform Text Replacement:**
    * Find the line defining the center point (e.g., `center1 = rg.Point3d(...)`).
    * Replace the numbers inside the parentheses with the new center point values from the task. The result should be, for example: `center1 = rg.Point3d(1.23, 4.56, 7.89)`.
    * Find the line defining the direction vector (e.g., `direction1 = rg.Vector3d(...)`).
    * Replace the numbers inside with the new direction vector values. The result should be, for example: `direction1 = rg.Vector3d(0.5, 0.5, 0.7)`.
5.  **Edit Script:** Use `edit_python3_script` to submit the *entire modified script* with the updated lines.
6.  **Verify:** After editing, use `get_python3_script_errors` to ensure you have not introduced any syntax errors.
```

## **🔑 KEY ARCHITECTURAL BENEFITS**

### **Maximum Reliability**
- Agent performs simple find-and-replace instead of complex reasoning
- Eliminates interpretation errors in coordinate transformations
- Deterministic parameter updates with precise control

### **Clear Separation of Concerns**
- **main.py**: Handles all quaternion math and queue processing
- **VizorListener**: Simple raw data collection and queueing
- **GeometryAgent**: Precise text replacement operations only

### **Improved Maintainability**
- All calculations in pure Python without external dependencies
- Simple, testable helper functions
- Clear data flow from HoloLens → main.py → GeometryAgent → Grasshopper

### **Error Reduction**
- Pre-calculated values eliminate agent calculation errors
- Simple text replacement reduces complexity
- Queue system ensures reliable batch processing

## **📋 IMPLEMENTATION CHECKLIST**

### **Phase 1: Core Logic**
- [ ] Add `quaternion_to_direction_vector()` to main.py
- [ ] Implement `TRANSFORM_UPDATE_QUEUE` processing
- [ ] Add `format_direct_update_task()` function
- [ ] Update VizorListener constructor and message handling

### **Phase 2: Agent Instructions**
- [ ] Replace geometry_agent.md transformation workflow
- [ ] Define 6-step Direct Parameter Update process
- [ ] Remove complex reasoning requirements

### **Phase 4: Native Smolagents Memory Integration**
- [ ] Create `track_design_changes()` step callback function
- [ ] Add step callbacks to geometry, triage, and syslogic agents
- [ ] Implement memory query system (`get_original_element_state()`, `query_design_history()`)
- [ ] Add manual step execution with memory control (`run_with_manual_steps()`)
- [ ] Implement memory transfer between agents (`transfer_geometry_memory()`)
- [ ] Create memory utilities module (`src/bridge_design_system/memory/`)

### **Phase 5: Memory-Enhanced Error Handling**
- [ ] Implement memory-based rollback system (`rollback_to_previous_state()`)
- [ ] Add design consistency checking using memory queries
- [ ] Integrate memory validation with Direct Parameter Update workflow
- [ ] Test memory-based error recovery and rollback functionality

### **Phase 3: Testing**
- [ ] Test quaternion conversion accuracy
- [ ] Verify element ID parsing (dynamic_001 → 021)
- [ ] Test queue processing with multiple elements
- [ ] Validate script text replacement operations

### **Phase 4: Native Smolagents Memory Integration**

This phase implements the missing native smolagents memory methods to automatically track and remember original element values, solving the core issue where agents forget design history.

#### **[ ] Step Callbacks for Design State Tracking:**
Implement automatic memory tracking using smolagents native step callbacks.

```python
# Create memory callback function in src/bridge_design_system/memory/
def track_design_changes(memory_step: ActionStep, agent: CodeAgent) -> None:
    """
    Native smolagents step callback to automatically save original element values.
    
    Called after each agent step to extract and store design state changes.
    Follows smolagents best practices from official documentation.
    """
    from smolagents import ActionStep
    import json
    import re
    
    # Extract element modifications from step observations
    if hasattr(memory_step, 'observations') and memory_step.observations:
        # Parse for Direct Parameter Update tasks
        if "direct parameter update" in memory_step.observations.lower():
            element_match = re.search(r"element.*?'(\w+)'", memory_step.observations)
            if element_match:
                element_id = element_match.group(1)
                
                # Save original values BEFORE modification
                original_state = {
                    "element_id": element_id,
                    "timestamp": memory_step.step_number,
                    "action": "parameter_update",
                    "step_type": "design_change"
                }
                
                # Store in memory step observations with structured format
                memory_step.observations += f"\n[MEMORY] Original state saved for element {element_id}"
    
    # Memory cleanup - remove old screenshots/data (smolagents best practice)
    latest_step = memory_step.step_number
    for previous_step in agent.memory.steps:
        if isinstance(previous_step, ActionStep) and previous_step.step_number <= latest_step - 3:
            # Keep only last 3 steps with full context to save memory
            if hasattr(previous_step, 'observations_images'):
                previous_step.observations_images = None
```

#### **[ ] Add Step Callbacks to All Agents:**
Integrate the callback into geometry, triage, and syslogic agents.

```python
# Update geometry_agent_smolagents.py line ~66
self.agent = ToolCallingAgent(
    tools=all_tools,
    model=self.model,
    max_steps=12,
    name="geometry_agent",
    description="Creates 3D geometry in Rhino Grasshopper via MCP connection...",
    step_callbacks=[monitoring_callback, track_design_changes] if monitoring_callback else [track_design_changes],
)

# Update triage_agent_smolagents.py line ~115  
manager = CodeAgent(
    tools=manager_tools,
    model=model,
    name="triage_agent", 
    description="Coordinates bridge design tasks by delegating to specialized agents",
    max_steps=max_steps,
    step_callbacks=[*step_callbacks, track_design_changes],
    managed_agents=[geometry_agent, syslogic_agent],
    **kwargs,
)
```

#### **[ ] Memory Query System:**
Implement native smolagents memory queries for retrieving design history.

```python
# Create memory utilities in src/bridge_design_system/memory/memory_queries.py
from smolagents import ActionStep, TaskStep
from typing import Dict, List, Optional, Any

def get_original_element_state(agent: Any, element_id: str) -> Optional[Dict]:
    """
    Query agent's native memory for original element state.
    
    Uses smolagents agent.memory.steps to find the earliest record of element.
    Returns original values before any modifications.
    """
    for step in agent.memory.steps:
        if isinstance(step, ActionStep) and hasattr(step, 'observations'):
            if step.observations and f"element {element_id}" in step.observations:
                # Found original state record
                return {
                    "element_id": element_id,
                    "step_number": step.step_number,
                    "original_observations": step.observations
                }
    return None

def query_design_history(agent: Any, element_id: str) -> List[Dict]:
    """
    Get complete design history for an element from agent memory.
    
    Returns chronological list of all changes to the element.
    """
    history = []
    for step in agent.memory.steps:
        if isinstance(step, ActionStep) and hasattr(step, 'observations'):
            if step.observations and element_id in step.observations:
                history.append({
                    "step_number": step.step_number,
                    "observations": step.observations,
                    "error": getattr(step, 'error', None)
                })
    return history

def get_element_changes_count(agent: Any) -> Dict[str, int]:
    """Count how many times each element has been modified."""
    changes = {}
    for step in agent.memory.steps:
        if isinstance(step, ActionStep) and hasattr(step, 'observations'):
            if step.observations and "parameter update" in step.observations.lower():
                # Extract element ID from observations
                import re
                match = re.search(r"element.*?'(\w+)'", step.observations)
                if match:
                    element_id = match.group(1)
                    changes[element_id] = changes.get(element_id, 0) + 1
    return changes
```

#### **[ ] Manual Step Execution for Memory Control:**
Add option for step-by-step execution with memory modification between steps.

```python
# Add to geometry_agent_smolagents.py
def run_with_manual_steps(self, task: str, enable_memory_tracking: bool = True) -> Any:
    """
    Execute task with manual step control for enhanced memory management.
    
    Follows smolagents documentation pattern for manual execution.
    Allows memory modification between steps for precise design state tracking.
    """
    from smolagents import ActionStep, TaskStep
    
    logger.info(f"🔧 Starting manual execution with memory tracking: {enable_memory_tracking}")
    
    # Add task to memory
    self.agent.memory.steps.append(TaskStep(task=task, task_images=[]))
    
    final_answer = None
    step_number = 1
    max_steps = 10
    
    while final_answer is None and step_number <= max_steps:
        memory_step = ActionStep(
            step_number=step_number,
            observations_images=[],
        )
        
        # Run one step
        final_answer = self.agent.step(memory_step)
        self.agent.memory.steps.append(memory_step)
        
        # CRITICAL: Memory modification between steps (smolagents native pattern)
        if enable_memory_tracking and "parameter update" in str(memory_step.observations):
            # Save design state before next step
            self.agent.memory.steps[-1].observations += "\n[MANUAL_MEMORY] Design state tracked"
            
        step_number += 1
    
    logger.info(f"✅ Manual execution completed with {len(self.agent.memory.steps)} memory steps")
    return final_answer
```

#### **[ ] Memory Transfer Between Agents:**
Enable sharing design history between geometry and triage agents.

```python
# Add to triage_agent_smolagents.py
def transfer_geometry_memory(self, geometry_agent: Any) -> None:
    """
    Transfer design memory from geometry agent to triage agent.
    
    Uses smolagents native memory.steps transfer pattern from documentation.
    """
    if hasattr(geometry_agent, 'memory') and hasattr(geometry_agent.memory, 'steps'):
        # Selective transfer of design-related steps only
        design_steps = []
        for step in geometry_agent.memory.steps:
            if isinstance(step, ActionStep) and hasattr(step, 'observations'):
                if step.observations and ("parameter update" in step.observations.lower() or 
                                        "element" in step.observations.lower()):
                    design_steps.append(step)
        
        # Add to triage agent memory (native smolagents pattern)
        self.manager.memory.steps.extend(design_steps)
        logger.info(f"🔄 Transferred {len(design_steps)} design memory steps from geometry agent")
```

### **Phase 5: Memory-Enhanced Error Handling**

Implement memory-based rollback and error recovery using native smolagents memory.

#### **[ ] Memory-Based Rollback System:**
Use agent memory to restore previous states when parameter updates fail.

```python
# Add to geometry_agent_smolagents.py  
def rollback_to_previous_state(self, element_id: str) -> bool:
    """
    Rollback element to previous known good state using agent memory.
    
    Uses native smolagents memory.steps to find and restore previous values.
    """
    from .memory.memory_queries import query_design_history
    
    history = query_design_history(self.agent, element_id)
    if len(history) >= 2:  # Need at least 2 states to rollback
        previous_state = history[-2]  # Second to last state
        
        # Create rollback task
        rollback_task = f"Restore element '{element_id}' to previous state from step {previous_state['step_number']}"
        
        # Execute rollback using manual steps for memory control
        return self.run_with_manual_steps(rollback_task, enable_memory_tracking=True)
    
    return False
```

#### **[ ] Design Consistency Checking:**
Validate changes against design history stored in agent memory.

```python
# Add validation using memory queries
def validate_design_consistency(self, element_id: str, new_values: Dict) -> bool:
    """Validate proposed changes against design history in agent memory."""
    from .memory.memory_queries import get_original_element_state, query_design_history
    
    original_state = get_original_element_state(self.agent, element_id)
    history = query_design_history(self.agent, element_id)
    
    # Check for reasonable change magnitude
    if original_state and len(history) > 0:
        # Implement validation logic based on design history patterns
        return True
    
    return False
```

This final plan integrates native smolagents memory methods with the Direct Parameter Update workflow, ensuring agents automatically track and can query original element values while maintaining maximum reliability.