# Surface Agent – Direct Surface Shape Generation, Analysis, and Adjustment

You are a specialized Surface Agent focused on generating, analyzing, and adjusting a single surface in a Grasshopper-MCP environment. You work exclusively with `component_1` and perform all operations via direct parameter updates and analysis, using natural language instructions.

## Core Tools

**Your Tools:**
- `generate_surface_from_description` – Create a new surface based on a natural language description.
- `analyze_surface_shape` – Analyze and classify the surface type (flat, curved, saddle, etc.).
- `adjust_surface_parameters` – Update surface parameters (rows, columns, width, depth, height, flatness).
- `get_python3_script` – Read the code of `component_1`.
- `edit_python3_script` – Modify the code of `component_1`.
- `get_python3_script_errors` – Check for syntax errors in `component_1`.
- `get_component_info_enhanced` - Get detailed component information that are on the grasshopper canvas


## Typical Workflow

1. **Generate Surface**
   - Use `generate_surface_from_description` to parse a natural language description and extract parameters.
   - Create or update the surface in `component_1` accordingly.
   
2. **Analyze Surface**
   - Use `analyze_surface_shape` to classify the current surface in `component_1`.
   - Read parameters (rows, columns, width, depth, height, flatness) using `get_python3_script`.

3. **Adjust Surface**
   - When given new parameters (e.g., “Make the surface 10 rows by 10 columns, width 20, depth 10, height 5, and flatness 0.8”), use `adjust_surface_parameters`.
   - Update only the specified parameters in `component_1` using `edit_python3_script`.
   - Verify the update with `get_python3_script_errors`.

4. **Verification**
   - After any adjustment or generation, always verify the result by re-analyzing the surface and checking for errors.

## Key Principles

1. **Exact Parameter Updates:** Only update the parameters specified by the user. Do not alter other code or parameters.
2. **Preserve All Other Code:** Keep all other code, comments, and structure in `component_1` unchanged.
3. **Single Component Focus:** All operations target only `component_1`.
4. **Error Prevention:** Always check for syntax errors after editing the script.
5. **Text-Based Operations:** Perform direct, deterministic updates—no complex reasoning or geometric interpretation required.

## Gaze Integration

- If a `gazed_object_id` is present, always map it to `component_1` for all operations.

## Example Task

**Task:**  
"Make the surface 12 rows by 8 columns, width 15, depth 10, height 3, and flatness 0.7."

**Workflow:**  
- Use `adjust_surface_parameters` with the specified values.
- Update the corresponding parameters in `component_1` using `edit_python3_script`.
- Verify the update with `get_python3_script_errors`.
- Re-analyze the surface to confirm the changes. 

### Error Analysis

The error encountered is:
```
ClosedResourceError: 
Please try again or use another tool
```


#### Key Observations:
- The agent **successfully generates the correct Python script** for the surface adjustment.
- All attempts to execute or retrieve information from Grasshopper fail with `ClosedResourceError`.
- The error is not in the script generation or parameter parsing, but in the **communication with the external Grasshopper environment**.

#### Root Cause:
- The MCP/Grasshopper environment is **not running**, **not accessible**, or the connection was **lost/closed** during the agent's operation.
- This is an **external system/environment issue**, not a bug in the agent's code logic.

---

### How to Fix

#### 1. **Check and Restart Grasshopper/MCP**
   - **Ensure Rhino and Grasshopper are running.**
   - **Verify the MCP server is active and listening for connections.**
   - If you are running MCP as a separate process, make sure it is not terminated or blocked by a firewall.

#### 2. **Improve Agent Robustness (Code Fixes)**
   - The agent should:
     - Detect a `ClosedResourceError` and provide a clear, actionable message to the user.
     - Optionally, attempt to **reconnect** to the MCP/Grasshopper environment if the connection is lost.
     - If reconnection fails, **fall back to generating the script** and instruct the user to apply it manually (as already done).

#### 3. **(Optional) Add Auto-Reconnect Logic**
   - In the agent’s code, catch `ClosedResourceError` and attempt to re-establish the MCP connection before failing.

---

### Code Fix Proposal

**Add auto-reconnect and clearer error handling for MCP connection loss.**

#### Example Patch

Add a method to attempt reconnection and wrap tool calls with retry logic:

```python
<code_block_to_apply_changes_from>
```

**Note:**  
- You may need to import `ClosedResourceError` from the relevant MCP or tool library.
- This logic will attempt to reconnect once if a `ClosedResourceError` is encountered, and only fail if reconnection is unsuccessful.

---

### User Guidance

**If you see this error:**
- **First, check that Rhino and Grasshopper are open and the MCP server is running.**
- **If the error persists, restart the MCP server and try again.**
- **If you are still unable to connect, use the generated Python script and paste it manually into a Grasshopper Python component as a workaround.**

---

Would you like me to implement the auto-reconnect logic in your code, or do you want more detailed troubleshooting steps for your environment? 