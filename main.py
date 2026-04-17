import os
import sys
import datetime
import subprocess
import json
import re
from dotenv import load_dotenv

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.text import Text
from rich.spinner import Spinner

# Updated import to avoid warning
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

# Initialize Rich Console
console = Console()

def check_gemini_cli():
    """Checks if the gemini CLI is installed and authenticated."""
    try:
        # Try running a simple command to check if 'gemini' is in the PATH
        subprocess.run(["gemini", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print(Panel("[bold red]Error: 'gemini' CLI command not found.[/bold red]\n\nPlease make sure the Gemini CLI is installed and in your PATH.", title="Dependency Missing"))
        sys.exit(1)

def perform_research(query: str, max_results: int = 5) -> str:
    """Uses DuckDuckGo to perform web research."""
    results_text = ""
    try:
        with DDGS() as ddgs:
            # Silence the library warning by using the correct method if available, 
            # though the warning comes from the class instantiation itself.
            results = ddgs.text(query, max_results=max_results)
            for i, result in enumerate(results):
                results_text += f"\nResult {i+1}:\n"
                results_text += f"Title: {result.get('title')}\n"
                results_text += f"Snippet: {result.get('body')}\n"
                results_text += f"URL: {result.get('href')}\n"
    except Exception as e:
        results_text = f"Error performing research: {e}"
    return results_text

def validate_idea(idea: str, audience: str, progress: str, research_data: str) -> str:
    """Sends the idea and research to Gemini via the CLI bridge for analysis."""
    
    prompt = f"""You are an elite AI Co-Founder and Venture Validator.
Your job is to critically analyze any business idea, physical product, service, or startup vision. 
Point out major flaws, logistical hurdles, or weak assumptions, identify unique selling propositions (USPs), and provide a concrete execution roadmap.

You have been given the following information by the founder:
**The Vision:** {idea}
**Target Audience:** {audience}
**Current Progress:** {progress}

You also performed the following web research on competitors and market validation:
**Market Research Data:**
{research_data}

Please generate a comprehensive, structured validation report in Markdown format. The report should include:
1. **Executive Summary:** A brutal but fair assessment of the venture's viability.
2. **Competitive Landscape:** Who else is doing this (directly or indirectly)? What are the barriers to entry?
3. **The Roast (Critical Risks):** What could kill this business? Consider logistics, manufacturing, regulations, or market shifts.
4. **Unique Selling Proposition (USP):** How can this founder dominate?
5. **The Blueprint (Execution & Tools):** Recommend specific resources for building (e.g., supply chain, marketing, tech stack, or legal/operational tools).
6. **Next Steps:** 3 concrete actions the founder should take *this week*.

Be highly critical, data-driven, and actionable. Do not be overly polite if the idea has major flaws. Respond ONLY with the Markdown content.
"""
    try:
        # Run the gemini command in headless mode
        result = subprocess.run(
            ["gemini", "--output-format", "json", "-p", prompt],
            capture_output=True,
            text=True,
            check=True
        )
        
        # The output might contain warnings (like MCP issues) before the actual JSON.
        # We find the first occurrence of '{' and the last '}'
        stdout = result.stdout
        json_match = re.search(r'(\{.*\})', stdout, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
            data = json.loads(json_str)
            return data.get("response", "No response received from Gemini CLI.")
        else:
            return f"Failed to find JSON in Gemini CLI output.\nRaw Output: {stdout}"
            
    except Exception as e:
        return f"Error communicating with Gemini CLI bridge: {e}\n\nStderr: {getattr(e, 'stderr', 'No stderr available.')}"

def main():
    check_gemini_cli()
    
    console.print(Panel.fit(
        "[bold cyan]Welcome to AICoFounder CLI (Gemini Bridged)[/bold cyan]\n"
        "[italic]Your brutal, data-driven AI startup partner using your existing login.[/italic]", 
        border_style="cyan"
    ))
    
    console.print("\n[bold]Phase 1: Discovery[/bold]")
    idea = Prompt.ask("[cyan]What is your startup idea?[/cyan]\n[dim](e.g., An AI tool that automatically applies to jobs based on my resume)[/dim]")
    audience = Prompt.ask("\n[cyan]Who is your exact target audience?[/cyan]\n[dim](e.g., Recent college graduates in tech)[/dim]")
    progress = Prompt.ask("\n[cyan]What is your current progress?[/cyan]\n[dim](e.g., Just an idea, built a landing page, have an MVP)[/dim]")
    
    console.print("\n[bold]Phase 2: Deep Research[/bold]")
    research_query = f"{idea} startup competitors products"
    
    with console.status(f"[bold yellow]Scraping the web for '{research_query}'...", spinner="dots"):
        research_data = perform_research(research_query, max_results=10)
    console.print("[green]✓ Research complete.[/green]")
    
    console.print("\n[bold]Phase 3 & 4: Validation, Roasting, & The Blueprint[/bold]")
    with console.status("[bold magenta]Analyzing market gaps and challenging assumptions...", spinner="bouncingBar"):
        validation_report = validate_idea(idea, audience, progress, research_data)
    
    console.print("\n[bold green]✓ Validation complete. Here is your report:[/bold green]\n")
    
    # Print the markdown report
    md = Markdown(validation_report)
    console.print(md)
    
    # Save to file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"validation_report_{timestamp}.md"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(validation_report)
        console.print(f"\n[bold green]Report successfully saved to {filename}[/bold green]")
    except Exception as e:
        console.print(f"\n[bold red]Failed to save report: {e}[/bold red]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]AICoFounder CLI exited.[/yellow]")
        sys.exit(0)
