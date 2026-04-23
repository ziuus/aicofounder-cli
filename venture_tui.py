import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, RichLog, Input, ProgressBar, Label
from textual.containers import Container, VerticalScroll, Horizontal, Vertical
from textual.binding import Binding
from textual.screen import Screen
from textual.reactive import reactive
from textual.worker import Worker, WorkerState

from state_manager import StateManager
from agent_manager import VentureAgentManager

# --- Modern Components ---

class MissionHeader(Static):
    """A sleek, modern header with dynamic status."""
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("🚀 [bold]Venture[/bold] | Mission Control", id="app-title")
            yield Static("", id="status-indicator")

# --- Phase Screens (Modernized) ---

class BasePhaseScreen(Screen):
    def __init__(self, state_manager: StateManager, agent_manager: AgentManager, current_project: dict):
        super().__init__()
        self.state_manager = state_manager
        self.agent_manager = agent_manager
        self.current_project = current_project

    def notify_user(self, message: str, title: str = "Info", severity: str = "information"):
        self.app.notify(message, title=title, severity=severity)

class IdeaDiscoveryScreen(BasePhaseScreen):
    def compose(self) -> ComposeResult:
        yield MissionHeader()
        with Container(classes="main-container"):
            with Vertical(id="input-area", classes="glass-panel"):
                yield Static("[bold cyan]0. Reverse Discovery[/bold cyan]\nFind gaps based on your profile.")
                yield Label("Your Skills", classes="field-label")
                self.skills_input = Input(placeholder="Python, Rust, UX Design...", value=self.current_project.get("user_skills", ""))
                yield self.skills_input
                yield Label("Interests", classes="field-label")
                self.interests_input = Input(placeholder="Fintech, Space, Web3...", value=self.current_project.get("user_interests", ""))
                yield self.interests_input
                yield Button("Generate Opportunities", variant="primary", id="find_ideas_button")
                yield ProgressBar(total=100, id="discovery_progress", classes="hidden")
            
            with Vertical(id="display-area", classes="glass-panel"):
                yield Label("AI Strategy Suggestions", classes="section-title")
                self.log = RichLog(id="ideas_log", wrap=True, highlight=True, markup=True)
                yield self.log
        yield Footer()

    def on_mount(self) -> None:
        if self.current_project.get("generated_ideas"):
            self.log.write(self.current_project["generated_ideas"])

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "find_ideas_button":
            skills = self.skills_input.value.strip()
            interests = self.interests_input.value.strip()
            if not skills and not interests:
                self.notify_user("Please enter your profile data.", severity="error")
                return
            
            self.query_one("#discovery_progress").remove_class("hidden")
            self.log.clear()
            self.log.write("[bold cyan]Consulting the Strat-Agent...[/bold cyan]\n")
            self.run_worker(self.perform_discovery(skills, interests))

    async def perform_discovery(self, skills: str, interests: str):
        try:
            # FIX: Using asyncio.to_thread for blocking agent calls
            ideas = await asyncio.to_thread(self.agent_manager.current_engine.find_ideas, skills, interests)
            self.log.write(ideas)
            self.current_project["generated_ideas"] = ideas
            self.current_project["user_skills"] = skills
            self.current_project["user_interests"] = interests
            self.state_manager.save_project(self.current_project["name"], self.current_project)
        except Exception as e:
            self.log.write(f"[bold red]Discovery Error: {e}[/bold red]")
        finally:
            self.query_one("#discovery_progress").add_class("hidden")

class ResearchScreen(BasePhaseScreen):
    def compose(self) -> ComposeResult:
        yield MissionHeader()
        with Container(classes="main-container"):
            with Vertical(id="research-controls", classes="glass-panel"):
                yield Static("[bold cyan]1. Deep Research[/bold cyan]\nAutonomous market gap analysis.")
                self.query_input = Input(placeholder="Describe market or problem...", value=self.current_project.get("research_query", ""))
                yield self.query_input
                yield Button("Launch Scrapers", variant="primary", id="start_research_button")
                yield ProgressBar(total=100, id="research_progress", classes="hidden")
            
            with Vertical(id="research-display", classes="glass-panel"):
                yield Label("Market Intelligence", classes="section-title")
                self.log = RichLog(id="research_log", wrap=True, highlight=True, markup=True)
                yield self.log
        yield Footer()

    def on_mount(self) -> None:
        if self.current_project.get("research_data"):
            self.log.write(self.current_project["research_data"])

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start_research_button":
            query = self.query_input.value.strip()
            if query:
                self.query_one("#research_progress").remove_class("hidden")
                self.log.clear()
                self.log.write(f"[bold cyan]Scouring web for: {query}...[/bold cyan]\n")
                self.run_worker(self.perform_research(query))

    async def perform_research(self, query: str):
        try:
            results = await asyncio.to_thread(self.agent_manager.current_engine.perform_research, query)
            self.log.write(results)
            self.current_project["research_data"] = results
            self.current_project["research_query"] = query
            self.state_manager.save_project(self.current_project["name"], self.current_project)
        except Exception as e:
            self.log.write(f"[bold red]Research Error: {e}[/bold red]")
        finally:
            self.query_one("#research_progress").add_class("hidden")

