import os
from textual.app import App, ComposeResult
from textual.widgets import (
    DataTable,
    Input,
    ListItem,
    TabbedContent,
    TabPane,
    ProgressBar,
    Header,
    RichLog,
    Label,
    ListView,
)
from textual.containers import Container, Vertical, Horizontal
from textual import on, work
from rich.text import Text


class SloppyDNF(App):
    TITLE = "SloppyDNF"
    ENABLE_COMMAND_PALETTE = False
    CSS_PATH = "../style.tcss"

    TAB_MAP = {
        "tab-all": "all",
        "tab-installed": "installed",
        "tab-updates": "updates",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.all_packages = []
        self.upgrade_packages = []
        self.installed_packages = []
        self.displayed_packages = {"all": [], "installed": [], "updates": []}
        self.search_term = ""

    # LAYOYT
    def compose(self) -> ComposeResult:
        yield Label("SloppyDNF", id="header")

        with Horizontal(id="main"):
            with Vertical(id="package_stuff"):
                yield RichLog(id="package_information", wrap=True, auto_scroll=False)
                yield RichLog(id="package_log", wrap=True, auto_scroll=False)
            with Vertical(id="package_selector"):
                with TabbedContent(id="tabs"):
                    with TabPane("all", id="tab-all"):
                        yield DataTable(id="all")
                    with TabPane("installed", id="tab-installed"):
                        yield DataTable(id="installed")

                    with TabPane("updates", id="tab-updates"):
                        yield DataTable(id="updates")
                yield Input(id="searcher")
                with Horizontal(id="options"):

                    yield ListView(
                        ListItem(Label("One")),
                        ListItem(Label("Two")),
                        ListItem(Label("Three")),
                    )

        yield ProgressBar(id="progress", clock=None, show_eta=False)

    # FIRST MOUNT
    def on_mount(self) -> None:
        # if os.getuid() != 0:
        # self.exit("sudo missing.")
        # return

        for table_id in ("all", "installed", "updates"):
            table = self.query_one(f"#{table_id}", DataTable)
            table.add_column("Package - Version - Arch - Installed")
            table.show_header = False
            table.cursor_type = "row"

            self.query_one("#package_information", RichLog).border_title = "Info"
            self.query_one("#package_log", RichLog).border_title = "Log"
            self.query_one("#package_selector", Vertical).border_title = "Packages"
            self.query_one("#package_selector", Vertical).border_subtitle = (
                "M enu ─ R emove"
            )

        self.load_packages()

    @work(exclusive=True, thread=True)
    def load_packages(self) -> None:
        from engine import get_all

        all_pkgs, installed_pkgs, upgrade_pkgs = get_all()
        self.call_from_thread(
            self.store_and_display, all_pkgs, upgrade_pkgs, installed_pkgs
        )

    def store_and_display(self, all_pkgs, upgrade_pkgs, installed_pkgs) -> None:
        self.all_packages = all_pkgs
        self.upgrade_packages = upgrade_pkgs
        self.installed_packages = installed_pkgs
        self.populate_tab("all")
        self.populate_tab("installed")
        self.populate_tab("updates")
        total = len(self.all_packages)
        self.query_one("#progress", ProgressBar).update(total=total, progress=total)

    def populate_tab(self, tab: str, search: str = "") -> None:
        table = self.query_one(f"#{tab}", DataTable)
        table.clear()
        if tab == "all":
            packages = self.all_packages
        elif tab == "installed":
            packages = self.installed_packages
        elif tab == "updates":
            packages = self.upgrade_packages
        else:
            packages = []

        if search:
            packages = [p for p in packages if search.lower() in p.name.lower()]

        self.displayed_packages[tab] = packages

        if not packages:
            table.add_row("No packages found.")
            return

        for pkg in packages:
            indicator = "✓" if pkg.reponame == "@System" else "x"
            table.add_row(f"{pkg.name} - {pkg.version} - {pkg.arch} - {indicator}")

    @on(TabbedContent.TabActivated)
    def on_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        tab_id = event.tab.id
        if tab_id in self.TAB_MAP:
            self.populate_tab(self.TAB_MAP[tab_id], self.search_term)

    @on(Input.Changed, "#searcher")
    def handle_search(self, event: Input.Changed) -> None:
        self.search_term = event.value
        self.refresh_current_tab()

    def current_tab(self) -> str:
        active = self.query_one("#tabs", TabbedContent).active
        return self.TAB_MAP.get(active, "all")

    def refresh_current_tab(self) -> None:
        self.populate_tab(self.current_tab(), self.search_term)

    def show_package_info(self, pkg) -> None:
        log = self.query_one("#package_information", RichLog)
        log.clear()
        lines = [
            f"{pkg.name} - {pkg.version}-{pkg.release}",
            f"Repo: {pkg.reponame}",
            f"Summary: {pkg.summary}",
            f"License: {pkg.license}",
            f"Size: {pkg.installsize // 1024} KB",
            f"URL: {pkg.url}",
            f"",
            f"{pkg.description}",
        ]
        for line in lines:
            log.write(line, log.size.width)

    @on(DataTable.RowHighlighted)
    def on_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.control.id != self.current_tab():
            return
        packages = self.displayed_packages[self.current_tab()]
        index = event.cursor_row
        if 0 <= index < len(packages):
            self.show_package_info(packages[index])


if __name__ == "__main__":
    app = SloppyDNF()
    app.run()
