import subprocess
import json
import re
import os
from abc import ABC, abstractmethod
from rich.console import Console
from groq import Groq, GroqError
from dotenv import load_dotenv

# Load from .env file
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

    @abstractmethod
    def find_ideas(self, skills: str, interests: str) -> str:
        pass

    @abstractmethod
    def analyze_codebase(self, repo_path: str) -> str:
        pass

# --- Groq Backend Implementation ---
class GroqEngine(BaseAgentEngine):
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = "llama-3.3-70b-versatile"
        self.client = None
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                console.print(f"[bold red]Error initializing Groq client: {e}[/bold red]")

    def is_available(self) -> bool:
        return self.client is not None

    def perform_research(self, query: str, max_results: int = 5) -> str:
        if not self.is_available():
            return "Groq API key is missing. Please set GROQ_API_KEY in your .env file."
        
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
        
        prompt = f"Summarize the following research data for a startup co-founder:\n\n{results_text}"
        return self._query_groq(prompt)

    def _query_groq(self, prompt: str, system_message: str = "You are an elite AI Co-Founder.") -> str:
        if not self.is_available():
            return "Groq Engine is not configured."
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

    def find_ideas(self, skills: str, interests: str) -> str:
        prompt = f"Based on my skills: {skills} and my interests: {interests}, suggest 3 unique, high-potential startup ideas with a brief explanation of why they would work and a potential MVP roadmap for each."
        return self._query_groq(prompt, "You are a creative Startup Strategist.")

    def analyze_codebase(self, repo_path: str) -> str:
        try:
            files = []
            for root, dirs, filenames in os.walk(repo_path):
                dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'venv', '__pycache__']]
                for f in filenames:
                    files.append(os.path.join(root, f))
            
            file_structure = "\n".join(files[:50])
            prompt = f"Analyze the following codebase structure and provide a technical audit focusing on scalability, technical debt, and architectural maturity:\n\n{file_structure}"
            return self._query_groq(prompt, "You are a senior Software Architect and CTO.")
        except Exception as e:
            return f"Error analyzing codebase: {e}"

# --- Lightweight Gemini CLI Backend Implementation ---
class LightweightGeminiEngine(BaseAgentEngine):
    def _run_gemini_cli(self, prompt: str, repo_path: str = None) -> str:
        # Note: This relies on the 'gemini' CLI tool being installed and authenticated
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
            return f"Gemini CLI failed. Error: {e.stderr}"
        except Exception as e:
            return f"Error communicating with Gemini CLI bridge: {e}"

    def perform_research(self, query: str, max_results: int = 5) -> str:
        from ddgs import DDGS
        results_text = ""
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=max_results)
                for i, result in enumerate(results):
                    results_text += f"\nResult {i+1}: {result.get('title')}\nURL: {result.get('href')}\n"
        except Exception as e:
            results_text = f"Error: {e}"
        return results_text

    def validate_idea(self, idea: str, audience: str, progress: str, research_data: str, repo_path: str = None) -> str:
        prompt = f"Validate this idea: {idea} for audience {audience}. Research: {research_data}"
        return self._run_gemini_cli(prompt, repo_path)

    def find_ideas(self, skills: str, interests: str) -> str:
        prompt = f"Suggest startup ideas for skills: {skills} and interests: {interests}"
        return self._run_gemini_cli(prompt)

    def analyze_codebase(self, repo_path: str) -> str:
        prompt = "Analyze this codebase for scalability and technical debt."
        return self._run_gemini_cli(prompt, repo_path)

# --- AgentManager for switching between engines ---
class AgentManager:
    def __init__(self, default_engine: str = "groq"):
        self.engines = {
            "lightweight": LightweightGeminiEngine(),
            "groq": GroqEngine(),
        }
        
        # Fallback logic if groq is requested but not available
        self._current_engine_name = default_engine
        if self._current_engine_name == "groq" and not self.engines["groq"].is_available():
            # Only switch if lightweight is actually viable (inherits gemini CLI)
            self._current_engine_name = "lightweight"
        
        if self._current_engine_name not in self.engines:
            self._current_engine_name = "lightweight"
        
    @property
    def current_engine(self) -> BaseAgentEngine:
        return self.engines[self._current_engine_name]

    def set_engine(self, engine_name: str):
        if engine_name not in self.engines:
            raise ValueError(f"Unknown agent engine: {engine_name}")
        
        if engine_name == "groq" and not self.engines["groq"].is_available():
            console.print("[bold red]Cannot switch to Groq: API key missing in .env[/bold red]")
            return

        self._current_engine_name = engine_name
        console.print(f"[bold green]Switched to agent engine: {engine_name}[/bold green]")

    def get_available_engines(self) -> list[str]:
        return [name for name, eng in self.engines.items() if (name != "groq" or eng.is_available())]
