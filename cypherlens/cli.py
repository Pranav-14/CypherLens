"""
CypherLens CLI - Conversational Search Simplifier with Native Clickable Links, Multi-Turn Chat & Arbitrage.
"""

import sys
import json
import webbrowser
import click
from typing import Optional

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
from rich.markdown import Markdown

from cypherlens.engines.chat_session import CypherChatSession
from cypherlens.engines.currency import CurrencyConverter
from cypherlens.engines.ai_provider import AIProviderManager
from cypherlens.engines.geo_resolver import GeoResolver

console = Console(force_terminal=True, legacy_windows=False)

CYPHER_BANNER = """[bold #00f5d4]
  ██████╗██╗   ██╗██████╗ ██╗  ██╗███████╗██████╗ ██╗     ███████╗███╗   ██╗███████╗
 ██╔════╝╚██╗ ██╔╝██╔══██╗██║  ██║██╔════╝██╔══██╗██║     ██╔════╝████╗  ██║██╔════╝
 ██║      ╚████╔╝ ██████╔╝███████║█████╗  ██████╔╝██║     █████╗  ██╔██╗ ██║███████╗
 ██║       ╚██╔╝  ██╔═══╝ ██╔══██║██╔══╝  ██╔══██╗██║     ██╔══╝  ██║╚██╗██║╚════██║
 ╚██████╗   ██║   ██║     ██║  ██║███████╗██║  ██║███████╗███████╗██║ ╚████║███████║
  ╚═════╝   ╚═╝   ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝[/bold #00f5d4]
        [bold #ffd166]>> Conversational Web Intelligence & Price Radar <<[/bold #ffd166]
"""


def render_chat_turn(response: dict):
    """Renders assistant response cleanly in rich markdown with structured cards if present."""
    content = response.get("content", "")
    struct = response.get("structured_data", {})
    resp_type = response.get("type", "general")

    # Render Markdown response text
    console.print(Markdown(content))

    # Render Clarification Options (if any)
    if resp_type == "clarification":
        questions = struct.get("questions", [])
        for q in questions:
            console.print(f"\n[bold #ffd166]{q['label']}[/bold #ffd166]")
            opts_text = "  • " + "   • ".join([f"[cyan]{opt}[/cyan]" for opt in q.get("options", [])])
            console.print(opts_text)

    # Render Deep Links (if any)
    deep_links = struct.get("deep_links", [])
    if deep_links:
        radar_table = Table(title="[bold #ffd166]⚡ 1-Click Direct Pre-Filled Hubs[/bold #ffd166]", show_header=True, header_style="bold cyan", border_style="dim")
        radar_table.add_column("Hub / Matrix", style="bold white", width=30)
        radar_table.add_column("Direct Hyperlink (Click to Open)", style="cyan")
        radar_table.add_column("Type", style="dim yellow", justify="center")

        for dl in deep_links:
            clickable_url = f"[link={dl['url']}]{dl['url'][:62]}...[/link]"
            radar_table.add_row(dl['title'], clickable_url, f"[{dl.get('badge', 'Direct Hub')}]")
        
        console.print(radar_table)


@click.command(help="CypherLens - Conversational Search Simplifier and Price Radar")
@click.argument("query", required=False)
@click.option("--region", "-r", type=click.Choice(["auto", "de", "in", "us", "uk"]), default="auto", help="Geographic region (de=Germany, in=India, us=USA, uk=UK)")
@click.option("--currency", "-c", default="EUR", help="Display currency code (EUR, INR, USD, GBP)")
@click.option("--web", is_flag=True, help="Launch the CypherLens Web Dashboard")
@click.option("--port", default=8000, help="Port for the web server (default 8000)")
def main(query: Optional[str], region: str, currency: str, web: bool, port: int):
    # Launch Web Server if requested
    if web:
        from cypherlens.web_app import start_server
        console.print(CYPHER_BANNER)
        console.print(f"[bold #00f5d4]Initializing CypherLens Web Dashboard on http://localhost:{port}...[/bold #00f5d4]")
        webbrowser.open(f"http://localhost:{port}")
        start_server(port=port)
        return

    session = CypherChatSession(region=region, currency=currency)

    # One-shot direct query
    if query:
        with console.status(f"[bold #00f5d4]Analyzing & scouting for '{query}'...[/bold #00f5d4]", spinner="dots"):
            resp = session.process_message(query)
        render_chat_turn(resp)
        return

    # Interactive Conversational REPL Mode
    console.print(CYPHER_BANNER)
    cfg = AIProviderManager.load_config()
    provider_status = f"[bold green]{cfg.get('provider', 'zero_key').upper()}[/bold green]" if cfg.get("api_key") else "[dim yellow]Zero-Key (Free Mode)[/dim yellow]"
    console.print(f"[dim]AI Provider: {provider_status} | Region: [bold cyan]{session.region.upper()}[/bold cyan] | Currency: [bold #06d6a0]{session.display_currency}[/bold #06d6a0][/dim]")
    console.print("[dim]Commands: [bold]/region <de|in|us|uk>[/bold], [bold]/currency <EUR|INR|USD>[/bold], [bold]/key <gemini_key>[/bold], [bold]/clear[/bold], [bold]exit[/bold][/dim]\n")

    while True:
        try:
            user_input = Prompt.ask(f"[bold #00f5d4]cypherlens ({session.region.upper()}|{session.display_currency})[/bold #00f5d4] [dim]>[/dim]")
            if not user_input or user_input.strip() == "":
                continue
            
            clean_cmd = user_input.strip()
            if clean_cmd.lower() in ["exit", "quit", "q"]:
                console.print("[bold #ffd166]Session ended. Goodbye.[/bold #ffd166]")
                break
            elif clean_cmd.lower() == "/clear":
                session.reset()
                console.print("[bold green]✓ Session memory cleared.[/bold green]\n")
                continue
            elif clean_cmd.lower().startswith("/region "):
                new_reg = clean_cmd.split(" ")[1].strip().lower()
                if new_reg in ["auto", "de", "in", "us", "uk"]:
                    session.set_region(new_reg)
                    console.print(f"[bold green]✓ Region switched to: {new_reg.upper()}[/bold green]\n")
                continue
            elif clean_cmd.lower().startswith("/currency "):
                new_curr = clean_cmd.split(" ")[1].strip().upper()
                session.set_currency(new_curr)
                console.print(f"[bold green]✓ Display currency switched to: {new_curr}[/bold green]\n")
                continue
            elif clean_cmd.lower().startswith("/key "):
                key_val = clean_cmd.split(" ")[1].strip()
                AIProviderManager.save_config("gemini", api_key=key_val)
                console.print("[bold green]✓ Google Gemini API key saved successfully![/bold green]\n")
                continue
            elif clean_cmd.lower() in ["web", "ui", "dashboard"]:
                from cypherlens.web_app import start_server
                webbrowser.open(f"http://localhost:{port}")
                start_server(port=port)
                break

            with console.status("[bold #00f5d4]Scouting & analyzing...[/bold #00f5d4]", spinner="dots"):
                res = session.process_message(user_input)
            
            render_chat_turn(res)
            console.print("\n" + "─" * 60 + "\n")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold #ffd166]Session ended. Exiting.[/bold #ffd166]")
            break


if __name__ == "__main__":
    main()
