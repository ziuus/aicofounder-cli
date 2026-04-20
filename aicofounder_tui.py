from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, RichLog, Input, ProgressBar
from textual.containers import Container, VerticalScroll, Horizontal
from textual.binding import Binding
from textual.screen import Screen
from textual.reactive import reactive
from textual.worker import Worker, WorkerState

from state_manager import StateManager
from agent_manager import AgentManager

# --- Phase Screens ---

class IdeaDiscoveryScreen(Screen):
    def __init__(self, state_manager: StateManager, agent_manager: AgentManager, current_project: dict):
        super().__init__()
        self.state_manager = state_manager
        self.agent_manager = agent_manager
        self.current_project = current_project
        self.skills_input = Input(placeholder="Your skills (e.g., Python, Marketing)", id="skills_input", value=self.current_project.get("user_skills", ""))
        self.interests_input = Input(placeholder="Your interests (e.g., Finance, Education)", id="interests_input", value=self.current_project.get("user_interests", ""))

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="idea-discovery-screen-grid"):
            with VerticalScroll(id="idea-discovery-controls"):
                yield Static("[bold green]Reverse Idea Discovery (Gap Finder)[/bold green]", classes="sidebar-title")
                yield Static("Input your skills and interests to find validated startup ideas.", classes="description")
                yield Static("Your Skills:", classes="canvas-label")
                yield self.skills_input
                yield Static("Your Interests:", classes="canvas-label")
                yield self.interests_input
                yield Button("Find Ideas", id="find_ideas_button", variant="primary")
                yield ProgressBar(total=100, show_percentage=True, id="idea_discovery_progress_bar", classes="hidden")
                yield Button("Back to Main", id="back_to_main_button", classes="project-button")
            with VerticalScroll(id="idea-discovery-display"):
                yield Static("[bold blue]Generated Ideas[/bold blue]", classes="sidebar-title")
                yield RichLog(id="generated_ideas_log", wrap=True, highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        if self.current_project.get("generated_ideas"):
            self.query_one("#generated_ideas_log", RichLog).write(self.current_project["generated_ideas"])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "find_ideas_button":
            skills = self.skills_input.value.strip()
            interests = self.interests_input.value.strip()
            if not skills and not interests:
                self.query_one("#generated_ideas_log", RichLog).write("[bold red]Please enter your skills or interests.[/bold red]")
                return
            
            self.query_one("#idea_discovery_progress_bar").remove_class("hidden")
            self.query_one("#generated_ideas_log", RichLog).write(f"[bold cyan]Asking AI for ideas based on your profile...[/bold cyan]\n")
            self.run_worker(self.perform_background_idea_discovery(skills, interests), exclusive=True)
        elif event.button.id == "back_to_main_button":
            self.app.pop_screen()

    async def perform_background_idea_discovery(self, skills: str, interests: str):
        generated_ideas = await self.app.run_in_thread(self.agent_manager.current_engine.find_ideas, skills, interests)
        self.query_one("#generated_ideas_log", RichLog).write(generated_ideas)
        self.query_one("#idea_discovery_progress_bar").add_class("hidden")
        
        self.current_project["generated_ideas"] = generated_ideas
        self.current_project["user_skills"] = skills
        self.current_project["user_interests"] = interests
        self.state_manager.save_project(self.current_project["name"], self.current_project)
        self.query_one("#generated_ideas_log", RichLog).write("\n[bold green]Generated ideas saved to project.[/bold green]")

class ResearchScreen(Screen):
    def __init__(self, state_manager: StateManager, agent_manager: AgentManager, current_project: dict):
        super().__init__()
        self.state_manager = state_manager
        self.agent_manager = agent_manager
        self.current_project = current_project
        self.research_query_input = Input(placeholder="Enter research query", id="research_query_input", value=self.current_project.get("research_query", ""))

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="research-screen-grid"):
            with VerticalScroll(id="research-controls"):
                yield Static("[bold green]Phase 1: Research[/bold green]", classes="sidebar-title")
                yield self.research_query_input
                yield Button("Start Research", id="start_research_button", variant="primary")
                yield ProgressBar(total=100, id="research_progress_bar", classes="hidden")
                yield Button("Back to Main", id="back_to_main_button", classes="project-button")
            with VerticalScroll(id="research-display"):
                yield Static("[bold blue]Research Results[/bold blue]", classes="sidebar-title")
                yield RichLog(id="research_results_log", wrap=True, highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        if self.current_project.get("research_data"):
            self.query_one("#research_results_log", RichLog).write(self.current_project["research_data"])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start_research_button":
            query = self.research_query_input.value.strip()
            if query:
                self.query_one("#research_progress_bar").remove_class("hidden")
                self.query_one("#research_results_log", RichLog).write(f"[bold cyan]Performing autonomous research on: {query}[/bold cyan]\n")
                self.run_worker(self.perform_background_research(query), exclusive=True)
        elif event.button.id == "back_to_main_button":
            self.app.pop_screen()

    async def perform_background_research(self, query: str):
        results = await self.app.run_in_thread(self.agent_manager.current_engine.perform_research, query)
        self.query_one("#research_results_log", RichLog).write(results)
        self.query_one("#research_progress_bar").add_class("hidden")
        self.current_project["research_data"] = results
        self.current_project["research_query"] = query
        self.state_manager.save_project(self.current_project["name"], self.current_project)

class CanvasScreen(Screen):
    def __init__(self, state_manager: StateManager, agent_manager: AgentManager, current_project: dict):
        super().__init__()
        self.state_manager = state_manager
        self.agent_manager = agent_manager
        self.current_project = current_project
        self.idea_input = Input(id="canvas_idea_input", value=self.current_project.get("idea", ""))
        self.audience_input = Input(id="canvas_audience_input", value=self.current_project.get("audience", ""))
        self.problem_input = Input(id="canvas_problem_input", value=self.current_project.get("problem", ""))

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="canvas-screen-grid"):
            with VerticalScroll(id="canvas-form"):
                yield Static("[bold green]Phase 2: Canvas[/bold green]", classes="sidebar-title")
                yield Static("Startup Idea:", classes="canvas-label")
                yield self.idea_input
                yield Static("Target Audience:", classes="canvas-label")
                yield self.audience_input
                yield Static("Problem Statement:", classes="canvas-label")
                yield self.problem_input
                yield Button("Save Canvas", id="save_canvas_button", variant="primary")
                yield Button("Back to Main", id="back_to_main_button", classes="project-button")
            with VerticalScroll(id="canvas-display"):
                yield Static("[bold blue]Canvas Summary[/bold blue]", classes="sidebar-title")
                yield RichLog(id="canvas_summary_log", wrap=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.update_summary()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_canvas_button":
            self.current_project["idea"] = self.idea_input.value.strip()
            self.current_project["audience"] = self.audience_input.value.strip()
            self.current_project["problem"] = self.problem_input.value.strip()
            self.state_manager.save_project(self.current_project["name"], self.current_project)
            self.update_summary()
            self.app.notify("Canvas saved successfully!", title="Project Updated")
        elif event.button.id == "back_to_main_button":
            self.app.pop_screen()

    def update_summary(self) -> None:
        log = self.query_one("#canvas_summary_log", RichLog)
        log.clear()
        log.write(f"[bold]Idea:[/bold] {self.current_project.get('idea', 'N/A')}")
        log.write(f"[bold]Audience:[/bold] {self.current_project.get('audience', 'N/A')}")
        log.write(f"[bold]Problem:[/bold] {self.current_project.get('problem', 'N/A')}")

class ValidationScreen(Screen):
    def __init__(self, state_manager: StateManager, agent_manager: AgentManager, current_project: dict):
        super().__init__()
        self.state_manager = state_manager
        self.agent_manager = agent_manager
        self.current_project = current_project

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="validation-screen-grid"):
            with VerticalScroll(id="validation-controls"):
                yield Static("[bold green]Phase 3: Validation[/bold green]", classes="sidebar-title")
                yield Button("Run Brutal Validation", id="run_validation_button", variant="primary")
                yield Button("Export MD Report", id="export_report_button", variant="success")
                yield ProgressBar(total=100, id="validation_progress_bar", classes="hidden")
                yield Button("Back to Main", id="back_to_main_button", classes="project-button")
            with VerticalScroll(id="validation-display"):
                yield Static("[bold blue]Validation Report[/bold blue]", classes="sidebar-title")
                yield RichLog(id="validation_report_log", wrap=True, highlight=True, markup=True)
        yield Footer()
    
    def on_mount(self) -> None:
        if self.current_project.get("validation_report"):
            self.query_one("#validation_report_log", RichLog).write(self.current_project["validation_report"])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run_validation_button":
            self.query_one("#validation_progress_bar").remove_class("hidden")
            self.query_one("#validation_report_log", RichLog).write("[bold cyan]Running Venture Validator... Be prepared for the roast.[/bold cyan]\n")
            self.run_worker(self.perform_background_validation(), exclusive=True)
        elif event.button.id == "export_report_button":
            filepath = self.state_manager.export_report(self.current_project["name"])
            self.app.notify(f"Report saved to {filepath}", title="Export Complete")
        elif event.button.id == "back_to_main_button":
            self.app.pop_screen()

    async def perform_background_validation(self):
        idea = self.current_project.get("idea", "")
        audience = self.current_project.get("audience", "")
        if not idea or not audience:
            self.query_one("#validation_report_log", RichLog).write("[bold red]Fill Canvas first![/bold red]")
            self.query_one("#validation_progress_bar").add_class("hidden")
            return
        report = await self.app.run_in_thread(self.agent_manager.current_engine.validate_idea, idea, audience, "Build stage", self.current_project.get("research_data", ""))
        self.query_one("#validation_report_log", RichLog).write(report)
        self.query_one("#validation_progress_bar").add_class("hidden")
        self.current_project["validation_report"] = report
        self.state_manager.save_project(self.current_project["name"], self.current_project)

