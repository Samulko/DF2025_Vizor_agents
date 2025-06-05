"""Test script to check Rich color rendering."""
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

def test_colors():
    console = Console()
    
    print("=== Testing Rich Color Support ===")
    
    # Test basic Rich functionality
    console.print("1. Basic Rich print test")
    console.print("[bold red]This should be bold red[/bold red]")
    console.print("[blue]This should be blue[/blue]")
    console.print("[green]This should be green[/green]")
    console.print("[yellow]This should be yellow[/yellow]")
    console.print()
    
    # Test agent colors
    console.print("2. Agent color test:")
    console.print("[bold blue]🔵 Triage Agent[/bold blue] - Should be blue")
    console.print("[bold green]🟢 Geometry Agent[/bold green] - Should be green") 
    console.print("[bold red]🔴 Material Agent[/bold red] - Should be red")
    console.print("[bold orange1]🟠 Structural Agent[/bold orange1] - Should be orange")
    console.print()
    
    # Test console capabilities
    console.print("3. Console capabilities:")
    console.print(f"Color system: {console.color_system}")
    console.print(f"Is terminal: {console.is_terminal}")
    console.print(f"Size: {console.size}")
    console.print(f"Encoding: {console.file.encoding if hasattr(console.file, 'encoding') else 'unknown'}")
    console.print()
    
    # Test with Panel
    console.print("4. Panel test:")
    console.print(Panel(
        "[bold green]This panel should have colors[/bold green]",
        border_style="blue",
        title="Test Panel"
    ))
    
    # Test forcing color
    console.print("5. Forced color test:")
    forced_console = Console(force_terminal=True, color_system="truecolor")
    forced_console.print("[bold red]FORCED: This should definitely be red[/bold red]")

if __name__ == "__main__":
    test_colors()