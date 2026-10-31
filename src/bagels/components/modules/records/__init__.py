from rich.text import Text
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Button, Static

from bagels.components.datatable import DataTable
from bagels.components.indicators import EmptyIndicator
from bagels.components.modules.records._cud import RecordCUD
from bagels.components.modules.records._table_builder import RecordTableBuilder
from bagels.config import CONFIG


class DisplayMode:
    DATE = "d"


class Records(RecordCUD, RecordTableBuilder, Static):
    BINDINGS = [
        (CONFIG.hotkeys.new, "new", "Add"),
        (CONFIG.hotkeys.delete, "delete", "Delete"),
        (CONFIG.hotkeys.edit, "edit", "Edit"),
        (CONFIG.hotkeys.home.new_transfer, "new_transfer", "Transfer"),
        (CONFIG.hotkeys.home.toggle_splits, "toggle_splits", "Toggle Splits"),
    ]

    can_focus = True
    show_splits = True
    displayMode = reactive(DisplayMode.DATE)

    def __init__(self, parent: Static, *args, **kwargs) -> None:
        super().__init__(
            *args, **kwargs, id="records-container", classes="module-container"
        )
        super().__setattr__("border_title", "Records")
        self.page_parent = parent

    def on_mount(self) -> None:
        self.rebuild()

    # region Callbacks
    # ------------- Callbacks ------------ #

    def on_resize(self, event) -> None:
        # Column widths depend on the module width: rebuild so the table always
        # fits without horizontal scrolling.
        self.rebuild(focus=False)

    def _update_details(self, row_key) -> None:
        details_widget = self.query_one("#record-details")
        details = (getattr(self, "_row_details", None) or {}).get(row_key)
        if not details:
            details_widget.update("")
            details_widget.display = False
            return
        title, meta = details
        text = Text()
        text.append(title, style="bold")
        text.append("\n")
        text.append(meta, style="dim")
        details_widget.update(text)
        details_widget.display = True

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        current_row_index = event.cursor_row
        if event.row_key and event.row_key.value:
            self.current_row = event.row_key.value
            self.current_row_index = current_row_index
        else:
            self.current_row = None
            self.current_row_index = None
        self._update_details(self.current_row)

    def action_toggle_splits(self) -> None:
        self.show_splits = not self.show_splits
        self.rebuild()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "prev-month":
                self.page_parent.action_prev_month()
            case "next-month":
                self.page_parent.action_next_month()
            case _:
                pass

    # region View
    # --------------- View --------------- #

    def compose(self) -> ComposeResult:
        self.table = DataTable(
            id="records-table",
            cursor_type="row",
            cursor_foreground_priority=True,
            zebra_stripes=True,
        )
        yield self.table
        yield Static(id="record-details", classes="record-details")
        yield EmptyIndicator("No entries")
