import os
import sys
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, ListItem, ListView, Label
from textual.worker import Worker, WorkerState
from textual import work
from src.engine import get_packages

class SDNFApp(App):
    """Sloppy DNF User Interface"""
    
    CSS_PATH = "style.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Search for a package (e.g., python):")
        yield Input(placeholder="Type and press Enter...", id="search_input")
        yield ListView(id="package_list")
        yield Footer()

    def on_mount(self) -> None:
        # Check root immediately on startup
        if os.getuid() != 0:
            self.exit("CRITICAL: sdnf must be run with sudo!")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Triggered when you press Enter in the search box"""
        self.run_search(event.value)

    @work(exclusive=True, thread=True)
    def run_search(self, term: str) -> None:
        """The Background Worker: Keeps the UI alive while DNF thinks"""
        self.notify(f"Searching for '{term}'...")
        
        # Call your engine (This is the slow part!)
        results = get_packages(term)
        
        # Send results back to the main UI thread
        self.call_from_thread(self.display_results, results)

    def display_results(self, packages) -> None:
        """Updates the list on the screen"""
        list_view = self.query_one("#package_list", ListView)
        list_view.clear()
        
        if not packages:
            list_view.append(ListItem(Label("No packages found.")))
            return

        for pkg in packages:
            # pkg is the object returned from your DNF engine
            list_view.append(ListItem(Label(f"{pkg.name} - {pkg.version}")))

if __name__ == "__main__":
    app = SDNFApp()
    app.run()