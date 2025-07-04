from src.bridge_design_system.agents.form_agent import create_form_agent

if __name__ == "__main__":
    # Example 2D pattern (square)
    pattern_2d = [
        [0.0, 0.0],
        [1.0, 0.0],
        [1.0, 1.0],
        [0.0, 1.0]
    ]
    # Example anchor indices (corners)
    anchor_indices = [0, 1, 2, 3]
    # Example flatness and curvature
    flatness = 0.5
    curvature = 1.0

    agent = create_form_agent()
    task = (
        f"Run Kangaroo simulation with pattern_2d={pattern_2d}, "
        f"anchor_indices={anchor_indices}, flatness={flatness}, curvature={curvature} "
        f"and return the resulting geometry."
    )
    result = agent.run(task)
    print("Resulting geometry:")
    print(result) 