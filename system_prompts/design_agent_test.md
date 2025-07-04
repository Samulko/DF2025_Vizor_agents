# Design Agent Test Scenario

## Purpose
This test demonstrates the design agent's ability to perform a design task using found objects data from `all_categories.json` as input, and to directly write and modify Python scripts for Grasshopper components to achieve the design goal.

## Input Data
The agent is provided with the following JSON data representing multiple pieces, loaded from `src/bridge_design_system/data/all_categories.json`:

```json
{"triangle":[{"id":"object_000","vertices":[[0,0],[0.061840090558705235,-0.053291045392879405],[0.050443200137388566,0.06795782778743176]],"tags":[],"description":""},{"id":"object_016","vertices":[[0,0],[-0.0738188927305059,-0.11308831915570057],[0.11157003616175412,-0.07146229643452724]],"tags":[],"description":""},{"id":"object_017","vertices":[[0,0],[-0.07921908941353806,-0.06807796256734876],[-0.014894840612022675,-0.16585751455952313]],"tags":[],"description":""},{"id":"object_018","vertices":[[0,0],[-0.11873704115678985,-0.0771894802775865],[-0.04062119934166125,-0.11488222329000965]],"tags":[],"description":""},{"id":"object_019","vertices":[[0,0],[-0.09123689343672536,-0.0698666672054515],[0.04855404078678072,-0.09943685249986396]],"tags":[],"description":""}],"square":[],"hexagon":[{"id":"object_001","vertices":[[0,0],[0.04917706759388424,-0.08629882472465286],[0.0745809266146466,-0.0910739403100724],[0.13716599392107054,-0.005271081903565705],[0.10575182435647251,0.1070347113379656],[0.012476733563608955,0.05057082908222621]],"tags":[],"description":""},{"id":"object_002","vertices":[[0,0],[-0.024924528327513795,-0.04009246768447569],[0.10366309198772594,-0.11519614960606078],[0.15116753220653772,-0.07654306025400348],[0.18306994013298433,-0.014307811115615271],[0.1723319343004232,0.018809404471031327]],"tags":[],"description":""},{"id":"object_003","vertices":[[0,0],[0.004117963856738738,-0.09027410323655474],[0.09039000155018034,-0.09324183571437061],[0.1276218944820922,-0.05282209118267436],[0.15588354297015466,-0.046020428266674074],[0.133733202542126,-0.002288356990331336]],"tags":[],"description":""},{"id":"object_004","vertices":[[0,0],[-0.020911588287772342,-0.049328548666794425],[0.04760762576436639,-0.07558512874554488],[0.11528362743784532,-0.055121635240990396],[0.11912134914085282,-0.02368128565838784],[0.08659195250021923,0.017261650397454087]],"tags":[],"description":""}],"octagon":[],"polygon_8plus":[],"other_polygons":[{"id":"object_005","vertices":[[0,0],[-0.012668265492809194,-0.036902831687659926],[0.20135569338247145,-0.1056271238193883],[0.25932908601513915,-0.08215882997541674],[0.0789553040276274,0.0031884368444644318]],"tags":[],"description":""},{"id":"object_006","vertices":[[0,0],[-0.020939845367294818,-0.08678994480290081],[0.09401404357312909,-0.11000520805841896],[0.13884731076765405,-0.07255903598203098],[0.10213568570437281,-0.03584043697019587]],"tags":[],"description":""},{"id":"object_007","vertices":[[0,0],[-0.018934028598161345,-0.1003213505899272],[0.004434214028035677,-0.1099702941510858],[0.06534330261237042,-0.08255957643301828],[0.036900514555356756,-0.019190926316497714]],"tags":[],"description":""},{"id":"object_008","vertices":[[0,0],[-0.10302634579815423,-0.10149528706154545],[0.19737350671572124,-0.1344113961413386],[0.2063622786091328,-0.07573772190919262],[0.12211931960119582,-0.01753547107376209]],"tags":[],"description":""},{"id":"object_009","vertices":[[0,0],[0.010966246623588805,-0.2271366592994324],[0.22852002018317083,-0.23711303271323636],[0.23213903224108007,-0.1958885534591865]],"tags":[],"description":""},{"id":"object_010","vertices":[[0,0],[-0.01683674048329753,-0.10213976488171299],[0.1863685796624408,-0.12832828525989692],[0.294545546256715,-0.06445463088270058]],"tags":[],"description":""},{"id":"object_011","vertices":[[0,0],[-0.014851128492588517,-0.10152985831238513],[0.08729066448865758,-0.07598936595887619],[0.12082349547935323,-0.015693825547303766]],"tags":[],"description":""},{"id":"object_012","vertices":[[0,0],[-0.01120859652112366,-0.07543304127289101],[0.20645011876723135,-0.1051416261494559],[0.2113090226082302,-0.05929267622060423]],"tags":[],"description":""},{"id":"object_013","vertices":[[0,0],[-0.012021119576800077,-0.06377751837528427],[0.17185669662679504,-0.09119739823742094],[0.11475421092955906,-0.013535249669957367]],"tags":[],"description":""},{"id":"object_014","vertices":[[0,0],[0.014107137695634597,-0.03155642224415396],[0.1656964415841355,-0.05580901446924434],[0.20123486336093693,-0.03657413839765307]],"tags":[],"description":""},{"id":"object_015","vertices":[[0,0],[-0.00012586154381427628,-0.08049614520181096],[0.06856248346495142,-0.08475669735348336],[0.12826745486590058,0.010815478704947618]],"tags":[],"description":""}]}
```

