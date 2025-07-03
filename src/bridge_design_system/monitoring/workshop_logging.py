"""
Simple modular workshop logging for student agents.

Students can add workshop logging to any agent with just 3 lines of code:
    from bridge_design_system.monitoring.workshop_logging import add_workshop_logging
    agent = create_my_agent()  # their existing agent
    add_workshop_logging(agent, "my_agent_name")
"""

import time
from typing import Any
from .trace_logger import log_agent_interaction
from ..config.logging_config import get_logger

logger = get_logger(__name__)


def add_workshop_logging(agent: Any, agent_name: str) -> Any:
    """
    Add workshop logging to any smolagents agent.
    
    This follows the exact same pattern as geometry_agent_smolagents.py:
    - Wraps the agent's run method
    - Tracks step counter
    - Logs start/completion/errors
    - Saves to workshop_logs/ directory structure
    
    Usage:
        from bridge_design_system.monitoring.workshop_logging import add_workshop_logging
        
        agent = CodeAgent(...)  # Create your agent normally
        add_workshop_logging(agent, "my_agent")  # Add logging
        
        # Now agent.run() automatically logs to workshop_logs/
    
    Args:
        agent: Any smolagents agent (CodeAgent, ToolCallingAgent, etc.)
        agent_name: Name to use in logs (e.g., "category_agent", "my_custom_agent")
    
    Returns:
        The same agent object with logging enabled
    """
    # Don't double-wrap if already has logging
    if hasattr(agent, '_workshop_logging_enabled'):
        logger.info(f"📊 Workshop logging already enabled for {agent_name}")
        return agent
    
    # Store original run method and add step counter
    agent._original_run = agent.run
    agent._step_counter = 0
    agent._workshop_logging_enabled = True
    
    def logged_run(task: str, **kwargs):
        """Enhanced run method with workshop logging (matches geometry agent pattern)."""
        # Increment step counter (same as geometry agent)
        agent._step_counter += 1
        step_number = agent._step_counter
        
        logger.info(f"🎯 {agent_name} executing task: {task[:100]}...")
        
        # Workshop logging - start (same as geometry agent lines 113-118)
        start_time = time.time()
        log_agent_interaction(
            agent_name=agent_name,
            step_number=step_number,
            task_description=task[:200] + "..." if len(task) > 200 else task,
            status="started"
        )
        
        try:
            # Call original run method
            result = agent._original_run(task, **kwargs)
            
            # Workshop logging - success (same as geometry agent lines 138-148)
            duration = time.time() - start_time
            result_str = str(result) if result else ""
            log_agent_interaction(
                agent_name=agent_name,
                step_number=step_number,
                task_description=task[:200] + "..." if len(task) > 200 else task,
                status="completed",
                response_content=result_str[:500] + "..." if len(result_str) > 500 else result_str,
                duration_seconds=duration
            )
            
            logger.info(f"✅ {agent_name} task completed successfully")
            return result
            
        except Exception as e:
            # Workshop logging - error (same as geometry agent lines 154-166)
            duration = time.time() - start_time
            log_agent_interaction(
                agent_name=agent_name,
                step_number=step_number,
                task_description=task[:200] + "..." if len(task) > 200 else task,
                status="failed",
                error_message=str(e),
                duration_seconds=duration
            )
            
            logger.error(f"❌ {agent_name} task failed: {e}")
            raise
    
    # Replace the run method (same as geometry agent line 428)
    agent.run = logged_run
    
    logger.info(f"📊 Workshop logging enabled for {agent_name}")
    logger.info(f"📁 Logs will be saved to workshop_logs/agents/{agent_name}_traces.jsonl")
    
    return agent


def remove_workshop_logging(agent: Any) -> Any:
    """
    Remove workshop logging from an agent (restore original behavior).
    
    Args:
        agent: The agent to restore
        
    Returns:
        The agent with original run method restored
    """
    if hasattr(agent, '_original_run'):
        agent.run = agent._original_run
        delattr(agent, '_original_run')
        delattr(agent, '_step_counter')
        delattr(agent, '_workshop_logging_enabled')
        logger.info("📊 Workshop logging disabled")
    
    return agent


# Convenience aliases
enable_logging = add_workshop_logging
disable_logging = remove_workshop_logging