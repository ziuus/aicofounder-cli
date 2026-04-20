import sqlite3
import os
import json

class StateManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to a hidden directory in the user's home for persistence
            home_dir = os.path.expanduser("~")
            app_dir = os.path.join(home_dir, ".aicofounder")
            os.makedirs(app_dir, exist_ok=True)
            self.db_path = os.path.join(app_dir, "projects.db")
        else:
            self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    data TEXT
                )
            """)
            conn.commit()

    def save_project(self, project_name: str, project_data: dict):
        """Saves or updates project data."""
        data_json = json.dumps(project_data)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO projects (name, data) VALUES (?, ?)",
                (project_name, data_json)
            )
            conn.commit()

    def load_project(self, project_name: str) -> dict | None:
        """Loads project data by name."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM projects WHERE name = ?", (project_name,))
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return None

    def list_projects(self) -> list[str]:
        """Lists all saved project names."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM projects")
            return [row[0] for row in cursor.fetchall()]

    def delete_project(self, project_name: str):
        """Deletes a project by name."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE name = ?", (project_name,))
            conn.commit()

if __name__ == "__main__":
    # Example usage (for testing purposes)
    state_manager = StateManager(db_path="test_projects.db")
    
    # Save a project
    state_manager.save_project("MyFirstStartup", {"idea": "AI that makes coffee", "phase": "Research"})
    state_manager.save_project("MySecondStartup", {"idea": "Robots for everything", "phase": "Build"})

    # Load a project
    loaded_data = state_manager.load_project("MyFirstStartup")
    print(f"Loaded project: {loaded_data}")

    # List projects
    projects = state_manager.list_projects()
    print(f"All projects: {projects}")

    # Update a project
    state_manager.save_project("MyFirstStartup", {"idea": "AI that makes coffee", "phase": "Validation", "market_size": "large"})
    updated_data = state_manager.load_project("MyFirstStartup")
    print(f"Updated project: {updated_data}")
    
    # Delete a project
    state_manager.delete_project("MySecondStartup")
    print(f"Projects after deletion: {state_manager.list_projects()}")

    # Clean up test db
    os.remove("test_projects.db")
