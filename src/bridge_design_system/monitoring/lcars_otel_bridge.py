"""Bridge between OpenTelemetry and LCARS monitoring interface."""

import asyncio
import json
from typing import Optional, Sequence
from datetime import datetime

from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.trace import Span, StatusCode

from .agent_monitor import AgentStatusTracker
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class LCARSSpanExporter(SpanExporter):
    """Custom OpenTelemetry exporter that feeds data to LCARS interface."""
    
    def __init__(self, status_tracker: AgentStatusTracker):
        """Initialize with reference to LCARS status tracker."""
        self.status_tracker = status_tracker
        self._shutdown = False
        
    def export(self, spans: Sequence[Span]) -> SpanExportResult:
        """Export OpenTelemetry spans to LCARS monitoring system."""
        if self._shutdown:
            return SpanExportResult.FAILURE
            
        try:
            for span in spans:
                # Convert span to LCARS format
                lcars_data = self._convert_span_to_lcars(span)
                
                if lcars_data:  # Only send if we have valid data
                    # Send to LCARS asynchronously
                    asyncio.create_task(
                        self._send_to_lcars(lcars_data)
                    )
                
            return SpanExportResult.SUCCESS
            
        except Exception as e:
            logger.error(f"❌ Failed to export spans to LCARS: {e}")
            return SpanExportResult.FAILURE
            
    def _convert_span_to_lcars(self, span: Span) -> Optional[dict]:
        """Convert OpenTelemetry span to LCARS format."""
        try:
            attributes = dict(span.attributes or {})
            
            # Extract agent information
            agent_name = attributes.get("agent.name", "unknown")
            if agent_name == "unknown":
                # Try to extract from span name
                span_name_lower = span.name.lower()
                if "triage" in span_name_lower:
                    agent_name = "triage_agent"
                elif "geometry" in span_name_lower:
                    agent_name = "geometry_agent"
                elif "rational" in span_name_lower:
                    agent_name = "rational_agent"
                else:
                    # Skip unknown agents
                    return None
            
            # Extract step information
            step_number = attributes.get("step.number", 0)
            
            # Extract tool information
            tool_calls = []
            if "tool.name" in attributes:
                tool_calls.append(self._simplify_tool_name(attributes["tool.name"]))
            elif "tools.used" in attributes:
                tools_used = attributes["tools.used"]
                if isinstance(tools_used, str):
                    tool_calls = [self._simplify_tool_name(tools_used)]
                elif isinstance(tools_used, list):
                    tool_calls = [self._simplify_tool_name(t) for t in tools_used[:3]]  # Limit to 3
                    
            # Determine status from span
            status = self._determine_status_from_span(span, attributes)
            
            # Extract task/error information
            current_task = None
            if "task.description" in attributes:
                current_task = str(attributes["task.description"])[:100]
            elif span.name and span.name != "unknown":
                current_task = span.name[:100]
                
            error_message = None
            
            if span.status.status_code == StatusCode.ERROR:
                error_message = span.status.description or "Unknown error"
                status = "error"
                
            # Check for completion
            last_response = None
            if attributes.get("step.is_final", False) or "final_answer" in span.name.lower():
                status = "completed"
                last_response = attributes.get("step.result") or attributes.get("output", "Task completed")
                
            # Calculate memory size from span duration or use attribute
            memory_size = attributes.get("memory.size", 0)
            if not memory_size and hasattr(span, 'end_time') and hasattr(span, 'start_time'):
                if span.end_time and span.start_time:
                    # Use duration as proxy for memory activity
                    duration_ms = (span.end_time - span.start_time) // 1_000_000
                    memory_size = min(duration_ms // 100, 100)  # Scale to reasonable memory size
                    
            return {
                "agent_name": agent_name,
                "status": status,
                "step_number": step_number,
                "current_task": current_task,
                "error_message": error_message,
                "tool_calls": tool_calls,
                "last_response": last_response,
                "memory_size": memory_size,
            }
            
        except Exception as e:
            logger.debug(f"🔍 Error converting span to LCARS format: {e}")
            return None
        
    def _determine_status_from_span(self, span: Span, attributes: dict) -> str:
        """Determine LCARS status from span attributes."""
        # Check span name patterns
        span_name_lower = span.name.lower()
        
        # Check for specific operation types
        if "delegation" in span_name_lower or "managed_agent" in span_name_lower:
            return "delegating"
        elif "mcp" in span_name_lower or "connection" in span_name_lower:
            return "mcp_connecting"
        elif "validate" in span_name_lower or "check" in span_name_lower or "rational" in span_name_lower:
            return "validating"
        elif any(tool in span_name_lower for tool in ["tool", "execute", "get_", "edit_"]):
            return "working"
        elif attributes.get("step.thinking", False) or "thinking" in span_name_lower:
            return "thinking"
        elif span.status.status_code == StatusCode.OK and span.end_time:
            return "ready"  # Completed operation
        else:
            return "working"  # Default for active operations
            
    def _simplify_tool_name(self, tool_name: str) -> str:
        """Convert tool names to LCARS-friendly format."""
        # Reuse existing mapping from agent_monitor.py with additions
        tool_mapping = {
            "get_python3_script": "View Code",
            "edit_python3_script": "Edit Code",
            "get_component_info_enhanced": "Inspect Component",
            "get_all_components_enhanced": "List Components",
            "register_bridge_component": "Register Component",
            "list_bridge_components": "List Bridge Parts",
            "geometry_agent": "Geometry Agent",
            "rational_agent": "Rational Agent",
            "syslogic_agent": "Structure Validator",
            "final_answer": "Complete Task",
            "web_search": "Web Search",
            "visit_webpage": "Visit Page",
            # Additional OpenTelemetry specific tools
            "run": "Execute Task",
            "step": "Process Step",
            "tool_call": "Use Tool",
        }
        
        # Clean up tool name
        clean_name = str(tool_name).strip()
        if "(" in clean_name:
            clean_name = clean_name.split("(")[0].strip()
            
        return tool_mapping.get(clean_name, clean_name.replace("_", " ").title())
        
    async def _send_to_lcars(self, data: dict):
        """Send converted data to LCARS status tracker."""
        try:
            agent_name = data.pop("agent_name")
            await self.status_tracker.update_status(agent_name, **data)
            logger.debug(f"📤 Sent OpenTelemetry data to LCARS for {agent_name}")
        except Exception as e:
            logger.debug(f"❌ Failed to send to LCARS: {e}")
            
    def shutdown(self) -> None:
        """Shutdown the exporter."""
        self._shutdown = True
        logger.debug("🔌 LCARS span exporter shutdown")


def create_lcars_exporter(status_tracker: AgentStatusTracker) -> LCARSSpanExporter:
    """
    Factory function to create LCARS span exporter.
    
    Args:
        status_tracker: LCARS status tracker instance
        
    Returns:
        Configured LCARS span exporter
    """
    return LCARSSpanExporter(status_tracker)