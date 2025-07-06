C:\Users\17124\Desktop\D+2025+ICD\DF2025_Vizor_agents
src
│   ├── bridge_design_system
│   └── vizor_agents.egg-info
system_prompts
│   ├── backup_geometry_agent.md
│   ├── geometry_agent.md
│   ├── geometry_agent_202507031910.md
│   ├── geometry_agent_202507032043.md
│   ├── rational_agent.md
│   ├── SysLogic_agent.md
│   └── triage_agent.md
examples
│   ├── 290625_workflow.gh
│   ├── Component
│   ├── GH_MCP
│   └── GH_MCP_iOS


C:\Users\17124\Desktop\D+2025+ICD\DF2025_Vizor_agents
src/bridge_design_system
│   ├── agents
│   │   ├── agent_templates.py
│   │   ├── geometry_agent_smolagents.py
│   │   ├── hrc_agent.py
│   │   ├── objects.py
│   │   ├── rational_smolagents.py
│   │   ├── realtime_gemini_agent.py
│   │   ├── robot_agent.py
│   │   ├── syslogic_agent_smolagents.py
│   │   ├── triage_agent_smolagents.py
│   │   ├── VizorListener.py
│   │   ├── __init__.py
│   │   └── __pycache__
│   │   │   ├── geometry_agent_smolagents.cpython-312.pyc
│   │   │   ├── rational_smolagents.cpython-312.pyc
│   │   │   ├── triage_agent_smolagents.cpython-312.pyc
│   │   │   ├── VizorListener.cpython-312.pyc
│   │   │   └── __init__.cpython-312.pyc
│   ├── api
│   │   ├── status_broadcaster.py
│   │   ├── websocket_server.py
│   │   └── __init__.py
│   ├── config
│   │   ├── logging_config.py
│   │   ├── model_config.py
│   │   ├── settings.py
│   │   ├── __init__.py
│   │   └── __pycache__
│   │   │   ├── logging_config.cpython-312.pyc
│   │   │   ├── model_config.cpython-312.pyc
│   │   │   ├── settings.cpython-312.pyc
│   │   │   └── __init__.cpython-312.pyc
│   ├── data
│   │   ├── backups
│   │   │   ├── auto_backup_before_reset_20250624_122647.json
│   │   │   ├── auto_backup_before_reset_20250624_122707.json
│   │   │   ├── auto_backup_before_reset_20250625_052632.json
│   │   │   ├── auto_backup_before_reset_20250625_065255.json
│   │   │   ├── auto_backup_before_reset_20250626_131927.json
│   │   │   └── cli_backup_before_reset_20250624_061123.json
│   │   ├── material_inventory.json
│   │   ├── material_inventory.json.backup
│   │   └── memory
│   ├── database
│   │   └── __init__.py
│   ├── main.py
│   ├── mcp
│   │   ├── GH_MCP
│   │   │   ├── .gitignore
│   │   │   ├── BUILD_INSTRUCTIONS.md
│   │   │   ├── fix_references.ps1
│   │   │   ├── fix_references.py
│   │   │   ├── fix_references.sh
│   │   │   ├── gha
│   │   │   ├── GH_AssemblyInfo.cs
│   │   │   ├── GH_MCP
│   │   │   ├── GH_MCP.sln
│   │   │   ├── Properties
│   │   │   ├── README.md
│   │   │   ├── TEST_INSTRUCTIONS.md
│   │   │   ├── VizorAgents.GH_MCP.csproj
│   │   │   └── VizorAgents.GH_MCP.sln
│   │   ├── grasshopper_mcp
│   │   │   ├── bridge.py
│   │   │   ├── tools
│   │   │   ├── utils
│   │   │   ├── __init__.py
│   │   │   ├── __main__.py
│   │   │   └── __pycache__
│   │   ├── grasshopper_mcp.egg-info
│   │   │   ├── dependency_links.txt
│   │   │   ├── entry_points.txt
│   │   │   ├── PKG-INFO
│   │   │   ├── requires.txt
│   │   │   ├── SOURCES.txt
│   │   │   └── top_level.txt
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── setup.py
│   │   ├── streamable_http_server.py
│   │   ├── uv.lock
│   │   └── __init__.py
│   ├── memory
│   │   ├── memory_callbacks.py
│   │   ├── memory_queries.py
│   │   ├── memory_utils.py
│   │   ├── __init__.py
│   │   └── __pycache__
│   │   │   ├── memory_callbacks.cpython-312.pyc
│   │   │   ├── memory_queries.cpython-312.pyc
│   │   │   ├── memory_utils.cpython-312.pyc
│   │   │   └── __init__.cpython-312.pyc
│   ├── monitoring
│   │   ├── agent_monitor.py
│   │   ├── design_profile.json
│   │   ├── DF logo.png
│   │   ├── example.html
│   │   ├── hololens_visualization
│   │   │   ├── assets
│   │   │   ├── index.html
│   │   │   ├── plan.md
│   │   │   ├── README.md
│   │   │   ├── realStructure.md
│   │   │   ├── test.html
│   │   │   ├── test_enhanced.html
│   │   │   ├── test_unified_animation.html
│   │   │   ├── UNIFIED_ANIMATION_REFACTOR.md
│   │   │   └── unused
│   │   ├── lcars_interface.py
│   │   ├── lcars_otel_bridge.py
│   │   ├── otel_config.py
│   │   ├── README.md
│   │   ├── server.py
│   │   ├── status.html
│   │   ├── trace_logger.py
│   │   ├── __init__.py
│   │   └── __pycache__
│   │   │   ├── agent_monitor.cpython-312.pyc
│   │   │   ├── lcars_interface.cpython-312.pyc
│   │   │   ├── lcars_otel_bridge.cpython-312.pyc
│   │   │   ├── otel_config.cpython-312.pyc
│   │   │   ├── server.cpython-312.pyc
│   │   │   ├── trace_logger.cpython-312.pyc
│   │   │   └── __init__.cpython-312.pyc
│   ├── py.typed
│   ├── state
│   │   ├── component_registry.py
│   │   ├── __init__.py
│   │   └── __pycache__
│   │   │   ├── component_registry.cpython-312.pyc
│   │   │   └── __init__.cpython-312.pyc
│   ├── tools
│   │   ├── material_tools.py
│   │   ├── memory_tools.py
│   │   ├── __init__.py
│   │   └── __pycache__
│   │   │   ├── material_tools.cpython-312.pyc
│   │   │   ├── memory_tools.cpython-312.pyc
│   │   │   └── __init__.cpython-312.pyc
│   ├── voice_input.py
│   ├── whisper-voice-assistant
│   │   ├── .env.example
│   │   ├── .gitignore
│   │   ├── INTEGRATION_GUIDE.md
│   │   ├── LICENSE
│   │   ├── models
│   │   │   └── .gitkeep
│   │   ├── poetry.lock
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── testing.py
│   │   ├── uv.lock
│   │   └── voice_assistant.py
│   ├── __init__.py
│   ├── __main__.py
│   └── __pycache__
│   │   ├── main.cpython-312.pyc
│   │   ├── voice_input.cpython-312.pyc
│   │   └── __init__.cpython-312.pyc
src/vizor_agents.egg-info
│   ├── dependency_links.txt
│   ├── entry_points.txt
│   ├── PKG-INFO
│   ├── requires.txt
│   ├── SOURCES.txt
│   └── top_level.txt

