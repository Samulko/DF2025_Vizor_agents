"""Simple enhanced CLI with clear input/output and agent conversation display."""

import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..agents.triage_agent import TriageAgent
from ..api.status_broadcaster import get_broadcaster


class AgentConversationDisplay:
    """Displays agent conversations and status updates."""

    def __init__(self):
        self.console = Console()
        self.conversations: List[Dict[str, any]] = []
        self.agent_statuses: Dict[str, Dict[str, any]] = {
            "triage": {"status": "idle", "message": "Ready", "last_update": None},
            "geometry": {"status": "idle", "message": "Ready", "last_update": None},
            "material": {"status": "idle", "message": "Ready", "last_update": None},
            "structural": {"status": "idle", "message": "Ready", "last_update": None},
        }
        self.broadcaster = get_broadcaster()
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self):
        """Start monitoring agent status updates."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_status, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring agent status updates."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)

    def _monitor_status(self):
        """Monitor status updates from broadcaster."""
        last_message_count = 0
        while self.monitoring:
            # Check for new messages from broadcaster
            current_count = len(self.broadcaster.recent_messages)
            if current_count > last_message_count:
                # Process new messages
                new_messages = self.broadcaster.recent_messages[last_message_count:]
                for message in new_messages:
                    self.update_agent_status(
                        message.agent_name, message.status.value, message.message
                    )
                last_message_count = current_count
            time.sleep(0.2)

    def update_agent_status(self, agent_name: str, status: str, message: str):
        """Update an agent's status and display it."""
        if agent_name in self.agent_statuses:
            old_status = self.agent_statuses[agent_name]["status"]
            self.agent_statuses[agent_name].update(
                {"status": status, "message": message, "last_update": datetime.now()}
            )

            # Display status change
            if status != old_status or status in ["active", "delegating"]:
                self.display_status_update(agent_name, status, message)

    def display_status_update(self, agent_name: str, status: str, message: str):
        """Display a status update."""
        # Agent-specific colors for better visual distinction
        agent_colors = {
            "triage": "blue",  # Blue - coordination/management
            "geometry": "green",  # Green - creation/building
            "material": "red",  # Red - resources/inventory
            "structural": "orange",  # Orange - analysis/engineering
        }

        status_icons = {
            "idle": "⭕",
            "thinking": "🤔",
            "active": "🔄",
            "delegating": "📤",
            "error": "❌",
        }

        # Get agent color, fallback to status-based color
        agent_color = agent_colors.get(agent_name, "white")
        icon = status_icons.get(status, "●")
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Make the agent name bold and colored, status in brackets
        self.console.print(
            f"[dim]{timestamp}[/dim] {icon} [bold {agent_color}]{agent_name.title()}[/bold {agent_color}] [{status.upper()}]: {message}"
        )

    def add_conversation(self, user_input: str, agent_response: str):
        """Add a conversation exchange."""
        self.conversations.append(
            {"timestamp": datetime.now(), "user": user_input, "response": agent_response}
        )

        # Display the conversation
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print()
        self.console.print(f"[dim]{timestamp}[/dim] [bold blue]You:[/bold blue] {user_input}")
        self.console.print(
            f"[dim]{timestamp}[/dim] [bold green]Triage Agent:[/bold green] {agent_response}"
        )
        self.console.print()

    def show_agent_status_table(self):
        """Display current agent status as a table."""
        table = Table(title="Current Agent Status", show_header=True, header_style="bold magenta")
        table.add_column("Agent", width=12)
        table.add_column("Status", width=12)
        table.add_column("Current Task", width=50)
        table.add_column("Last Update", width=12)

        # Agent-specific colors (same as display_status_update)
        agent_colors = {
            "triage": "blue",  # Blue - coordination/management
            "geometry": "green",  # Green - creation/building
            "material": "red",  # Red - resources/inventory
            "structural": "orange",  # Orange - analysis/engineering
        }

        status_colors = {
            "idle": "dim white",
            "thinking": "yellow",
            "active": "bright_green",
            "delegating": "bright_blue",
            "error": "bright_red",
        }

        for agent_name, info in self.agent_statuses.items():
            status = info["status"]
            agent_color = agent_colors.get(agent_name, "white")
            status_color = status_colors.get(status, "white")

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
                Text(agent_name.title(), style=f"bold {agent_color}"),
                Text(status.title(), style=status_color),
                info["message"][:50],
                time_str,
            )

        self.console.print(table)