class BuildScreen(Screen):
    def __init__(self, state_manager: StateManager, agent_manager: AgentManager, current_project: dict):
        super().__init__()
        self.state_manager = state_manager
        self.agent_manager = agent_manager
        self.current_project = current_project
        self.repo_path_input = Input(placeholder="Path to codebase (e.g., .)", id="repo_path_input")

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="build-screen-grid"):
            with VerticalScroll(id="build-controls"):
                yield Static("[bold green]Phase 4: Build[/bold green]", classes="sidebar-title")
                yield Button("Generate Roadmap", id="gen_roadmap", variant="primary")
                yield Static("\n[bold]Codebase Audit[/bold]", classes="canvas-label")
                yield self.repo_path_input
                yield Button("Run Technical Audit", id="run_audit", variant="warning")
                yield ProgressBar(id="build_progress_bar", classes="hidden")
                yield Button("Back to Main", id="back_to_main_button", classes="project-button")
            with VerticalScroll(id="build-display"):
                yield Static("[bold blue]Output[/bold blue]", classes="sidebar-title")
                yield RichLog(id="build_log", wrap=True, highlight=True, markup=True)
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one("#build_log", RichLog)
        if event.button.id == "gen_roadmap":
            log.write("[bold cyan]Generating technical roadmap...[/bold cyan]")
            # Future: Call agent_manager.current_engine.generate_roadmap
            self.current_project["mvp_roadmap"] = "Phase 1: Basic TUI. Phase 2: Groq Integration. Phase 3: Web Dashboard."
            self.state_manager.save_project(self.current_project["name"], self.current_project)
            log.write(self.current_project["mvp_roadmap"])
        elif event.button.id == "run_audit":
            path = self.repo_path_input.value.strip() or "."
            log.write(f"[bold cyan]Auditing codebase at: {path}[/bold cyan]\n")
            self.query_one("#build_progress_bar").remove_class("hidden")
            self.run_worker(self.perform_background_audit(path), exclusive=True)
        elif event.button.id == "back_to_main_button":
            self.app.pop_screen()

    async def perform_background_audit(self, path: str):
        audit = await self.app.run_in_thread(self.agent_manager.current_engine.analyze_codebase, path)
        self.query_one("#build_log", RichLog).write(audit)
        self.query_one("#build_progress_bar").add_class("hidden")
        self.current_project["codebase_audit"] = audit
        self.state_manager.save_project(self.current_project["name"], self.current_project)

