'''

This agent listen to vizor-ros system execution states and make robot interactions more natural (like a human colleague)

This is a runtime agent and does not care about HRC task generation. 
It understands the internal execution state of the robot and can verbalise it. 

It can generate natural language responses based on input. 
e.g.1 Input: "Verify task completion"
      Response: <personality prompt> + input --> "I'm ready to roll if everything looks a-ok. "

e.g.2 Input: "pick and place start"
      Response: <personality prompt> + input --> "fetch me a 40cm beam will ya? "

It can receive prompts from the user and make runtime changes + respond to user 
e.g.1 Input: "The robot is moving too slowly. Can you speed it up?"
      Response: modify execution bridge parameters --> "Done"
     
e.g.2 Input: "Shit I gave you the wrong beam earlier. Can we repeat the last round?"
      Response: repeat the execution stored in memory 
      NOTE: this is a more advanced feature, may not implement if we don't have enough time

[tbd] It can be a runtime assistant. 
AR input // move beam? -- "move to where beam 3 is right now and hold it please"

See if we can implement the UR10 control as a tool. i.e. vizor bridge -- listen to ros traj execution inputs

'''