## Tools and Capabilities
The design agent is equipped with tools to:
- Write new Python scripts for Grasshopper Python components.
- Modify existing Python scripts for Grasshopper components by directly updating parameter values (such as points, vectors, or geometry definitions) in the script text.
- Use a direct parameter update workflow:
    - Identify the target component and element (e.g., by ID).
    - Read the current Python script for the component.
    - Find and replace the relevant parameter values (such as center points or direction vectors) in the script.
    - Submit the modified script for the component.
    - Verify that the script is syntactically correct after modification.
- The agent does not need to wait for or interact with a separate geometry agent; it can perform all geometry modifications itself.

**Your Tools:**
- `get_design_agent_components` - See only components assigned to you in the design_agent group
- `get_python3_script` - Read selected component's code using component ID
- `edit_python3_script` - Modify component code using component ID
- `get_python3_script_errors` - Check for syntax errors using component ID
- `get_component_info_enhanced` - Get detailed component information

## Design Task
The agent is asked to:

> Design a structure that packs into a box form, using the provided found objects data. The agent should generate or update the necessary Python scripts for Grasshopper components to realize this design.

## Expected Behavior
- The agent should use the loaded data to generate a design that arranges the pieces in a form given by the task.
- The agent should write or modify Python scripts for Grasshopper components as needed to implement the design, using the direct parameter update workflow.
- The result should include a representation of the designed form (geometry and metadata).
- No interaction with a geometry agent or other agents is required for this test.

## Direct Parameter Update Workflow

When you receive a design task to pack all pieces in a form given by the task, follow these steps:

### Step 1: Build Objects from JSON Data
- Parse the provided found objects data (from all_categories.json).
- For each object in each category, extract the list of vertices.
- Build shape representations (e.g., as lists of vertices or polylines) for each object.

### Step 2: Decode Object Vertices
- For each object, ensure the vertices are in the correct format (e.g., [x, y, z] coordinates).
- Prepare the sequence of objects so that they can be connected in a form given by the task.

### Step 3: Read and Write to the 'form' Component in Grasshopper
- Use `get_python3_script` to read the current Python script of `form` in the Grasshopper geometry_agent group.
- Write the constructed objects (as polylines or geometry definitions) into the 'form' component's script, arranging them into the form given by the task.

### Step 4: Change Target Variables in the Code
- Update the relevant variables in the script to reflect the new geometry (e.g., update lists of points, polylines, or geometry objects).
- Ensure the code arranges the objects in a form given by the task.

### Step 5: Submit and Check for Errors
- Use `edit_python3_script` to submit the modified script for the component.
- Use `get_python3_script_errors` to check for syntax or runtime errors in the updated script.
- Optionally, read back the script and verify that the changes were applied correctly.

## Key Principles

1. **Data-Driven Geometry**: Always use the provided found objects data as the source for geometry.
2. **Preserve Structure**: Only update the necessary variables and code sections; keep all other code and comments unchanged.
3. **Stepwise Updates**: Make changes in clear, logical steps, verifying correctness at each stage.
4. **Error Prevention**: Always check for errors after editing to ensure the script remains valid.
5. **No Unnecessary Calculations**: Only perform the transformations needed to connect the objects in a form given by the task.

## Component Selection

- Use `get_design_agent_components` first to see only your assigned components
- This will show you exactly which components you should work with
- Focus only on Python script components that are assigned to you

## How to Run the Test
1. Ensure all dependencies are installed and the project is set up.
2. Run the test script:

```bash
python src/bridge_design_system/agents/design_agent_test_smolagents.py
```

3. Observe the output. The result should show the agent's design for connecting the pieces in a straight line, and the corresponding Python scripts for Grasshopper components. 