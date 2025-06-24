"""Enhanced CLI interface with Rich formatting and real-time status display."""
from datetime import datetime
from typing import Dict, List, Optional

from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..agents.triage_agent import TriageAgent
from ..api.status_broadcaster import get_broadcaster


class DesignStateDisplay:
    """Manages the visual representation of the bridge design state."""
    
    def __init__(self):
        self.design_state = {
            "current_step": "initial",
            "bridge_type": None,
            "start_point": None,
            "end_point": None,
            "materials_checked": False,
            "structural_validated": False,
            "progress": 0
        }
    
    def update_state(self, updates: Dict[str, any]):
        """Update the design state."""
        self.design_state.update(updates)
    
    def render_ascii_bridge(self) -> str:
        """Render a simple ASCII representation of bridge progress."""
        if self.design_state["bridge_type"] is None:
            return "No bridge design started"
        
        progress = self.design_state.get("progress", 0)
        
        if progress < 25:
            return """
    [No bridge points set]
    """
        elif progress < 50:
            return """
    Point A ●                     ● Point B
            |                     |
    """
        elif progress < 75:
            return """
    Point A ●═══════════════════● Point B
            |                     |
            |     Bridge Span     |
    """
        else:
            return """
    Point A ●═══════════════════● Point B
            ║                     ║
            ║   ╔═══════════╗     ║
            ║   ║  Materials ║     ║
            ║   ║  ✓ Checked ║     ║
            ║   ╚═══════════╝     ║
    """
    
    def get_progress_percentage(self) -> int:
        """Calculate overall design progress."""
        progress = 0
        if self.design_state["bridge_type"]:
            progress += 20
        if self.design_state["start_point"]:
            progress += 20
        if self.design_state["end_point"]:
            progress += 20
        if self.design_state["materials_checked"]:
            progress += 20
        if self.design_state["structural_validated"]:
            progress += 20
        return progress


class AgentStatusDisplay:
    """Manages the visual representation of agent statuses."""
    
    def __init__(self):
        self.agent_statuses: Dict[str, Dict[str, any]] = {
            "triage": {"status": "idle", "message": "Ready", "last_update": None},
            "geometry": {"status": "idle", "message": "Ready", "last_update": None},
            "material": {"status": "idle", "message": "Ready", "last_update": None},
            "structural": {"status": "idle", "message": "Ready", "last_update": None}
        }
    
    def update_agent_status(self, agent_name: str, status: str, message: str):
        """Update an agent's status."""
        if agent_name in self.agent_statuses:
            self.agent_statuses[agent_name].update({
                "status": status,
                "message": message,
                "last_update": datetime.now()
            })
    
    def render_agent_table(self) -> Table:
        """Render agent status as a Rich table."""
        table = Table(title="Agent Status", show_header=True, header_style="bold magenta")
        table.add_column("Agent", style="cyan", width=12)
        table.add_column("Status", width=12)
        table.add_column("Current Task", width=40)
        table.add_column("Last Update", width=12)
        
        status_colors = {
            "idle": "dim white",
            "thinking": "yellow",
            "active": "green",
            "delegating": "blue",
            "error": "red"
        }
        
        for agent_name, info in self.agent_statuses.items():
            status = info["status"]
            color = status_colors.get(status, "white")
            
            # Add status indicator
            if status == "active":
                status_text = "🔄 " + status.title()
            elif status == "thinking":
                status_text = "🤔 " + status.title()
            elif status == "delegating":
                status_text = "📤 " + status.title()
            elif status == "error":
                status_text = "❌ " + status.title()
            else:
                status_text = "⭕ " + status.title()
            
            last_update = info["last_update"]
            if last_update:
                time_diff = (datetime.now() - last_update).total_seconds()
                if time_diff < 60:
                    time_str = f"{int(time_diff)}s ago"
                else:
                    time_str = f"{int(time_diff/60)}m ago"
            else:
                time_str = "Never"
            
            table.add_row(
                agent_name.title(),
                Text(status_text, style=color),
                info["message"][:40],
                time_str
            )
        
        return table


