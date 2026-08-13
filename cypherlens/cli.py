"""
CypherLens CLI - Terminal Search Simplifier with Native Clickable Links.
"""

import sys
import json
import webbrowser
import click
from typing import Optional

# Ensure UTF-8 output for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt

from cypherlens.engines.orchestrator import CypherOrchestrator
from cypherlens.engines.base import LensResponse

console = Console(force_terminal=True, legacy_windows=False)

CYPHER_BANNER = """[bold #00f5d4]
  ██████╗██╗   ██╗██████╗ ██╗  ██╗███████╗██████╗ ██╗     ███████╗███╗   ██╗███████╗
 ██╔════╝╚██╗ ██╔╝██╔══██╗██║  ██║██╔════╝██╔══██╗██║     ██╔════╝████╗  ██║██╔════╝
 ██║      ╚████╔╝ ██████╔╝███████║█████╗  ██████╔╝██║     █████╗  ██╔██╗ ██║███████╗
 ██║       ╚██╔╝  ██╔═══╝ ██╔══██║██╔══╝  ██╔══██╗██║     ██╔══╝  ██║╚██╗██║╚════██║
 ╚██████╗   ██║   ██║     ██║  ██║███████╗██║  ██║███████╗███████╗██║ ╚████║███████║
  ╚═════╝   ╚═╝   ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝[/bold #00f5d4]
        [bold #ffd166]>> Real-Time Search Simplifier & Price Radar <<[/bold #ffd166]
"""


def render_response(res: LensResponse, export_md: Optional[str] = None, export_json: bool = False):
    """Renders structured scout results with Rich terminal panels and clickable links."""
    if export_json:
        console.print_json(res.model_dump_json())
        return

    # Header Panel
    cat_badges = {
        "flight": "✈ FLIGHT RADAR",
        "amazon": "📦 AMAZON & DEALS",
        "tech": "💻 TECH & HARDWARE",
        "general": "🌐 WEB SEARCH"
    }
    cat_title = cat_badges.get(res.detected_category, "🔍 WEB SEARCH")
    
    header_text = Text()
    header_text.append(f"Target: ", style="bold white")
    header_text.append(f'"{res.query}"', style="bold #00f5d4")
    header_text.append(f"  |  Lens: ", style="bold white")
    header_text.append(f"{cat_title}", style="bold #ffd166")
    header_text.append(f"  |  Latency: ", style="dim")
    header_text.append(f"{res.execution_time_ms}ms\n", style="dim cyan")
    header_text.append(f"{res.summary}", style="italic #e0e0e0")

    console.print(Panel(header_text, border_style="#00f5d4", title="[bold #00f5d4]CYPHERLENS RADAR ACTIVE[/bold #00f5d4]", subtitle="[dim]Hold Ctrl/Cmd + Click any link to open in browser[/dim]"))

    # Render Deep Radar Action Links (if any)
    if res.deep_links:
        radar_table = Table(title="[bold #ffd166]⚡ 1-Click Direct Hubs[/bold #ffd166]", show_header=True, header_style="bold cyan", border_style="dim")
        radar_table.add_column("Hub / Matrix", style="bold white", width=28)
        radar_table.add_column("Direct Hyperlink (Click to Open)", style="cyan")
        radar_table.add_column("Type", style="dim yellow", justify="center")

        for dl in res.deep_links:
            clickable_url = f"[link={dl['url']}]{dl['url'][:60]}...[/link]"
            radar_table.add_row(dl['title'], clickable_url, f"[{dl.get('badge', 'Direct Hub')}]")
        
        console.print(radar_table)
        console.print("")

    # Render Result Cards / Table
    if not res.items:
        console.print("[yellow]No direct results matched this query. Try rephrasing or broadening terms.[/yellow]")
        return

    table = Table(
        title=f"[bold #00f5d4]Scouted Results ({len(res.items)} items)[/bold #00f5d4]",
        show_header=True,
        header_style="bold #00f5d4",
        border_style="#00f5d4",
        show_lines=True
    )
    table.add_column("#", style="dim", width=3, justify="center")
    table.add_column("Product / Result Title", style="bold white", min_width=32)
    table.add_column("Price / Specs", style="bold #06d6a0", width=22)
    table.add_column("Source", style="bold yellow", width=14)
    table.add_column("Action / Direct Link", style="bold cyan", width=24)

    for idx, item in enumerate(res.items, start=1):
        # Specs and Price
        spec_text = []
        if item.price:
            spec_text.append(f"[bold #06d6a0]{item.price}[/bold #06d6a0]")
        if item.rating:
            spec_text.append(f"[yellow]{item.rating}[/yellow]")
        if item.specs:
            spec_text.extend([f"[dim cyan]• {s}[/dim cyan]" for s in item.specs[:2]])
        
        price_specs_content = "\n".join(spec_text) if spec_text else "[dim]N/A[/dim]"

        # Direct Clickable Link Text
        link_display = f"[bold underline cyan link={item.url}]>> Open Deal >>[/bold underline cyan link]"
        
        # Title with snippet
        title_content = Text()
        title_content.append(item.title[:85] + ("..." if len(item.title) > 85 else ""), style="bold white")
        if item.snippet:
            snippet_clean = item.snippet[:120].replace("\n", " ") + ("..." if len(item.snippet) > 120 else "")
            title_content.append(f"\n[dim]{snippet_clean}[/dim]")

        table.add_row(
            str(idx),
            title_content,
            price_specs_content,
            f"[{item.source}]\n[dim]{item.badge or ''}[/dim]",
            link_display
        )

    console.print(table)

    # Optional Export to Markdown
    if export_md:
        with open(export_md, "w", encoding="utf-8") as f:
            f.write(f"# CypherLens Report: {res.query}\n\n")
            f.write(f"- **Category**: {res.detected_category}\n")
            f.write(f"- **Latency**: {res.execution_time_ms}ms\n\n")
            f.write("## 1-Click Direct Hubs\n")
            for dl in res.deep_links:
                f.write(f"- [{dl['title']}]({dl['url']})\n")
            f.write("\n## Results\n\n")
            for it in res.items:
                f.write(f"### [{it.title}]({it.url})\n")
                f.write(f"- **Source**: {it.source} | **Price**: {it.price or 'N/A'}\n")
                if it.specs:
                    f.write(f"- **Specs**: {', '.join(it.specs)}\n")
                f.write(f"- **Summary**: {it.snippet}\n\n")
        console.print(f"[bold green]Report exported successfully to {export_md}[/bold green]")