class CanvasScreen(BasePhaseScreen):
    def compose(self) -> ComposeResult:
        yield MissionHeader()
        with Container(classes="main-container"):
            with Vertical(classes="glass-panel"):
                yield Static("[bold cyan]2. Startup Canvas[/bold cyan]\nDefine your core value prop.")
                yield Label("The Vision", classes="field-label")
                self.idea_input = Input(value=self.current_project.get("idea", ""))
                yield self.idea_input
                yield Label("Target Audience", classes="field-label")
                self.audience_input = Input(value=self.current_project.get("audience", ""))
                yield self.audience_input
                yield Label("The Core Problem", classes="field-label")
                self.problem_input = Input(value=self.current_project.get("problem", ""))
                yield self.problem_input
                yield Button("Save & Sync", variant="primary", id="save_canvas")
            
            with Vertical(classes="glass-panel"):
                yield Label("Canvas Integrity Check", classes="section-title")
                self.summary = Static(id="canvas_summary")
                yield self.summary
        yield Footer()

    def on_mount(self) -> None:
        self.update_summary()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_canvas":
            self.current_project["idea"] = self.idea_input.value.strip()
            self.current_project["audience"] = self.audience_input.value.strip()
            self.current_project["problem"] = self.problem_input.value.strip()
            self.state_manager.save_project(self.current_project["name"], self.current_project)
            self.update_summary()
            self.notify_user("Canvas synchronized.")

    def update_summary(self) -> None:
        text = f"[b]Idea:[/b] {self.current_project.get('idea', '...')}\n\n"
        text += f"[b]Audience:[/b] {self.current_project.get('audience', '...')}\n\n"
        text += f"[b]Problem:[/b] {self.current_project.get('problem', '...')}"
        self.query_one("#canvas_summary").update(text)

class ValidationScreen(BasePhaseScreen):
    def compose(self) -> ComposeResult:
        yield MissionHeader()
        with Container(classes="main-container"):
            with Vertical(classes="glass-panel"):
                yield Static("[bold cyan]3. Adversarial Validation[/bold cyan]\nBrutal roasts and risk assessment.")
                yield Button("Run Venture Roast", variant="warning", id="run_roast")
                yield Button("Export Final Report", variant="success", id="export_report")
                yield ProgressBar(total=100, id="roast_progress", classes="hidden")
            
            with Vertical(classes="glass-panel"):
                yield Label("Brutal Truth Log", classes="section-title")
                self.log = RichLog(id="roast_log", wrap=True, highlight=True, markup=True)
                yield self.log
        yield Footer()

    def on_mount(self) -> None:
        if self.current_project.get("validation_report"):
            self.log.write(self.current_project["validation_report"])

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run_roast":
            self.query_one("#roast_progress").remove_class("hidden")
            self.log.clear()
            self.log.write("[bold orange3]Initiating adversarial audit...[/bold orange3]\n")
            self.run_worker(self.perform_roast())
        elif event.button.id == "export_report":
            path = self.state_manager.export_report(self.current_project["name"])
            self.notify_user(f"Report exported: {path}")

    async def perform_roast(self):
        idea = self.current_project.get("idea", "")
        audience = self.current_project.get("audience", "")
        if not idea:
            self.log.write("[red]Error: Define your idea in Phase 2 first![/red]")
        else:
            try:
                report = await asyncio.to_thread(self.agent_manager.current_engine.validate_idea, idea, audience, "MVP stage", self.current_project.get("research_data", ""))
                self.log.write(report)
                self.current_project["validation_report"] = report
                self.state_manager.save_project(self.current_project["name"], self.current_project)
            except Exception as e:
                self.log.write(f"[red]Roast Error: {e}[/red]")
        self.query_one("#roast_progress").add_class("hidden")