class CommandProcessor:
    """Handles enhanced command processing with shortcuts."""
    
    def __init__(self, triage_agent: TriageAgent):
        self.triage_agent = triage_agent
        self.command_history: List[str] = []
        self.shortcuts = {
            "st": "status",
            "rs": "reset", 
            "h": "help",
            "q": "exit",
            "ds": "design_state"
        }
    
    def process_command(self, user_input: str) -> tuple[bool, Optional[str]]:
        """Process user command and return (continue, response).
        
        Returns:
            Tuple of (should_continue, response_message)
        """
        command = user_input.strip().lower()
        
        # Expand shortcuts
        if command in self.shortcuts:
            command = self.shortcuts[command]
        
        # Handle special commands
        if command == "exit" or command == "quit":
            return False, "Exiting Bridge Design System..."
        
        elif command == "reset":
            self.triage_agent.reset_all_agents()
            return True, "🔄 All agents reset successfully."
        
        elif command == "status":
            status = self.triage_agent.get_agent_status()
            response = "📊 Agent Status Summary:\n"
            for agent, info in status.items():
                response += f"  • {agent.title()}: Steps={info['step_count']}, Active={info['initialized']}\n"
            return True, response
        
        elif command == "design_state":
            state = self.triage_agent.design_state
            response = "🏗️  Current Design State:\n"
            for key, value in state.items():
                response += f"  • {key}: {value}\n"
            return True, response
        
        elif command == "help":
            return True, self.get_help_text()
        
        elif command == "":
            return True, None
        
        else:
            # Regular design request
            self.command_history.append(user_input)
            return True, None  # Will be processed by triage agent
    
    def get_help_text(self) -> str:
        """Get help text for available commands."""
        return """
🚀 Available Commands:
  • [bold]exit/quit (q)[/bold] - Exit the system
  • [bold]reset (rs)[/bold] - Reset all agents  
  • [bold]status (st)[/bold] - Show agent status
  • [bold]design_state (ds)[/bold] - Show current design state
  • [bold]help (h)[/bold] - Show this help
  
  Or simply type your bridge design request!
  Example: "I want to create a pedestrian bridge"
        """


