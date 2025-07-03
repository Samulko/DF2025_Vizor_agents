"""
Trace logging system for workshop analysis and research documentation.
Saves detailed traces of agent interactions for academic analysis.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from ..config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AgentTrace:
    """Structured trace data for a single agent action."""
    timestamp: str
    session_id: str
    agent_name: str
    step_number: int
    task_description: Optional[str]
    status: str
    tool_calls: List[str]
    response_content: Optional[str]
    error_message: Optional[str]
    duration_seconds: Optional[float]
    token_usage: Optional[Dict[str, int]]
    memory_size: int


@dataclass
class SessionMetadata:
    """Metadata for a workshop session."""
    session_id: str
    start_time: str
    end_time: Optional[str]
    participant_id: Optional[str]
    workshop_group: Optional[str]
    total_interactions: int
    agents_used: List[str]
    session_notes: Optional[str]


class TraceLogger:
    """Logs agent traces to structured files for workshop analysis."""
    
    def __init__(self, logs_dir: str = "workshop_logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.logs_dir / "sessions").mkdir(exist_ok=True)
        (self.logs_dir / "daily").mkdir(exist_ok=True)
        (self.logs_dir / "agents").mkdir(exist_ok=True)
        
        self.current_session_id = self._generate_session_id()
        self.session_start_time = datetime.now().isoformat()
        self.session_traces: List[AgentTrace] = []
        
        logger.info(f"📊 TraceLogger initialized - Session: {self.current_session_id}")
        logger.info(f"📁 Logs directory: {self.logs_dir.absolute()}")
        
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{timestamp}"
    
    def log_agent_trace(
        self,
        agent_name: str,
        step_number: int,
        task_description: Optional[str] = None,
        status: str = "unknown",
        tool_calls: List[str] = None,
        response_content: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        token_usage: Optional[Dict[str, int]] = None,
        memory_size: int = 0
    ):
        """Log a single agent trace."""
        trace = AgentTrace(
            timestamp=datetime.now().isoformat(),
            session_id=self.current_session_id,
            agent_name=agent_name,
            step_number=step_number,
            task_description=task_description,
            status=status,
            tool_calls=tool_calls or [],
            response_content=response_content,
            error_message=error_message,
            duration_seconds=duration_seconds,
            token_usage=token_usage,
            memory_size=memory_size
        )
        
        self.session_traces.append(trace)
        
        # Save to multiple file formats for different analysis needs
        self._save_trace_immediate(trace)
        
        logger.debug(f"📝 Logged trace for {agent_name} step {step_number}")
    
    def _save_trace_immediate(self, trace: AgentTrace):
        """Save trace immediately to files."""
        try:
            # 1. Daily log file (append mode for continuous logging)
            daily_file = self.logs_dir / "daily" / f"{datetime.now().strftime('%Y-%m-%d')}_traces.jsonl"
            with daily_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(trace), ensure_ascii=False) + "\n")
            
            # 2. Agent-specific log file
            agent_file = self.logs_dir / "agents" / f"{trace.agent_name}_traces.jsonl"
            with agent_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(trace), ensure_ascii=False) + "\n")
            
            # 3. Readable summary file (human-readable format)
            summary_file = self.logs_dir / "daily" / f"{datetime.now().strftime('%Y-%m-%d')}_summary.txt"
            with summary_file.open("a", encoding="utf-8") as f:
                f.write(f"\n[{trace.timestamp}] {trace.agent_name} - Step {trace.step_number}\n")
                f.write(f"Status: {trace.status}\n")
                if trace.task_description:
                    f.write(f"Task: {trace.task_description[:200]}...\n")
                if trace.tool_calls:
                    f.write(f"Tools: {', '.join(trace.tool_calls)}\n")
                if trace.response_content:
                    # Truncate for readability
                    content = trace.response_content[:300] + "..." if len(trace.response_content) > 300 else trace.response_content
                    f.write(f"Response: {content}\n")
                if trace.error_message:
                    f.write(f"Error: {trace.error_message}\n")
                if trace.duration_seconds:
                    f.write(f"Duration: {trace.duration_seconds:.2f}s\n")
                f.write("-" * 80 + "\n")
                
        except Exception as e:
            logger.error(f"❌ Failed to save trace: {e}")
    
    def save_session_summary(
        self, 
        participant_id: Optional[str] = None,
        workshop_group: Optional[str] = None,
        session_notes: Optional[str] = None
    ):
        """Save complete session summary."""
        try:
            agents_used = list(set(trace.agent_name for trace in self.session_traces))
            
            metadata = SessionMetadata(
                session_id=self.current_session_id,
                start_time=self.session_start_time,
                end_time=datetime.now().isoformat(),
                participant_id=participant_id,
                workshop_group=workshop_group,
                total_interactions=len(self.session_traces),
                agents_used=agents_used,
                session_notes=session_notes
            )
            
            # Save session file
            session_file = self.logs_dir / "sessions" / f"{self.current_session_id}.json"
            session_data = {
                "metadata": asdict(metadata),
                "traces": [asdict(trace) for trace in self.session_traces]
            }
            
            with session_file.open("w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            # Save workshop analysis file (CSV-like format for easy analysis)
            analysis_file = self.logs_dir / "workshop_analysis.csv"
            
            # Create header if file doesn't exist
            if not analysis_file.exists():
                with analysis_file.open("w", encoding="utf-8") as f:
                    f.write("session_id,start_time,end_time,participant_id,workshop_group,")
                    f.write("total_interactions,agents_used,avg_response_time,errors_count,session_notes\n")
            
            # Calculate statistics
            response_times = [t.duration_seconds for t in self.session_traces if t.duration_seconds]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            errors_count = len([t for t in self.session_traces if t.error_message])
            
            with analysis_file.open("a", encoding="utf-8") as f:
                f.write(f"{metadata.session_id},{metadata.start_time},{metadata.end_time},")
                f.write(f"{metadata.participant_id or ''},{metadata.workshop_group or ''},")
                f.write(f"{metadata.total_interactions},\"{';'.join(agents_used)}\",")
                f.write(f"{avg_response_time:.2f},{errors_count},")
                f.write(f"\"{metadata.session_notes or ''}\"\n")
            
            logger.info(f"✅ Session summary saved: {session_file}")
            logger.info(f"📊 Total interactions: {len(self.session_traces)}")
            logger.info(f"🤖 Agents used: {', '.join(agents_used)}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save session summary: {e}")
    
    def generate_workshop_report(self) -> str:
        """Generate a comprehensive workshop report."""
        try:
            # Read all session files
            sessions_dir = self.logs_dir / "sessions"
            session_files = list(sessions_dir.glob("*.json"))
            
            report_lines = [
                "# Workshop Analysis Report",
                f"Generated: {datetime.now().isoformat()}",
                f"Total Sessions: {len(session_files)}",
                "",
                "## Session Overview",
            ]
            
            total_interactions = 0
            all_agents = set()
            all_participants = set()
            
            for session_file in session_files:
                with session_file.open("r", encoding="utf-8") as f:
                    session_data = json.load(f)
                    metadata = session_data["metadata"]
                    traces = session_data["traces"]
                    
                    total_interactions += len(traces)
                    all_agents.update(metadata["agents_used"])
                    if metadata["participant_id"]:
                        all_participants.add(metadata["participant_id"])
                    
                    report_lines.append(f"- {metadata['session_id']}: {len(traces)} interactions")
            
            report_lines.extend([
                "",
                "## Summary Statistics",
                f"- Total Interactions: {total_interactions}",
                f"- Unique Participants: {len(all_participants)}",
                f"- Agents Used: {', '.join(sorted(all_agents))}",
                "",
                "## Files Generated",
                f"- Session files: {len(session_files)}",
                f"- Daily logs: workshop_logs/daily/",
                f"- Agent logs: workshop_logs/agents/",
                f"- Analysis CSV: workshop_logs/workshop_analysis.csv",
            ])
            
            report_content = "\n".join(report_lines)
            
            # Save report
            report_file = self.logs_dir / "workshop_report.md"
            with report_file.open("w", encoding="utf-8") as f:
                f.write(report_content)
            
            logger.info(f"📋 Workshop report generated: {report_file}")
            return str(report_file)
            
        except Exception as e:
            logger.error(f"❌ Failed to generate workshop report: {e}")
            return ""


# Global trace logger instance
_global_trace_logger: Optional[TraceLogger] = None


def get_trace_logger() -> TraceLogger:
    """Get or create global trace logger."""
    global _global_trace_logger
    if _global_trace_logger is None:
        _global_trace_logger = TraceLogger()
    return _global_trace_logger


def log_agent_interaction(
    agent_name: str,
    step_number: int,
    task_description: Optional[str] = None,
    status: str = "unknown",
    tool_calls: List[str] = None,
    response_content: Optional[str] = None,
    error_message: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    token_usage: Optional[Dict[str, int]] = None,
    memory_size: int = 0
):
    """Convenience function to log agent interaction."""
    logger_instance = get_trace_logger()
    logger_instance.log_agent_trace(
        agent_name=agent_name,
        step_number=step_number,
        task_description=task_description,
        status=status,
        tool_calls=tool_calls,
        response_content=response_content,
        error_message=error_message,
        duration_seconds=duration_seconds,
        token_usage=token_usage,
        memory_size=memory_size
    )


def finalize_workshop_session(
    participant_id: Optional[str] = None,
    workshop_group: Optional[str] = None,
    session_notes: Optional[str] = None
):
    """Finalize and save workshop session."""
    logger_instance = get_trace_logger()
    logger_instance.save_session_summary(
        participant_id=participant_id,
        workshop_group=workshop_group,
        session_notes=session_notes
    )