class BuildScreen(BasePhaseScreen):
    def compose(self) -> ComposeResult:
        yield MissionHeader()
        with Container(classes="main-container"):
            with Vertical(classes="glass-panel"):
                yield Static("[bold cyan]4. Technical Blueprint[/bold cyan]\nRoadmaps and Code Audits.")
                yield Button("Generate Tech Roadmap", variant="primary", id="gen_roadmap")
                yield Label("Codebase Path", classes="field-label")
                self.path_input = Input(placeholder=".", value=".")
                yield self.path_input
                yield Button("Run Technical Audit", variant="warning", id="run_audit")
                yield ProgressBar(id="build_progress", classes="hidden")
            
            with Vertical(classes="glass-panel"):
                yield Label("Architectural Analysis", classes="section-title")
                self.log = RichLog(id="build_log", wrap=True, highlight=True, markup=True)
                yield self.log
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "gen_roadmap":
            self.log.write("[bold cyan]Architecting MVP roadmap...[/bold cyan]")
            self.current_project["mvp_roadmap"] = "Phase 1: Architecture Core. Phase 2: AI Logic. Phase 3: Deployment."
            self.state_manager.save_project(self.current_project["name"], self.current_project)
            self.log.write(self.current_project["mvp_roadmap"])
        elif event.button.id == "run_audit":
            path = self.path_input.value.strip()
            self.query_one("#build_progress").remove_class("hidden")
            self.log.write(f"[bold yellow]Auditing: {path}[/bold yellow]\n")
            self.run_worker(self.perform_audit(path))

    async def perform_audit(self, path: str):
        try:
            audit = await asyncio.to_thread(self.agent_manager.current_engine.analyze_codebase, path)
            self.log.write(audit)
            self.current_project["codebase_audit"] = audit
            self.state_manager.save_project(self.current_project["name"], self.current_project)
        except Exception as e:
            self.log.write(f"[red]Audit Error: {e}[/red]")
        finally:
            self.query_one("#build_progress").add_class("hidden")

# --- Main Landing ---

class MainScreen(Screen):
    def __init__(self, state_manager, agent_manager, current_project):
        super().__init__()
        self.state_manager = state_manager
        self.agent_manager = agent_manager
        self.current_project = current_project

    def compose(self) -> ComposeResult:
        yield MissionHeader()
        with Container(id="landing-grid"):
            with Vertical(id="phase-selector", classes="glass-panel"):
                yield Label(f"Project: [b]{self.current_project['name']}[/b]", id="proj-tag")
                yield Button("0. Idea Discovery", id="p0", classes="p-btn")
                yield Button("1. Deep Research", id="p1", classes="p-btn")
                yield Button("2. Startup Canvas", id="p2", classes="p-btn")
                yield Button("3. Brutal Validation", id="p3", classes="p-btn")
                yield Button("4. Technical Build", id="p4", classes="p-btn")
                yield Button("Switch Project", id="p_switch", variant="error")
            
            with Vertical(id="mission-brief", classes="glass-panel"):
                yield Label("Mission Briefing", classes="section-title")
                yield Static(f"Welcome back, Founder. Select a mission phase to execute strategy for [cyan]{self.current_project['name']}[/cyan].", id="brief-text")
                yield RichLog(id="main_chat", classes="chat-box", markup=True)
                with Horizontal(id="chat-row"):
                    yield Input(placeholder="Ask your AI Co-founder anything...", id="chat_in")
                    yield Button("Ask", variant="primary", id="chat_send")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        screens = {
            "p0": IdeaDiscoveryScreen,
            "p1": ResearchScreen,
            "p2": CanvasScreen,
            "p3": ValidationScreen,
            "p4": BuildScreen
        }
        if event.button.id in screens:
            self.app.push_screen(screens[event.button.id](self.state_manager, self.agent_manager, self.current_project))
        elif event.button.id == "p_switch":
            self.app.pop_screen()

class ProjectScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="startup-hub"):
            yield Static("✨ [bold cyan]Venture Hub[/bold cyan]", id="hub-title")
            with VerticalScroll(id="proj-list"):
                for p in self.app.state_manager.list_projects():
                    yield Button(f"🚀 {p}", id=f"load_{p}", classes="proj-entry")
            yield Input(placeholder="Enter startup name...", id="new_name")
            yield Button("Create New Startup Mission", variant="success", id="create_btn")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id.startswith("load_"):
            name = event.button.id.replace("load_", "")
            data = self.app.state_manager.load_project(name)
            data["name"] = name
            self.app.push_screen(MainScreen(self.app.state_manager, self.app.agent_manager, data))
        elif event.button.id == "create_btn":
            name = self.query_one("#new_name", Input).value.strip()
            if name:
                data = {"name": name, "current_phase": "discovery"}
                self.app.state_manager.save_project(name, data)
                self.app.push_screen(MainScreen(self.app.state_manager, self.app.agent_manager, data))

class VentureTUI(App):
    CSS_PATH = "venture.css"
    def on_mount(self) -> None:
        self.state_manager = StateManager()
        self.agent_manager = VentureAgentManager()
        self.push_screen(ProjectScreen())

def main():
    VentureTUI().run()

if __name__ == "__main__":
    main()