class EnhancedCLI:
    """Main enhanced CLI interface with Rich formatting."""
    
    def __init__(self):
        self.console = Console()
        self.triage_agent: Optional[TriageAgent] = None
        self.design_display = DesignStateDisplay()
        self.agent_display = AgentStatusDisplay()
        self.command_processor: Optional[CommandProcessor] = None
        self.broadcaster = get_broadcaster()
        self.running = False
        
        # Set up status update handler
        self._setup_status_handler()
    
    def _setup_status_handler(self):
        """Set up handler for status updates from broadcaster."""
        # We'll poll the broadcaster for updates in the display loop
        pass
    
    def initialize(self):
        """Initialize the CLI with triage agent."""
        self.console.print(Panel.fit(
            "[bold blue]Initializing Bridge Design System...[/bold blue]",
            border_style="blue"
        ))
        
        try:
            self.triage_agent = TriageAgent()
            self.triage_agent.initialize_agent()
            self.command_processor = CommandProcessor(self.triage_agent)
            
            self.console.print("[green]✓[/green] System initialized successfully!")
            return True
        except Exception as e:
            self.console.print(f"[red]✗[/red] Initialization failed: {str(e)}")
            return False
    
    def create_main_layout(self) -> Layout:
        """Create the main display layout."""
        layout = Layout()
        
        layout.split_row(
            Layout(name="main", ratio=2),
            Layout(name="sidebar", ratio=1)
        )
        
        layout["main"].split_column(
            Layout(name="header", size=3),
            Layout(name="chat", ratio=1),
            Layout(name="input", size=3)
        )
        
        layout["sidebar"].split_column(
            Layout(name="agents", ratio=1),
            Layout(name="design", ratio=1)
        )
        
        return layout
    
    def update_layout(self, layout: Layout, last_response: Optional[str] = None):
        """Update the layout with current information."""
        # Header
        layout["header"].update(Panel(
            Align.center(
                Text("🌉 AR-Assisted Bridge Design System", style="bold blue")
            ),
            border_style="blue"
        ))
        
        # Chat area - show last response
        if last_response:
            chat_content = Panel(
                f"[bold green]Triage Agent:[/bold green] {last_response}",
                title="💬 Response",
                border_style="green"
            )
        else:
            chat_content = Panel(
                "[dim]Waiting for your bridge design request...[/dim]",
                title="💬 Chat",
                border_style="dim"
            )
        layout["chat"].update(chat_content)
        
        # Input prompt
        layout["input"].update(Panel(
            "[bold yellow]Designer>[/bold yellow] Type your request (or 'help' for commands)",
            border_style="yellow"
        ))
        
        # Agent status
        layout["agents"].update(Panel(
            self.agent_display.render_agent_table(),
            title="🤖 Agents",
            border_style="cyan"
        ))
        
        # Design state
        design_content = Text()
        design_content.append("Progress: ")
        progress = self.design_display.get_progress_percentage()
        design_content.append(f"{progress}%\n\n", style="bold green")
        design_content.append(self.design_display.render_ascii_bridge())
        
        layout["design"].update(Panel(
            design_content,
            title="🏗️  Design State",
            border_style="magenta"
        ))
    
    def run_interactive(self):
        """Run the interactive CLI mode."""
        if not self.initialize():
            return
        
        self.running = True
        layout = self.create_main_layout()
        last_response = None
        
        self.console.clear()
        self.console.print(Panel.fit(
            "[bold green]🌉 Bridge Design System Ready![/bold green]\n" +
            "Type your bridge design requests or use commands like 'help', 'status', 'reset'",
            border_style="green"
        ))
        
        try:
            with Live(layout, refresh_per_second=2, screen=True) as live:
                while self.running:
                    self.update_layout(layout, last_response)
                    
                    try:
                        # Get user input
                        user_input = self.console.input("\n🔧 ").strip()
                        
                        # Process command
                        should_continue, command_response = self.command_processor.process_command(user_input)
                        
                        if not should_continue:
                            self.console.print(command_response)
                            break
                        
                        if command_response:
                            last_response = command_response
                            continue
                        
                        if user_input:  # Regular design request
                            self.console.print("[yellow]Processing...[/yellow]")
                            
                            # Update agent status to show processing
                            self.agent_display.update_agent_status("triage", "thinking", f"Analyzing: {user_input[:30]}...")
                            
                            # Process the request
                            response = self.triage_agent.handle_design_request(user_input)
                            
                            if response.success:
                                last_response = response.message
                                # Update design state if provided
                                if response.data and "design_state" in response.data:
                                    self.design_display.update_state(response.data["design_state"])
                            else:
                                last_response = f"❌ Error: {response.message}"
                            
                            # Reset agent status
                            self.agent_display.update_agent_status("triage", "idle", "Ready for next task")
                        
                    except KeyboardInterrupt:
                        self.console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
                        continue
                    except Exception as e:
                        last_response = f"❌ Unexpected error: {str(e)}"
                        self.console.print(f"[red]Error: {e}[/red]")
        
        finally:
            self.running = False
            self.console.print("\n[blue]Thank you for using the Bridge Design System![/blue]")
    
    def run_simple_mode(self):
        """Run simple mode without live layout (fallback)."""
        if not self.initialize():
            return
        
        self.console.print("\n" + "="*60)
        self.console.print("[bold blue]AR-Assisted Bridge Design System[/bold blue]")
        self.console.print("="*60)
        self.console.print("\nType 'exit' to quit, 'reset' to clear conversation")
        self.console.print("Type 'status' to see agent status, 'help' for commands\n")
        
        while True:
            try:
                user_input = self.console.input("\n[bold blue]Designer>[/bold blue] ").strip()
                
                should_continue, command_response = self.command_processor.process_command(user_input)
                
                if not should_continue:
                    self.console.print(command_response)
                    break
                
                if command_response:
                    self.console.print(command_response)
                    continue
                
                if user_input:
                    self.console.print("\n[yellow]Processing...[/yellow]")
                    response = self.triage_agent.handle_design_request(user_input)
                    
                    if response.success:
                        self.console.print(f"\n[bold green]Triage Agent>[/bold green] {response.message}")
                    else:
                        self.console.print(f"\n[red]Error:[/red] {response.message}")
                        if response.error:
                            self.console.print(f"[red]Error Type:[/red] {response.error.value}")
                            
            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
                continue
            except Exception as e:
                self.console.print(f"\n[red]Error:[/red] {str(e)}")


def run_enhanced_cli(simple_mode: bool = False):
    """Entry point for enhanced CLI mode."""
    cli = EnhancedCLI()
    
    if simple_mode:
        cli.run_simple_mode()
    else:
        try:
            cli.run_interactive()
        except Exception as e:
            print(f"Rich interface failed: {e}")
            print("Falling back to simple mode...")
            cli.run_simple_mode()