class SimpleEnhancedCLI:
    """Simple enhanced CLI with clear conversation display."""

    def __init__(self):
        self.console = Console()
        self.triage_agent: Optional[TriageAgent] = None
        self.conversation_display = AgentConversationDisplay()
        self.running = False

        self.shortcuts = {"st": "status", "rs": "reset", "h": "help", "q": "exit", "clear": "clear"}

    def initialize(self):
        """Initialize the CLI with triage agent."""
        self.console.print(
            Panel.fit(
                "[bold blue]Initializing Bridge Design System...[/bold blue]", border_style="blue"
            )
        )

        try:
            self.triage_agent = TriageAgent()
            self.triage_agent.initialize_agent()
            self.conversation_display.start_monitoring()

            self.console.print("[green]✓[/green] System initialized successfully!")
            return True
        except Exception as e:
            self.console.print(f"[red]✗[/red] Initialization failed: {str(e)}")
            return False

    def show_welcome(self):
        """Show welcome message."""
        self.console.clear()
        self.console.print(
            Panel(
                "[bold green]🌉 AR-Assisted Bridge Design System[/bold green]\n\n"
                + "Ready to help you design bridges! You can:\n"
                + "• Type natural language requests about bridge design\n"
                + "• Use shortcuts: 'help', 'status', 'reset', 'clear', 'exit'\n"
                + "• Watch real-time agent interactions below\n\n"
                + "[dim]Agent status updates will appear automatically as you interact[/dim]",
                border_style="green",
                title="Welcome",
            )
        )
        self.console.print()

    def process_command(self, user_input: str) -> tuple[bool, Optional[str]]:
        """Process user command and return (continue, response)."""
        command = user_input.strip().lower()

        # Expand shortcuts
        if command in self.shortcuts:
            command = self.shortcuts[command]

        # Handle special commands
        if command in ["exit", "quit"]:
            return False, "Exiting Bridge Design System..."

        elif command == "reset":
            self.triage_agent.reset_all_agents()
            return True, "🔄 All agents reset successfully."

        elif command == "status":
            self.conversation_display.show_agent_status_table()
            return True, None

        elif command == "clear":
            self.console.clear()
            self.show_welcome()
            return True, None

        elif command == "help":
            return True, self.get_help_text()

        elif command == "":
            return True, None

        else:
            # Regular design request
            return True, None  # Will be processed by triage agent

    def get_help_text(self) -> str:
        """Get help text for available commands."""
        help_panel = Panel(
            "[bold]Available Commands:[/bold]\n\n"
            + "• [bold cyan]exit/quit[/bold cyan] - Exit the system\n"
            + "• [bold cyan]reset[/bold cyan] - Reset all agents\n"
            + "• [bold cyan]status[/bold cyan] - Show current agent status\n"
            + "• [bold cyan]clear[/bold cyan] - Clear screen and show welcome\n"
            + "• [bold cyan]help[/bold cyan] - Show this help\n\n"
            + "[bold]Example Requests:[/bold]\n"
            + '• "I want to create a pedestrian bridge"\n'
            + '• "Create bridge points at 0,0,0 and 100,0,0"\n'
            + '• "Check material availability"\n'
            + '• "Run structural analysis"',
            title="Help",
            border_style="cyan",
        )
        self.console.print(help_panel)
        return None

    def run(self):
        """Run the simple enhanced CLI."""
        if not self.initialize():
            return

        self.running = True
        self.show_welcome()

        try:
            while self.running:
                try:
                    # Clear, simple input prompt
                    user_input = self.console.input("[bold blue]Designer> [/bold blue]").strip()

                    if not user_input:
                        continue

                    # Process command
                    should_continue, command_response = self.process_command(user_input)

                    if not should_continue:
                        self.console.print(f"[yellow]{command_response}[/yellow]")
                        break

                    if command_response:
                        self.console.print(f"[green]System:[/green] {command_response}")
                        continue

                    # Regular design request - show that we're processing
                    self.console.print(
                        f"[dim]{datetime.now().strftime('%H:%M:%S')}[/dim] [bold blue]You:[/bold blue] {user_input}"
                    )
                    self.console.print("[yellow]🤔 Processing your request...[/yellow]")

                    # Process the request
                    response = self.triage_agent.handle_design_request(user_input)

                    # Display the response
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    if response.success:
                        self.console.print(
                            f"[dim]{timestamp}[/dim] [bold green]Triage Agent:[/bold green] {response.message}"
                        )
                    else:
                        self.console.print(
                            f"[dim]{timestamp}[/dim] [bold red]Error:[/bold red] {response.message}"
                        )
                        if response.error:
                            self.console.print(f"[dim]Error Type: {response.error.value}[/dim]")

                    self.console.print()  # Add spacing

                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
                    continue
                except Exception as e:
                    self.console.print(f"[red]Error: {str(e)}[/red]")

        finally:
            self.conversation_display.stop_monitoring()
            self.running = False
            self.console.print("[blue]Thank you for using the Bridge Design System![/blue]")


def run_simple_enhanced_cli():
    """Entry point for simple enhanced CLI."""
    cli = SimpleEnhancedCLI()
    cli.run()
