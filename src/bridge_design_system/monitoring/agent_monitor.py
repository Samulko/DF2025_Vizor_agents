"""Enhanced agent monitor with direct smolagents step_callbacks integration."""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from smolagents import ActionStep

from ..config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AgentStatus:
    """Agent status data structure."""

    name: str
    status: str  # ready, working, delegating, mcp_connecting, validating, error
    step_number: Optional[int] = None
    current_task: Optional[str] = None
    last_update: float = 0.0
    error_message: Optional[str] = None
    memory_size: int = 0
    tool_calls: List[str] = None
    last_response: Optional[str] = None  # Store the agent's last response for task history

    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []
        if self.last_update == 0.0:
            self.last_update = time.time()


class AgentStatusTracker:
    """Manages current status of all monitored agents."""

    def __init__(self):
        self.agents: Dict[str, AgentStatus] = {}
        self.callbacks: Set[Callable] = set()
        self._lock = asyncio.Lock()

    def register_agent(self, name: str, agent_type: str = "unknown") -> None:
        """Register a new agent for monitoring."""
        self.agents[name] = AgentStatus(name=name, status="ready", last_update=time.time())
        logger.debug(f"📊 Registered agent for monitoring: {name} ({agent_type})")

    async def update_status(self, name: str, **kwargs) -> None:
        """Update agent status and notify callbacks."""
        async with self._lock:
            if name not in self.agents:
                self.register_agent(name)

            agent = self.agents[name]
            for key, value in kwargs.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)

            agent.last_update = time.time()

            # Notify all callbacks
            await self._notify_callbacks()

    def add_callback(self, callback: Callable) -> None:
        """Add a callback to be notified of status changes."""
        self.callbacks.add(callback)

    def remove_callback(self, callback: Callable) -> None:
        """Remove a callback."""
        self.callbacks.discard(callback)

    async def _notify_callbacks(self) -> None:
        """Notify all callbacks of status change."""
        status_dict = {
            name: {
                "name": agent.name,
                "status": agent.status,
                "step_number": agent.step_number,
                "current_task": agent.current_task,
                "last_update": agent.last_update,
                "error_message": agent.error_message,
                "memory_size": agent.memory_size,
                "tool_calls": agent.tool_calls,
                "last_response": agent.last_response,
                "timestamp": datetime.now().isoformat(),
            }
            for name, agent in self.agents.items()
        }

        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(status_dict)
                else:
                    callback(status_dict)
            except Exception as e:
                logger.error(f"❌ Callback error: {e}")