# --- Main Application Logic ---

class MainScreen(Screen):
    def __init__(self, state_manager, agent_manager, current_project):
        super().__init__()
        self.state_manager = state_manager
        self.agent_manager = agent_manager
        self.current_project = current_project
        self.project_name = current_project["name"]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="app-grid"):
            with VerticalScroll(id="sidebar"):
                yield Static(f"Project: [bold blue]{self.project_name}[/bold blue]", classes="sidebar-title")
                yield Button("0. Idea Discovery", id="phase_discovery", classes="phase-button")
                yield Button("1. Research", id="phase_research", classes="phase-button")
                yield Button("2. Canvas", id="phase_canvas", classes="phase-button")
                yield Button("3. Validation", id="phase_validation", classes="phase-button")
                yield Button("4. Build", id="phase_build", classes="phase-button")
                yield Button("Switch Project", id="switch_project", classes="project-button")
            with VerticalScroll(id="main-content"):
                yield Static(f"Welcome to [bold cyan]AICoFounder[/bold cyan]", id="current-phase-display")
                yield Static("\nYour mission-control for startup execution. Select a phase on the left to begin.", classes="description")
                yield RichLog(id="chat-log", classes="chat-window", markup=True)
                with Horizontal(id="chat-input-container"):
                    yield Input(placeholder="Ask your AI Co-founder...", id="chat-input")
                    yield Button("Send", id="chat-send-button", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "phase_discovery":
            self.app.push_screen(IdeaDiscoveryScreen(self.state_manager, self.agent_manager, self.current_project))
        elif event.button.id == "phase_research":
            self.app.push_screen(ResearchScreen(self.state_manager, self.agent_manager, self.current_project))
        elif event.button.id == "phase_canvas":
            self.app.push_screen(CanvasScreen(self.state_manager, self.agent_manager, self.current_project))
        elif event.button.id == "phase_validation":
            self.app.push_screen(ValidationScreen(self.state_manager, self.agent_manager, self.current_project))
        elif event.button.id == "phase_build":
            self.app.push_screen(BuildScreen(self.state_manager, self.agent_manager, self.current_project))
        elif event.button.id == "switch_project":
            self.app.pop_screen()

class ProjectScreen(Screen):
    def __init__(self, state_manager, agent_manager):
        super().__init__()
        self.state_manager = state_manager
        self.agent_manager = agent_manager

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="project-selection"):
            yield Static("[bold green]AICoFounder Workspace[/bold green]", classes="sidebar-title")
            yield Static("Select an existing project or create a new one to start your journey.", classes="description")
            with VerticalScroll(id="project-list"):
                for p in self.state_manager.list_projects():
                    yield Button(p, id=f"load_{p}", classes="project-list-button")
            yield Input(placeholder="New project name (e.g. MySaaS)", id="new_p_name")
            yield Button("Create New Project", id="create_p", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id.startswith("load_"):
            name = event.button.id.replace("load_", "")
            data = self.state_manager.load_project(name)
            data["name"] = name
            self.app.push_screen(MainScreen(self.state_manager, self.agent_manager, data))
        elif event.button.id == "create_p":
            name = self.query_one("#new_p_name", Input).value.strip()
            if name:
                data = {"name": name, "current_phase": "discovery"}
                self.state_manager.save_project(name, data)
                self.app.push_screen(MainScreen(self.state_manager, self.agent_manager, data))

class AICofounderTUI(App):
    CSS_PATH = "aicofounder.css"
    def on_mount(self) -> None:
        self.state_manager = StateManager()
        self.agent_manager = AgentManager()
        self.push_screen(ProjectScreen(self.state_manager, self.agent_manager))

if __name__ == "__main__":
    AICofounderTUI().run()
