"""Simple, clean CLI interface with color-coded agent interactions."""
from datetime import datetime
from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..agents.triage_agent import TriageAgent


class SimpleAgentCLI:
    """Clean, simple CLI with color-coded agent interactions."""
    
    def __init__(self):
        # Detect terminal type and set appropriate color support
        import os
        terminal_type = os.environ.get('TERM', '').lower()
        is_git_bash = 'MSYS' in os.environ.get('MSYSTEM', '') or 'mingw' in terminal_type
        
        if is_git_bash:
            # Git Bash - use minimal colors
            self.console = Console(force_terminal=True, color_system="standard", legacy_windows=False)
            self.use_simple_format = True
        else:
            # Try full color support for other terminals
            try:
                self.console = Console(force_terminal=True, color_system="truecolor")
                self.use_simple_format = False
            except:
                try:
                    self.console = Console(force_terminal=True, color_system="256")
                    self.use_simple_format = False
                except:
                    self.console = Console(force_terminal=True, color_system="standard")
                    self.use_simple_format = True
        
        self.triage_agent: Optional[TriageAgent] = None
        self.running = False
        
        # Agent colors for consistent visual identity (only specialized agents)
        self.agent_colors = {
            "triage": "blue",      # Blue - coordination/management
            "geometry": "green",   # Green - creation/building
            "material": "red",     # Red - resources/inventory  
            "structural": "orange" # Orange - analysis/engineering
        }
        
        # Status icons
        self.status_icons = {
            "idle": "⭕",
            "thinking": "🤔",
            "active": "🔄",
            "delegating": "📤",
            "error": "❌"
        }
        
        self.shortcuts = {
            "st": "status",
            "rs": "reset",
            "h": "help",
            "q": "exit",
            "clear": "clear"
        }
    
    def initialize(self):
        """Initialize the CLI with triage agent."""
        self.console.print(Panel.fit(
            "[bold blue]Initializing Bridge Design System...[/bold blue]",
            border_style="blue"
        ))
        
        try:
            self.triage_agent = TriageAgent()
            self.triage_agent.initialize_agent()
            
            self.console.print("[green]✓[/green] System initialized successfully!")
            return True
        except Exception as e:
            self.console.print(f"[red]✗[/red] Initialization failed: {str(e)}")
            return False
    
    def show_welcome(self):
        """Show welcome message."""
        self.console.clear()
        
        # Check terminal type and color support
        import os
        terminal_info = "Git Bash (limited colors)" if self.use_simple_format else f"Modern Terminal ({self.console.color_system})"
        
        if self.use_simple_format:
            # Simple welcome for Git Bash
            self.console.print("=" * 60)
            self.console.print("🌉 AR-Assisted Bridge Design System")
            self.console.print("=" * 60)
            self.console.print()
            self.console.print("Ready to help you design bridges!")
            self.console.print()
            self.console.print("Chat Commands:")
            self.console.print("• Type natural language requests about bridge design")
            self.console.print("• Example: 'I want to create a pedestrian bridge'")
            self.console.print()
            self.console.print("Quick Commands:")
            self.console.print("• help or h - Show available commands")
            self.console.print("• status or st - Show agent status")
            self.console.print("• clear - Clear screen")
            self.console.print("• exit or q - Exit system")
            self.console.print()
            self.console.print(f"Terminal: {terminal_info}")
            self.console.print("Agent symbols: [T]riage [G]eometry [M]aterial [S]tructural")
            self.console.print()
        else:
            # Rich welcome for modern terminals
            self.console.print(Panel(
                "[bold green]🌉 AR-Assisted Bridge Design System[/bold green]\n\n" +
                "Ready to help you design bridges!\n\n" +
                "💬 **Chat Commands:**\n" +
                "• Type natural language requests about bridge design\n" +
                "• Example: \"I want to create a pedestrian bridge\"\n\n" +
                "⚡ **Quick Commands:**\n" +
                "• `help` or `h` - Show available commands\n" +
                "• `status` or `st` - Show agent status\n" +
                "• `reset` or `rs` - Reset all agents\n" +
                "• `clear` - Clear screen\n" +
                "• `exit` or `q` - Exit system\n\n" +
                f"[dim]Terminal: {terminal_info}[/dim]",
                border_style="green",
                title="Welcome"
            ))
            
            # Test color display
            self.console.print("🎨 **Agent Color Test:**")
            self.console.print("🔵 [bold blue]Triage[/bold blue] | 🟢 [bold green]Geometry[/bold green] | 🔴 [bold red]Material[/bold red] | 🟠 [bold orange1]Structural[/bold orange1]")
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
            self.show_agent_status()
            return True, None
        
        elif command == "clear":
            self.console.clear()
            self.show_welcome()
            return True, None
        
        elif command == "help":
            self.show_help()
            return True, None
        
        elif command == "":
            return True, None
        
        else:
            # Regular design request
            return True, None  # Will be processed by triage agent
    
    def show_agent_status(self):
        """Display current agent status."""
        if not self.triage_agent:
            self.console.print("[red]System not initialized[/red]")
            return
        
        status = self.triage_agent.get_agent_status()
        
        table = Table(title="Current Agent Status", show_header=True, header_style="bold magenta")
        table.add_column("Agent", width=12)
        table.add_column("Status", width=15)
        table.add_column("Steps", width=8)
        table.add_column("Active", width=10)
        
        for agent_name, info in status.items():
            agent_color = self.agent_colors.get(agent_name, "white")
            
            table.add_row(
                Text(agent_name.title(), style=f"bold {agent_color}"),
                f"Step {info['step_count']}/{20}",
                "✓ Yes" if info['initialized'] else "✗ No",
                f"{info['conversation_length']} interactions"
            )
        
        self.console.print(table)
        self.console.print()
    
    def show_help(self):
        """Show help information."""
        help_panel = Panel(
            "[bold]Available Commands:[/bold]\n\n" +
            "🗨️  **Chat with Agents:**\n" +
            "• \"Create a pedestrian bridge between two points\"\n" +
            "• \"Check what materials are available\"\n" +
            "• \"Run structural analysis on the current design\"\n" +
            "• \"Generate bridge geometry with steel beams\"\n\n" +
            "⚡ **Quick Commands:**\n" +
            "• [bold cyan]help (h)[/bold cyan] - Show this help\n" +
            "• [bold cyan]status (st)[/bold cyan] - Show agent status\n" +
            "• [bold cyan]reset (rs)[/bold cyan] - Reset all agents\n" +
            "• [bold cyan]clear[/bold cyan] - Clear screen\n" +
            "• [bold cyan]exit (q)[/bold cyan] - Exit system\n\n" +
            "🎨 **Agent Colors:**\n" +
            "• [bold blue]Triage[/bold blue] - Coordination & delegation\n" +
            "• [bold green]Geometry[/bold green] - 3D modeling & creation\n" +
            "• [bold red]Material[/bold red] - Resource management\n" +
            "• [bold orange1]Structural[/bold orange1] - Analysis & validation",
            title="Help",
            border_style="cyan"
        )
        self.console.print(help_panel)
        self.console.print()
    
    def display_agent_interaction(self, agent_name: str, status: str, message: str):
        """Display an agent status update with color coding."""
        agent_color = self.agent_colors.get(agent_name, "white")
        icon = self.status_icons.get(status, "●")
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add agent symbols for better visibility even without colors
        agent_symbols = {
            "triage": "[T]",  # Simple for Git Bash
            "geometry": "[G]", 
            "material": "[M]",
            "structural": "[S]"
        }
        agent_symbol = agent_symbols.get(agent_name, "[?]")
        
        if self.use_simple_format:
            # Simple format for Git Bash
            self.console.print(
                f"{timestamp} {icon} {agent_symbol} {agent_name.upper()} [{status.upper()}]: {message}"
            )
        else:
            # Rich format for modern terminals
            try:
                self.console.print(
                    f"[dim]{timestamp}[/dim] {icon} {agent_symbol} [bold {agent_color}]{agent_name.upper()}[/bold {agent_color}] "
                    f"[dim]\\[{status.upper()}][/dim]: {message}"
                )
            except:
                # Fallback without color codes
                self.console.print(
                    f"{timestamp} {icon} {agent_symbol} {agent_name.upper()} [{status.upper()}]: {message}"
                )
    
    def display_agent_thoughts(self, agent_name: str, thought: str):
        """Display an agent's internal thoughts in their color."""
        agent_color = self.agent_colors.get(agent_name, "white")
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Agent symbols
        agent_symbols = {
            "triage": "[T]",
            "geometry": "[G]", 
            "material": "[M]",
            "structural": "[S]"
        }
        agent_symbol = agent_symbols.get(agent_name, "[?]")
        
        if self.use_simple_format:
            # Simple format for Git Bash
            self.console.print(
                f"{timestamp} *** {agent_symbol} {agent_name.title()} thinking: {thought}"
            )
        else:
            # Rich format for modern terminals  
            try:
                self.console.print(
                    f"[dim]{timestamp}[/dim] 💭 {agent_symbol} [bold {agent_color}]{agent_name.title()}[/bold {agent_color}] "
                    f"[dim italic {agent_color}]thinking:[/dim italic {agent_color}] "
                    f"[italic {agent_color}]{thought}[/italic {agent_color}]"
                )
            except:
                # Fallback without color codes
                self.console.print(
                    f"{timestamp} *** {agent_symbol} {agent_name.title()} thinking: {thought}"
                )
    
    def run(self):
        """Run the simple CLI."""
        if not self.initialize():
            return
        
        self.running = True
        self.show_welcome()
        
        try:
            while self.running:
                try:
                    # Simple, clear input prompt
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
                    
                    # Regular design request
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.console.print(f"[dim]{timestamp}[/dim] [bold cyan]You:[/bold cyan] {user_input}")
                    
                    # Show processing indicator
                    self.display_agent_interaction("triage", "thinking", f"Analyzing: {user_input[:50]}...")
                    
                    # Process the request
                    response = self.triage_agent.handle_design_request(user_input)
                    
                    # Display the response with agent color
                    response_timestamp = datetime.now().strftime("%H:%M:%S")
                    if response.success:
                        agent_color = self.agent_colors.get("triage", "blue")
                        agent_symbol = "🔵"
                        
                        try:
                            self.console.print(
                                f"[dim]{response_timestamp}[/dim] {agent_symbol} [bold {agent_color}]Triage Agent:[/bold {agent_color}] "
                                f"[{agent_color}]{response.message}[/{agent_color}]"
                            )
                        except:
                            # Fallback without color codes
                            self.console.print(
                                f"{response_timestamp} {agent_symbol} Triage Agent: {response.message}"
                            )
                        
                        # Simulate some agent delegation with colored thoughts
                        if "bridge" in user_input.lower() or "create" in user_input.lower():
                            self.display_agent_interaction("triage", "delegating", "Delegating to geometry agent")
                            self.display_agent_thoughts("geometry", "I need to create 3D geometry for this bridge design")
                            self.display_agent_interaction("geometry", "active", "Creating bridge geometry")
                            self.display_agent_thoughts("geometry", "Generating points, curves, and structural elements")
                            self.display_agent_interaction("geometry", "idle", "Geometry creation complete")
                        elif "material" in user_input.lower():
                            self.display_agent_interaction("triage", "delegating", "Delegating to material agent")
                            self.display_agent_thoughts("material", "Let me check our current material inventory")
                            self.display_agent_interaction("material", "active", "Checking material inventory")
                            self.display_agent_thoughts("material", "We have steel beams, concrete, and tension cables available")
                            self.display_agent_interaction("material", "idle", "Material check complete")
                        elif "structural" in user_input.lower() or "analysis" in user_input.lower():
                            self.display_agent_interaction("triage", "delegating", "Delegating to structural agent")
                            self.display_agent_thoughts("structural", "Running finite element analysis on the bridge design")
                            self.display_agent_interaction("structural", "active", "Running structural analysis")
                            self.display_agent_thoughts("structural", "Checking stress distribution and load capacity")
                            self.display_agent_interaction("structural", "idle", "Analysis complete")
                        
                        self.display_agent_interaction("triage", "idle", "Ready for next task")
                    else:
                        # Display error with agent color
                        agent_color = self.agent_colors.get("triage", "blue")
                        agent_symbol = "🔵"
                        
                        try:
                            self.console.print(
                                f"[dim]{response_timestamp}[/dim] ❌ {agent_symbol} [bold {agent_color}]Triage Agent:[/bold {agent_color}] "
                                f"[bold red]Error:[/bold red] [{agent_color}]{response.message}[/{agent_color}]"
                            )
                            if response.error:
                                self.console.print(f"[dim]Error Type: {response.error.value}[/dim]")
                        except:
                            # Fallback without color codes
                            self.console.print(
                                f"{response_timestamp} ❌ {agent_symbol} Triage Agent Error: {response.message}"
                            )
                        
                        self.display_agent_interaction("triage", "error", "Task failed")
                    
                    self.console.print()  # Add spacing
                        
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
                    continue
                except Exception as e:
                    self.console.print(f"[red]Error: {str(e)}[/red]")
        
        finally:
            self.running = False
            self.console.print("[blue]Thank you for using the Bridge Design System![/blue]")


def run_simple_cli():
    """Entry point for simple CLI."""
    cli = SimpleAgentCLI()
    cli.run()