@click.command(help="CypherLens - Search Simplifier and Web Intelligence Radar")
@click.argument("query", required=False)
@click.option("--category", "-c", type=click.Choice(["auto", "amazon", "flight", "tech", "general"]), default="auto", help="Force specific intelligence lens")
@click.option("--max-results", "-n", default=8, help="Max number of items to return")
@click.option("--export", "-e", type=str, help="Export results to a Markdown file (.md)")
@click.option("--json-output", is_flag=True, help="Output results in JSON format")
@click.option("--web", is_flag=True, help="Launch the CypherLens Web Dashboard")
@click.option("--port", default=8000, help="Port for the web server (default 8000)")
def main(query: Optional[str], category: str, max_results: int, export: Optional[str], json_output: bool, web: bool, port: int):
    # Launch Web Server if requested
    if web:
        from cypherlens.web_app import start_server
        console.print(CYPHER_BANNER)
        console.print(f"[bold #00f5d4]Initializing CypherLens Web Dashboard on http://localhost:{port}...[/bold #00f5d4]")
        webbrowser.open(f"http://localhost:{port}")
        start_server(port=port)
        return

    # If query supplied directly via CLI args
    if query:
        with console.status(f"[bold #00f5d4]Searching web for '{query}'...[/bold #00f5d4]", spinner="dots"):
            response = CypherOrchestrator.scout(query, category=category, max_results=max_results)
        render_response(response, export_md=export, export_json=json_output)
        return

    # Interactive REPL Mode
    console.print(CYPHER_BANNER)
    console.print("[dim cyan]Type any prompt (e.g. 'RTX 4060 laptop under $1000', 'flights from NYC to London', 'Sony headphones amazon') or 'exit' to quit.[/dim cyan]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold #00f5d4]cypherlens[/bold #00f5d4] [dim]>[/dim]")
            if not user_input or user_input.strip() == "":
                continue
            if user_input.lower().strip() in ["exit", "quit", "q"]:
                console.print("[bold #ffd166]Session ended. Goodbye.[/bold #ffd166]")
                break
            if user_input.lower().strip() in ["web", "ui", "dashboard"]:
                from cypherlens.web_app import start_server
                webbrowser.open(f"http://localhost:{port}")
                start_server(port=port)
                break

            with console.status("[bold #00f5d4]Searching...[/bold #00f5d4]", spinner="dots"):
                res = CypherOrchestrator.scout(user_input, category=category, max_results=max_results)
            
            render_response(res)
            console.print("\n" + "─" * 60 + "\n")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold #ffd166]Session ended. Exiting.[/bold #ffd166]")
            break


if __name__ == "__main__":
    main()
