import subprocess
import json
import re
import os
from abc import ABC, abstractmethod
from rich.console import Console
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

console = Console()

# --- Abstract Base Class for Agent Engines ---
class BaseAgentEngine(ABC):
    @abstractmethod
    def perform_research(self, query: str, max_results: int = 5) -> str:
        pass

    @abstractmethod
    def validate_idea(self, idea: str, audience: str, progress: str, research_data: str, repo_path: str = None) -> str:
        pass

# --- Groq Backend Implementation ---
class GroqEngine(BaseAgentEngine):
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def perform_research(self, query: str, max_results: int = 5) -> str:
        # Simplified: Llama 3 research logic (real search would still need DDGS or similar)
        # For consistency with the plan, we'll use DDGS here as well but processed by Groq if needed
        from ddgs import DDGS
        
        results_text = ""
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=max_results)
                for i, result in enumerate(results):
                    results_text += f"\nResult {i+1}:\n"
                    results_text += f"Title: {result.get('title')}\n"
                    results_text += f"Snippet: {result.get('body')}\n"
                    results_text += f"URL: {result.get('href')}\n"
        except Exception as e:
            results_text = f"Error performing research with DDGS: {e}"
        
        # We could use Groq here to summarize the results
        prompt = f"Summarize the following research data for a startup co-founder:\n\n{results_text}"
        return self._query_groq(prompt)

    def _query_groq(self, prompt: str, system_message: str = "You are an elite AI Co-Founder.") -> str:
        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error querying Groq: {e}"

    def validate_idea(self, idea: str, audience: str, progress: str, research_data: str, repo_path: str = None) -> str:
        prompt = f"""You are an elite AI Co-Founder and Venture Validator.
Critically analyze the following vision:
- Vision: {idea}
- Audience: {audience}
- Progress: {progress}

Research Context:
{research_data}

Generate a comprehensive validation report including Executive Summary, Competitive Landscape, Critical Risks (The Roast), USP, and Next Steps.
"""
        return self._query_groq(prompt, "You are a brutal Venture Validator. Be highly critical and data-driven.")

# --- Lightweight Gemini CLI Backend Implementation ---
class LightweightGeminiEngine(BaseAgentEngine):
    def _run_gemini_cli(self, prompt: str, repo_path: str = None) -> str:
        """Helper to run the gemini CLI command."""
        cmd = ["gemini", "-y", "--output-format", "json"]
        if repo_path:
            cmd.extend(["--include-directories", os.path.abspath(repo_path)])
        cmd.extend(["-p", prompt])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            json_match = re.search(r'(\{.*\})', result.stdout, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                return data.get("response", "No response received from Gemini CLI.")
            else:
                return f"Failed to find JSON in Gemini CLI output.\nRaw Output: {result.stdout}"
                
        except subprocess.CalledProcessError as e:
            return f"Gemini CLI command failed with exit code {e.returncode}.\nStderr: {e.stderr}"
        except Exception as e:
            return f"Error communicating with Gemini CLI bridge: {e}\n\nStderr: {getattr(e, 'stderr', 'No stderr available.')}"

    def perform_research(self, query: str, max_results: int = 5) -> str:
        from ddgs import DDGS
        results_text = ""
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=max_results)
                for i, result in enumerate(results):
                    results_text += f"\nResult {i+1}:\n"
                    results_text += f"Title: {result.get('title')}\n"
                    results_text += f"Snippet: {result.get('body')}\n"
                    results_text += f"URL: {result.get('href')}\n"
        except Exception as e:
            results_text = f"Error performing research with DDGS: {e}"
        return results_text

    def validate_idea(self, idea: str, audience: str, progress: str, research_data: str, repo_path: str = None) -> str:
        prompt = f"""You are an elite AI Co-Founder and Venture Validator.
Your job is to critically analyze any business idea.
**The Vision:** {idea}
**Target Audience:** {audience}
**Current Progress:** {progress}

**Market Research Data:**
{research_data}

Please generate a comprehensive, structured validation report in Markdown format.
"""
        return self._run_gemini_cli(prompt, repo_path)

# --- AgentManager for switching between engines ---
class AgentManager:
    def __init__(self, default_engine: str = "groq"):
        self.engines = {
            "lightweight": LightweightGeminiEngine(),
            "groq": GroqEngine(),
        }
        self._current_engine_name = default_engine
        if default_engine not in self.engines:
            self._current_engine_name = "lightweight"
        
    @property
    def current_engine(self) -> BaseAgentEngine:
        return self.engines[self._current_engine_name]

    def set_engine(self, engine_name: str):
        if engine_name not in self.engines:
            raise ValueError(f"Unknown agent engine: {engine_name}")
        self._current_engine_name = engine_name
        console.print(f"[bold green]Switched to agent engine: {engine_name}[/bold green]")

    def get_available_engines(self) -> list[str]:
        return list(self.engines.keys())

# Example usage
if __name__ == "__main__":
    agent_manager = AgentManager()
    console.print(f"Current engine: {agent_manager._current_engine_name}")
