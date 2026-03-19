import os
import sys
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, ListItem, ListView, Label
from textual.worker import Worker, WorkerState
from textual import work
from engine import get_packages

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
        if os.getuid() != 0:
            self.exit("CRITICAL: sdnf must be run with sudo!")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.run_search(event.value)

    @work(exclusive=True, thread=True)
    def run_search(self, term: str) -> None:
        self.notify(f"Searching for '{term}'...")
        
        # very slow uughh
        results = get_packages(term)
        
        self.call_from_thread(self.display_results, results)

    def display_results(self, packages) -> None:
        list_view = self.query_one("#package_list", ListView)
        list_view.clear()
        
        if not packages:
            list_view.append(ListItem(Label("No packages found.")))
            return

        for pkg in packages:
            list_view.append(ListItem(Label(f"{pkg.name} - {pkg.version}")))

if __name__ == "__main__":
    app = SDNFApp()
    app.run()