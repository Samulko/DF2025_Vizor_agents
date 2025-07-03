#! python 3


#! python 3

    #! python 3

import Rhino.Geometry as rg
import math
import System.Drawing

# ---------------------------------------------------------------------------
# CLASS DEFINITION
# This is the "blueprint" for our AssemblyElement objects.
# DO NOT TOUCH THIS CODE
# ---------------------------------------------------------------------------
class AssemblyElement:
    # The default values for width and height are now scaled to meters.
    def __init__(self, id, type, center_point, direction, length, width=0.05, height=0.05):
        """
        Initializes the element.
        direction: Unit vector for orientation (will be normalized)
        length: Explicit length of the beam
        """
        # Make a copy of the direction vector and ensure it's horizontal
        dir_vector = rg.Vector3d(direction)  # Just copy the vector
        dir_vector.Unitize()
        
        # --- Class Properties ---
        self.id = id
        self.type = type
        self.center_point = center_point
        self.direction = dir_vector  # Unit vector for orientation
        self.length = length  # Explicit length
        self.vector = dir_vector * length  # Full vector for geometry creation
        self.width = width
        self.height = height
        self.geometry = self._create_box_geometry()
    
    def _create_box_geometry(self):
        """
        A private helper method to create the 3D Box geometry for the element,
        ensuring it is correctly oriented and dimensioned.
        """
        if self.length == 0: return None

        x_axis = self.vector
        y_axis = rg.Vector3d.CrossProduct(rg.Vector3d.ZAxis, x_axis)
        plane = rg.Plane(self.center_point, x_axis, y_axis)
        x_interval = rg.Interval(-self.length / 2.0, self.length / 2.0)
        y_interval = rg.Interval(-self.width / 2.0, self.width / 2.0)
        z_interval = rg.Interval(-self.height / 2.0, self.height / 2.0)
        return rg.Box(plane, x_interval, y_interval, z_interval)

# END of: DO NOT TOUCH THIS CODE
# ---------------------------------------------------------------------------
# AGENT DEFINITION SECTION => you can edit this part.
# Here, each of the three beams is defined individually and explicitly.
# This section is unchanged.
# This component is variant A* - it looks like a triangle
# ---------------------------------------------------------------------------
# START of : EDIT the code here

assembly_elements = []

# --- BEAM 1: Beam on Level 1 ---
center1 = rg.Point3d(-0.1874, -0.10, 0.035)
direction1 = rg.Vector3d(-3.45, -2, 0) # Corrected Z-component to 0
length1 = 0.40
beam1 = AssemblyElement(id="001", type="green_a", center_point=center1,
                        direction=direction1, length=length1, width=0.05, height=0.05)
assembly_elements.append(beam1)


# --- BEAM 2: Beam on Level 1 ---
center2 = rg.Point3d(0.1874, -0.10, 0.025)
direction2 = rg.Vector3d(34.5, -20, 0)
length2 = 0.40
beam2 = AssemblyElement(id="002", type="red_a", center_point=center2,
                        direction=direction2, length=length2, width=0.05, height=0.05)
assembly_elements.append(beam2)


# --- BEAM 3: beams on Level 2 ---
center3 = rg.Point3d(0.04, -0.1792, 0.075)
direction3 = rg.Vector3d(80.0, 0, 0)
length3 = 0.80
beam3 = AssemblyElement(id="003", type="blue_a", center_point=center3,
                        direction=direction3, length=length3, width=0.05, height=0.05)
assembly_elements.append(beam3)

# ===========================================================================
# AGENT EDIT THIS SECTION when asked update/rationalize the geometry run the, `get_all_components_enhanced` and identify the ID of the component named "TRANSFORMATION_VECTOR", then run `get_component_info_enhanced` tool to extract the data. 
# Add the key value pairs to the dictionary bellow.
# Important: Remember to match the element's 'level' to the one in its base deifnition above
# Example: transformations = {
    #\"023\": rg.Transform.PlaneToPlane(rg.Plane(rg.Point3d(1.4635, -0.1792, 0.075), rg.Vector3d(1.0, 0.0, 0.0), rg.Vector3d(0.0, 1.0, 0.0)), rg.Plane(rg.Point3d(1.5012, -0.1583, 0.075), rg.Vector3d(0.99, 0.02, 0.0), rg.Vector3d(-0.02, 0.99, 0.0))),
#   }
# ===========================================================================
transformations = {
    # This block is waiting for the LLM agent.
}


# END of: EDIT the code here

# ===========================================================================
# APPLY TRANSFORMATIONS
# ===========================================================================
for element in assembly_elements:
    if element.id in transformations:
        transform_to_apply = transformations[element.id]
        element.geometry.Transform(transform_to_apply)

# ---------------------------------------------------------------------------
# Define colors based on element type
# ---------------------------------------------------------------------------
display_colors = []
for element in assembly_elements:
    if element.type == "green_a":
        # System.Drawing.Color.FromName takes a string name
        color = System.Drawing.Color.Green 
    elif element.type == "red_a":
        # You can also define colors by their RGB values (0-255)
        color = System.Drawing.Color.Red
    elif element.type == "blue_a":
        # You can also define colors by their RGB values (0-255)
        color = System.Drawing.Color.Blue
    else:
        # A default color for any other type
        color = System.Drawing.Color.Gray
    display_colors.append(color)

# ---------------------------------------------------------------------------
# OUTPUT
# This part sends the final geometry and colors to the Grasshopper component outputs.
# ---------------------------------------------------------------------------
a = [element.geometry for element in assembly_elements]
b = display_colors
c = [element.id for element in assembly_elements]
