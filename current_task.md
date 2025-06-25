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

**This process makes the agent's job extremely reliable, as it's not performing any complex reasoning—it's just executing a precise "find and replace" operation.**

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
                    # element_name is "dynamic_001", id is "001"
                    element_id = element_name.split('_')[-1]  # Keep full ID: 001, 002, 021

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

1.  **Parse Task:** The task will contain an `element_id` (e.g., '001'), a list of new center point values, and a list of new direction vector values. Extract these three pieces of information.
2.  **Read Script:** Use `get_python3_script` to read the code of the relevant component.
3.  **Find Target Variables:** In the script, locate the variable names associated with the target `element_id`. For `id="001"`, you would be looking for the variables `center1` and `direction1`.
4.  **Perform Text Replacement:**
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

### **Phase 3: Testing**
- [ ] Test quaternion conversion accuracy
- [ ] Verify element ID parsing (dynamic_001 → 021)
- [ ] Test queue processing with multiple elements
- [ ] Validate script text replacement operations

This final plan aligns perfectly with your specified workflow, resolves the technical challenges, and makes the agent's role maximally reliable.