class MonitorCallback:
    """Lightweight step callback for smolagents that captures minimal execution data."""

    # Class-level toggle for all monitoring
    monitoring_enabled = True

    def __init__(
        self,
        status_tracker: AgentStatusTracker,
        agent_name: str,
        update_cooldown: float = 0.5,
        high_performance_mode: bool = False,
    ):
        self.status_tracker = status_tracker
        self.agent_name = agent_name
        self._last_update_time = 0
        self._update_cooldown = update_cooldown
        self._high_performance_mode = high_performance_mode  # Skip some updates for performance
        self._skip_counter = 0
        self._completion_reset_delay = 10.0  # Reset to ready after 10 seconds
        self._last_completion_time = 0
        logger.debug(
            f"🔗 Created lightweight MonitorCallback for {agent_name} (performance_mode={high_performance_mode})"
        )

    def __call__(self, memory_step: ActionStep, agent: Any) -> None:
        """Called after each agent step - captures minimal step data and updates status."""
        # Early exit if monitoring disabled
        if not self.monitoring_enabled:
            return

        current_time = time.time()

        # Rate limiting to prevent spam updates
        if current_time - self._last_update_time < self._update_cooldown:
            return

        # High performance mode - skip every other update
        if self._high_performance_mode:
            self._skip_counter += 1
            if self._skip_counter % 2 == 0:
                return

        try:
            # Extract minimal step information
            step_data = self._extract_minimal_step_data(memory_step, agent)

            # Check if this is a completion step
            is_completion = step_data.get("status") == "completed"

            # Simple sync update using thread-safe queue
            self._queue_status_update(step_data)
            self._last_update_time = current_time

            # If this is a completion, schedule a reset to "ready" after delay
            if is_completion:
                import threading
                import time

                self._last_completion_time = time.time()
                logger.debug(
                    f"⏰ {self.agent_name} completion detected, will remain visible for {self._completion_reset_delay}s"
                )

                def reset_to_ready():
                    import time

                    time.sleep(self._completion_reset_delay)
                    # Only reset if no newer completion happened
                    if (
                        time.time() - self._last_completion_time
                        >= self._completion_reset_delay - 0.1
                    ):
                        logger.debug(f"🔄 Resetting {self.agent_name} status to ready...")
                        try:
                            import asyncio

                            loop = None
                            try:
                                loop = asyncio.get_running_loop()
                            except RuntimeError:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)

                            if loop and not loop.is_closed():
                                loop.run_until_complete(
                                    self.status_tracker.update_status(
                                        self.agent_name,
                                        status="ready",
                                        current_task=None,
                                        tool_calls=[],
                                    )
                                )
                                logger.debug(f"✅ {self.agent_name} status reset to ready")
                        except Exception as e:
                            logger.warning(f"❌ Failed to reset status for {self.agent_name}: {e}")
                    else:
                        logger.debug(
                            f"⏭️ Skipping reset for {self.agent_name} - newer completion detected"
                        )

                # Run reset in background thread
                reset_thread = threading.Thread(target=reset_to_ready, daemon=True)
                reset_thread.start()

        except Exception as e:
            logger.debug(f"📊 MonitorCallback error for {self.agent_name}: {e}")
            # Simple error update
            self._queue_error_update(str(e))

    def _extract_minimal_step_data(self, memory_step: ActionStep, agent: Any) -> Dict[str, Any]:
        """Extract minimal, reliable data from the ActionStep and agent."""
        step_data = {
            "step_number": getattr(memory_step, "step_number", 0),
            "memory_size": len(agent.memory.steps) if hasattr(agent, "memory") else 0,
            "agent_type": type(agent).__name__,
        }

        # Extract current task (simplified)
        if hasattr(memory_step, "task") and memory_step.task:
            step_data["current_task"] = str(memory_step.task)[:80]  # Shorter truncation

        # Check for errors first (most reliable indicator)
        if hasattr(memory_step, "error") and memory_step.error:
            step_data["status"] = "error"
            step_data["error_message"] = str(memory_step.error)[:200]
            return step_data

        # Simple tool detection
        tool_calls = []
        if hasattr(memory_step, "tool_calls") and memory_step.tool_calls:
            tool_calls = [
                self._simplify_tool_name(str(tc)) for tc in memory_step.tool_calls[:3]
            ]  # Limit to 3
        elif hasattr(memory_step, "code") and memory_step.code:
            tool_calls = self._extract_simple_tools(memory_step.code)

        step_data["tool_calls"] = tool_calls

        # Simple status determination
        step_data["status"] = self._determine_simple_status(step_data, memory_step, agent)

        return step_data

    def _simplify_tool_name(self, tool_call: str) -> str:
        """Convert technical tool names to user-friendly names."""
        tool_mapping = {
            "get_python3_script": "View Code",
            "edit_python3_script": "Edit Code",
            "get_component_info_enhanced": "Inspect Component",
            "get_all_components_enhanced": "List Components",
            "register_bridge_component": "Register Component",
            "list_bridge_components": "List Bridge Parts",
            "geometry_agent": "Geometry Agent",
            "syslogic_agent": "Structure Validator",
            "final_answer": "Complete Task",
            "web_search": "Web Search",
            "visit_webpage": "Visit Page",
        }

        # Extract function name from tool call
        if "(" in tool_call:
            func_name = tool_call.split("(")[0].strip()
        else:
            func_name = tool_call.strip()

        return tool_mapping.get(func_name, func_name.replace("_", " ").title())

    def _extract_simple_tools(self, code: str) -> List[str]:
        """Extract simplified tool calls from code."""
        import re

        tools = []

        # Look for function calls
        pattern = r"(\w+)\s*\("
        matches = re.findall(pattern, code.lower())

        # Filter for known tools
        known_tools = [
            "final_answer",
            "geometry_agent",
            "syslogic_agent",
            "get_python3_script",
            "edit_python3_script",
            "web_search",
        ]

        for match in matches:
            if match in known_tools:
                tools.append(self._simplify_tool_name(match))

        return tools[:3]  # Limit to 3 tools

    def _determine_simple_status(
        self, step_data: Dict[str, Any], memory_step: ActionStep, agent: Any
    ) -> str:
        """Simple, reliable status determination."""
        agent_type = step_data.get("agent_type", "").lower()
        tool_calls = step_data.get("tool_calls", [])
        has_observations = hasattr(memory_step, "observations") and memory_step.observations

        # Check for completion
        if "Complete Task" in tool_calls or "final_answer" in str(tool_calls).lower():
            logger.debug(f"🎯 {self.agent_name} detected completion - tool_calls: {tool_calls}")
            # Try to extract the response from the observations or other fields
            step_data["last_response"] = self._extract_response_content(memory_step)
            return "completed"

        # Agent-specific patterns
        if "triage" in agent_type:
            if any("Agent" in tool for tool in tool_calls):
                return "delegating"
        elif "geometry" in agent_type:
            if any(tool in ["View Code", "Edit Code", "Inspect Component"] for tool in tool_calls):
                return "working" if has_observations else "connecting"
        elif "syslogic" in agent_type:
            if "Structure Validator" in tool_calls or any(
                "validate" in tool.lower() for tool in tool_calls
            ):
                return "validating"

        # General states
        if tool_calls:
            return "working"
        elif hasattr(memory_step, "code") and memory_step.code:
            return "thinking"
        else:
            return "ready"

    def _extract_response_content(self, memory_step: ActionStep) -> Optional[str]:
        """Extract the agent's response content from the memory step."""
        try:
            # Check action_output first - this is where the final response is usually stored
            if hasattr(memory_step, "action_output") and memory_step.action_output:
                action_output = str(memory_step.action_output)

                # Handle different agent response formats
                if self.agent_name == "triage_agent":
                    # For triage agent, extract from "Final answer:" format
                    final_answer_match = action_output.split("Final answer: ")
                    if len(final_answer_match) > 1:
                        clean_answer = final_answer_match[-1].strip()
                        # Remove trailing metadata like [Step X: Duration...]
                        clean_answer = clean_answer.split("[Step")[0].strip()
                        if clean_answer:
                            return clean_answer
                elif "geometry_agent" in self.agent_name or "syslogic_agent" in self.agent_name:
                    # For geometry and syslogic agents, look for structured responses
                    if "### 1. Task outcome" in action_output:
                        return action_output
                    # Also check for clean final answer format
                    if "Here is the final answer from your managed agent" in action_output:
                        # Extract the content after this header
                        parts = action_output.split(
                            "Here is the final answer from your managed agent"
                        )
                        if len(parts) > 1:
                            clean_response = parts[-1].strip()
                            # Remove the agent name part if present
                            if clean_response.startswith("'") and "':" in clean_response:
                                clean_response = clean_response.split("':", 1)[1].strip()
                            return clean_response

                # If structured response found, return it
                if "### 1. Task outcome" in action_output:
                    return action_output

            # Check observations for response content
            if hasattr(memory_step, "observations") and memory_step.observations:
                observations = memory_step.observations
                if isinstance(observations, list) and len(observations) > 0:
                    # Look for the last observation which often contains the response
                    last_obs = observations[-1]
                    if hasattr(last_obs, "content"):
                        content = str(last_obs.content)

                        # Special handling for triage agent's final answer
                        if self.agent_name == "triage_agent":
                            # Extract the clean final answer from final_answer() output
                            final_answer_match = content.split("Final answer: ")
                            if len(final_answer_match) > 1:
                                clean_answer = final_answer_match[-1].strip()
                                # Remove any trailing metadata like [Step X: Duration...]
                                clean_answer = clean_answer.split("[Step")[0].strip()
                                if clean_answer:
                                    return clean_answer

                        # Check if this looks like a structured response
                        if "### 1. Task outcome" in content:
                            return content

                    # Try the observation as string directly
                    obs_str = str(last_obs)

                    # Special handling for triage agent
                    if self.agent_name == "triage_agent":
                        final_answer_match = obs_str.split("Final answer: ")
                        if len(final_answer_match) > 1:
                            clean_answer = final_answer_match[-1].strip()
                            clean_answer = clean_answer.split("[Step")[0].strip()
                            if clean_answer:
                                return clean_answer

                    if "### 1. Task outcome" in obs_str:
                        return obs_str

            # Check if there's a result field
            if hasattr(memory_step, "result") and memory_step.result:
                result_str = str(memory_step.result)

                # Special handling for triage agent
                if self.agent_name == "triage_agent":
                    final_answer_match = result_str.split("Final answer: ")
                    if len(final_answer_match) > 1:
                        clean_answer = final_answer_match[-1].strip()
                        clean_answer = clean_answer.split("[Step")[0].strip()
                        if clean_answer:
                            return clean_answer

                if "### 1. Task outcome" in result_str:
                    return result_str

            # Check the step as a whole string as last resort
            step_str = str(memory_step)

            # Special handling for triage agent
            if self.agent_name == "triage_agent":
                final_answer_match = step_str.split("Final answer: ")
                if len(final_answer_match) > 1:
                    clean_answer = final_answer_match[-1].strip()
                    clean_answer = clean_answer.split("[Step")[0].strip()
                    if clean_answer:
                        return clean_answer

            if "### 1. Task outcome" in step_str:
                return step_str

        except Exception as e:
            logger.debug(f"Error extracting response content: {e}")

        return None

    def _queue_status_update(self, step_data: Dict[str, Any]) -> None:
        """Queue a simple status update (no complex threading)."""
        # Use a simple background task approach
        import threading

        def update_status():
            try:
                # Create a new event loop for this thread if needed
                loop = None
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Simple update
                if loop and not loop.is_closed():
                    loop.run_until_complete(self._simple_status_update(step_data))

            except Exception as e:
                logger.debug(f"📊 Status update failed for {self.agent_name}: {e}")

        # Run in background thread (non-blocking)
        thread = threading.Thread(target=update_status, daemon=True)
        thread.start()

    def _queue_error_update(self, error_message: str) -> None:
        """Queue a simple error update."""
        import threading

        def update_error():
            try:
                loop = None
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                if loop and not loop.is_closed():
                    loop.run_until_complete(
                        self.status_tracker.update_status(
                            self.agent_name, status="error", error_message=error_message
                        )
                    )

            except Exception:
                pass  # Fail silently for monitoring

        thread = threading.Thread(target=update_error, daemon=True)
        thread.start()

    async def _simple_status_update(self, step_data: Dict[str, Any]) -> None:
        """Simple async status update."""
        update_kwargs = {
            "status": step_data.get("status", "working"),
            "step_number": step_data.get("step_number"),
            "memory_size": step_data.get("memory_size", 0),
            "tool_calls": step_data.get("tool_calls", []),
        }

        if "current_task" in step_data:
            update_kwargs["current_task"] = step_data["current_task"]
        if "error_message" in step_data:
            update_kwargs["error_message"] = step_data["error_message"]
        if "last_response" in step_data:
            update_kwargs["last_response"] = step_data["last_response"]

        await self.status_tracker.update_status(self.agent_name, **update_kwargs)


