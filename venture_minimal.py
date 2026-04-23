#!/usr/bin/env python3
import asyncio
import os
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.live import Live
from agent_manager import VentureAgentManager

console = Console()

async def run_minimal():
    console.clear()
    console.print(Panel("[bold emerald]VENTURE CORE[/bold emerald] - [dim]Minimal Analysis Mode[/dim]", border_style="green"))
    
    # 1. Inputs
    name = Prompt.ask("[bold white]Project Name[/bold white]")
    idea = Prompt.ask("[bold white]Core Idea[/bold white]")
    audience = Prompt.ask("[bold white]Target Audience[/bold white]")
    
    console.print("\n[bold green]»[/bold green] Initializing Neural Analysis...")
    
    # 2. Setup Agent
    manager = VentureAgentManager()
    
    # 3. Stream Analysis
    console.print(f"\n[bold emerald]ANALYSIS FOR: {name.upper()}[/bold emerald]\n")
    
    async for chunk in manager.get_analysis_stream(name, idea, audience):
        console.print(chunk, end="", highlight=True)
    
    console.print("\n\n[bold green]✔[/bold green] Analysis Complete. Pushed to venture-web.")

if __name__ == "__main__":
    try:
        asyncio.run(run_minimal())
    except KeyboardInterrupt:
        console.print("\n[red]Analysis Aborted.[/red]")