class WebSocketManager:
    """Manages WebSocket connections for real-time status broadcasting."""

    def __init__(self):
        self.connections: Set = set()
        logger.debug("🔌 WebSocketManager initialized")

    async def connect(self, websocket) -> None:
        """Add a new WebSocket connection."""
        await websocket.accept()
        self.connections.add(websocket)
        logger.debug(f"📱 WebSocket connected - {len(self.connections)} total connections")

    def disconnect(self, websocket) -> None:
        """Remove a WebSocket connection."""
        try:
            self.connections.discard(websocket)
            logger.debug(f"📱 WebSocket disconnected - {len(self.connections)} total connections")
        except Exception as e:
            logger.debug(f"📱 Error during WebSocket disconnect: {e}")

    async def broadcast(self, data: Dict[str, Any]) -> None:
        """Broadcast data to all connected WebSocket clients."""
        if not self.connections:
            logger.debug("📡 No WebSocket connections to broadcast to")
            return

        message = {"type": "status_update", "data": data, "timestamp": datetime.now().isoformat()}

        logger.debug(
            f"📡 Broadcasting to {len(self.connections)} WebSocket connections: {list(data.keys())}"
        )

        disconnected = set()

        for connection in self.connections:
            try:
                # Check if connection is still open before sending
                if (
                    hasattr(connection, "client_state") and connection.client_state.value == 3
                ):  # DISCONNECTED
                    disconnected.add(connection)
                    continue

                await connection.send_json(message)
                logger.debug("✅ Sent status update to WebSocket connection")
            except Exception as e:
                # Handle specific WebSocket errors more gracefully
                error_msg = str(e)
                if "websocket.close" in error_msg or "response already completed" in error_msg:
                    logger.debug("🔌 WebSocket already closed, removing from connections")
                elif "connection closed" in error_msg.lower():
                    logger.debug("🔌 WebSocket connection closed by client")
                else:
                    logger.debug(f"⚠️ WebSocket error: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.connections.discard(conn)
            logger.debug("🔌 Removed disconnected WebSocket connection")

        if disconnected:
            logger.debug(f"📱 {len(self.connections)} WebSocket connections remaining")

    def cleanup_stale_connections(self) -> None:
        """Remove stale WebSocket connections."""
        stale_connections = set()

        for connection in self.connections.copy():
            try:
                # Check if connection is still alive
                if (
                    hasattr(connection, "client_state") and connection.client_state.value == 3
                ):  # DISCONNECTED
                    stale_connections.add(connection)
            except Exception:
                stale_connections.add(connection)

        for conn in stale_connections:
            self.connections.discard(conn)

        if stale_connections:
            logger.debug(f"🧹 Cleaned up {len(stale_connections)} stale WebSocket connections")


def create_monitor_callback(agent_name: str, status_tracker: AgentStatusTracker) -> MonitorCallback:
    """Factory function to create a monitor callback for an agent."""
    return MonitorCallback(status_tracker, agent_name)


class RemoteMonitorCallback:
    """Callback that sends updates to a remote monitoring server via HTTP."""

    def __init__(self, agent_name: str, monitoring_url: str = "http://localhost:5000"):
        self.agent_name = agent_name
        self.monitoring_url = monitoring_url.rstrip("/") + "/api/status"
        self.session = None
        self._completion_reset_delay = 10.0  # Reset to ready after 10 seconds
        self._last_completion_time = 0
        logger.debug(f"🌐 Created RemoteMonitorCallback for {agent_name} -> {self.monitoring_url}")

    def _get_session(self):
        """Get or create HTTP session."""
        if self.session is None:
            try:
                import requests

                self.session = requests.Session()
                self.session.timeout = 1.0  # Short timeout
            except ImportError:
                logger.warning("⚠️ requests library not available for remote monitoring")
                return None
        return self.session

    def __call__(self, memory_step, agent) -> None:
        """Called after each agent step - sends status update to remote server."""
        import threading
        import time

        try:
            session = self._get_session()
            if not session:
                return

            # Extract step information similar to MonitorCallback
            step_data = self._extract_step_data(memory_step, agent)

            # Add agent name for the API
            step_data["agent_name"] = self.agent_name

            # Check if this is a completion step
            is_completion = step_data.get("status") == "completed"

            # Send current status to remote monitoring server
            response = session.post(self.monitoring_url, json=step_data, timeout=1.0)

            if response.status_code == 200:
                logger.debug(
                    f"📤 Sent status update for {self.agent_name}: {step_data.get('status')}"
                )
            else:
                logger.debug(f"⚠️ Monitoring server responded with {response.status_code}")

            # If this is a completion, schedule a reset to "ready" after delay
            if is_completion:
                self._last_completion_time = time.time()
                logger.debug(
                    f"⏰ {self.agent_name} (remote) completion detected, will remain visible for {self._completion_reset_delay}s"
                )

                def reset_to_ready():
                    import time

                    time.sleep(self._completion_reset_delay)
                    # Only reset if no newer completion happened
                    if (
                        time.time() - self._last_completion_time
                        >= self._completion_reset_delay - 0.1
                    ):
                        logger.debug(f"🔄 Resetting {self.agent_name} (remote) status to ready...")
                        try:
                            reset_data = {
                                "agent_name": self.agent_name,
                                "status": "ready",
                                "current_task": None,
                                "tool_calls": [],
                            }
                            session.post(self.monitoring_url, json=reset_data, timeout=1.0)
                            logger.debug(f"✅ {self.agent_name} (remote) status reset to ready")
                        except Exception as e:
                            logger.warning(
                                f"❌ Failed to reset remote status for {self.agent_name}: {e}"
                            )
                    else:
                        logger.debug(
                            f"⏭️ Skipping remote reset for {self.agent_name} - newer completion detected"
                        )

                # Run reset in background thread
                reset_thread = threading.Thread(target=reset_to_ready, daemon=True)
                reset_thread.start()

        except Exception as e:
            # Fail silently - monitoring is optional
            logger.debug(f"📡 Remote monitoring unavailable for {self.agent_name}: {e}")

    def _extract_step_data(self, memory_step, agent) -> dict:
        """Extract step data similar to MonitorCallback."""
        step_data = {
            "step_number": getattr(memory_step, "step_number", 0),
            "memory_size": len(agent.memory.steps) if hasattr(agent, "memory") else 0,
        }

        # Extract task information
        if hasattr(memory_step, "task"):
            step_data["current_task"] = str(memory_step.task)[:100]

        # Extract code and tool calls
        if hasattr(memory_step, "code") and memory_step.code:
            step_data["tool_calls"] = self._extract_tool_calls_from_code(memory_step.code)

        # Extract tool calls from ToolCallingAgent
        if hasattr(memory_step, "tool_calls") and memory_step.tool_calls:
            step_data["tool_calls"] = [str(tc) for tc in memory_step.tool_calls]

        # Check for errors
        if hasattr(memory_step, "error") and memory_step.error:
            step_data["error_message"] = str(memory_step.error)
            step_data["status"] = "error"
        else:
            # Simple status determination (this will set last_response if completion is detected)
            step_data["status"] = self._determine_simple_status(step_data, memory_step, agent)

        return step_data

    def _extract_tool_calls_from_code(self, code: str) -> list:
        """Extract tool calls from code (simplified version)."""
        tool_calls = []
        import re

        # Look for function calls
        function_pattern = r"(\w+)\s*\("
        matches = re.findall(function_pattern, code)

        # Filter for likely tools
        for match in matches:
            if (
                "_" in match
                or match.endswith(("tool", "search", "get", "edit", "component"))
                or match in ["final_answer", "geometry_agent", "syslogic_agent"]
            ):
                tool_calls.append(match)

        return list(set(tool_calls))  # Remove duplicates

    def _determine_simple_status(self, step_data: dict, memory_step, agent) -> str:
        """Simple status determination for remote monitoring."""
        tool_calls = step_data.get("tool_calls", [])
        agent_type = type(agent).__name__.lower()

        # Check for completion
        if any("final_answer" in str(tool) for tool in tool_calls):
            logger.debug(
                f"🎯 {self.agent_name} (remote) detected completion - tool_calls: {tool_calls}"
            )
            # Try to extract response content for remote monitoring
            step_data["last_response"] = self._extract_response_content_remote(memory_step)
            return "completed"

        # Agent-specific patterns
        if "triage" in agent_type:
            if any("_agent" in str(tool) for tool in tool_calls):
                return "delegating"
        elif "geometry" in agent_type:
            if any("component" in str(tool) or "script" in str(tool) for tool in tool_calls):
                return "working"
        elif "syslogic" in agent_type:
            if any("validate" in str(tool) or "check" in str(tool) for tool in tool_calls):
                return "validating"

        # Default states
        if tool_calls:
            return "tool_calling"
        else:
            return "ready"

    def _extract_response_content_remote(self, memory_step) -> Optional[str]:
        """Extract response content for remote monitoring."""
        try:
            # Check action_output first - this is where the final response is usually stored
            if hasattr(memory_step, "action_output") and memory_step.action_output:
                action_output = str(memory_step.action_output)

                # Handle different agent response formats
                if self.agent_name == "triage_agent":
                    # For triage agent, extract from "Final answer:" format
                    final_answer_match = action_output.split("Final answer: ")
                    if len(final_answer_match) > 1:
                        clean_answer = final_answer_match[-1].strip()
                        # Remove trailing metadata like [Step X: Duration...]
                        clean_answer = clean_answer.split("[Step")[0].strip()
                        if clean_answer:
                            return clean_answer
                elif "geometry_agent" in self.agent_name or "syslogic_agent" in self.agent_name:
                    # For geometry and syslogic agents, look for structured responses
                    if "### 1. Task outcome" in action_output:
                        return action_output
                    # Also check for clean final answer format
                    if "Here is the final answer from your managed agent" in action_output:
                        # Extract the content after this header
                        parts = action_output.split(
                            "Here is the final answer from your managed agent"
                        )
                        if len(parts) > 1:
                            clean_response = parts[-1].strip()
                            # Remove the agent name part if present
                            if clean_response.startswith("'") and "':" in clean_response:
                                clean_response = clean_response.split("':", 1)[1].strip()
                            return clean_response

                # If structured response found, return it
                if "### 1. Task outcome" in action_output:
                    return action_output

            # Similar to the local version but adapted for remote
            if hasattr(memory_step, "observations") and memory_step.observations:
                observations = memory_step.observations
                if isinstance(observations, list) and len(observations) > 0:
                    last_obs = observations[-1]
                    if hasattr(last_obs, "content"):
                        content = str(last_obs.content)

                        # Special handling for triage agent's final answer
                        if self.agent_name == "triage_agent":
                            final_answer_match = content.split("Final answer: ")
                            if len(final_answer_match) > 1:
                                clean_answer = final_answer_match[-1].strip()
                                clean_answer = clean_answer.split("[Step")[0].strip()
                                if clean_answer:
                                    return clean_answer

                        if "### 1. Task outcome" in content:
                            return content

                    obs_str = str(last_obs)

                    # Special handling for triage agent
                    if self.agent_name == "triage_agent":
                        final_answer_match = obs_str.split("Final answer: ")
                        if len(final_answer_match) > 1:
                            clean_answer = final_answer_match[-1].strip()
                            clean_answer = clean_answer.split("[Step")[0].strip()
                            if clean_answer:
                                return clean_answer

                    if "### 1. Task outcome" in obs_str:
                        return obs_str

            # Check result field
            if hasattr(memory_step, "result") and memory_step.result:
                result_str = str(memory_step.result)

                # Special handling for triage agent
                if self.agent_name == "triage_agent":
                    final_answer_match = result_str.split("Final answer: ")
                    if len(final_answer_match) > 1:
                        clean_answer = final_answer_match[-1].strip()
                        clean_answer = clean_answer.split("[Step")[0].strip()
                        if clean_answer:
                            return clean_answer

                if "### 1. Task outcome" in result_str:
                    return result_str

            # Check the whole step as last resort
            step_str = str(memory_step)

            # Special handling for triage agent
            if self.agent_name == "triage_agent":
                final_answer_match = step_str.split("Final answer: ")
                if len(final_answer_match) > 1:
                    clean_answer = final_answer_match[-1].strip()
                    clean_answer = clean_answer.split("[Step")[0].strip()
                    if clean_answer:
                        return clean_answer

            if "### 1. Task outcome" in step_str:
                return step_str

        except Exception as e:
            logger.debug(f"Error extracting remote response content: {e}")

        return None


def create_remote_monitor_callback(
    agent_name: str, monitoring_url: str = "http://localhost:5000"
) -> RemoteMonitorCallback:
    """Factory function to create a remote monitor callback for an agent."""
    return RemoteMonitorCallback(agent_name, monitoring_url)


def create_agent_monitor_system() -> tuple[AgentStatusTracker, WebSocketManager]:
    """Create a complete agent monitoring system."""
    status_tracker = AgentStatusTracker()
    websocket_manager = WebSocketManager()

    # Connect websocket manager to status tracker
    status_tracker.add_callback(websocket_manager.broadcast)

    logger.debug("🎯 Agent monitoring system created successfully")
    return status_tracker, websocket_manager


def enable_monitoring():
    """Enable monitoring globally for all MonitorCallback instances."""
    MonitorCallback.monitoring_enabled = True
    logger.debug("📊 Agent monitoring enabled")


def disable_monitoring():
    """Disable monitoring globally for all MonitorCallback instances."""
    MonitorCallback.monitoring_enabled = False
    logger.debug("📊 Agent monitoring disabled")


def is_monitoring_enabled() -> bool:
    """Check if monitoring is currently enabled."""
    return MonitorCallback.monitoring_enabled
