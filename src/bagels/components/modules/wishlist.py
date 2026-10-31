from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Input, ListItem, ListView, Static

from bagels.config import CONFIG
from bagels.managers.wishlist import (
    add_wishlist_item,
    delete_wishlist_item,
    get_wishlist_items,
    move_wishlist_item,
    toggle_wishlist_item,
)

DONE_MARK = "✓ "
OPEN_MARK = "○ "


class Wishlist(Static):
    """A simple, persistent wishlist: add items, toggle done, delete."""

    can_focus = True

    BINDINGS = [
        Binding(CONFIG.hotkeys.new, "add_item", "Add"),
        Binding(CONFIG.hotkeys.delete, "delete_item", "Delete"),
        Binding("space", "toggle_item", "Done"),
        Binding("shift+up", "move_item_up", "Move up"),
        Binding("shift+down", "move_item_down", "Move down"),
        # Ctrl variants are the same actions (terminal-safe, no conflicts);
        # they're hidden so the footer stays short.
        Binding("ctrl+up", "move_item_up", "Move up", show=False),
        Binding("ctrl+down", "move_item_down", "Move down", show=False),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args, **kwargs, id="wishlist-container", classes="module-container"
        )
        super().__setattr__("border_title", "Wishlist")

    # --------------- Hooks -------------- #

    def on_mount(self) -> None:
        self.rebuild()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "wishlist-input":
            value = event.value.strip()
            if value:
                add_wishlist_item(value)
                event.input.value = ""
                self.rebuild()
                self.query_one("#wishlist-list", ListView).focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Enter on an item toggles its done state."""
        if event.list_view.index is not None:
            toggle_wishlist_item(self._items[event.list_view.index].id)
            self.rebuild()

    # --------------- Builders -------------- #

    def rebuild(self) -> None:
        list_view = self.query_one("#wishlist-list", ListView)
        # Keep the *selected item* (by id), not the selected index — after a
        # move the item sits on a different row, and the cursor should follow
        # it so repeated presses keep moving the same item.
        selected_id = (
            self._selected_entry().id if self._selected_entry() is not None else None
        )
        previous = list_view.index
        list_view.clear()
        self._items = get_wishlist_items()
        for entry in self._items:
            mark = DONE_MARK if entry.done else OPEN_MARK
            item_class = "wishlist-done" if entry.done else "wishlist-open"
            list_view.append(
                ListItem(Static(mark + entry.item, classes=f"wishlist-item {item_class}"))
            )
        # keep a visible selection so toggle/delete always have a target
        if self._items:
            target = next(
                ((i for i, e in enumerate(self._items) if e.id == selected_id)),
                None,
            )
            prev = previous if previous is not None else 0
            list_view.index = target if target is not None else min(prev, len(self._items) - 1)

    # --------------- Actions -------------- #

    def _selected_entry(self):
        list_view = self.query_one("#wishlist-list", ListView)
        if list_view.index is None or list_view.index >= len(self._items):
            return None
        return self._items[list_view.index]

    def action_add_item(self) -> None:
        self.query_one("#wishlist-input", Input).focus()

    def action_delete_item(self) -> None:
        entry = self._selected_entry()
        if entry is not None:
            delete_wishlist_item(entry.id)
            self.rebuild()

    def action_toggle_item(self) -> None:
        entry = self._selected_entry()
        if entry is not None:
            toggle_wishlist_item(entry.id)
            self.rebuild()

    def _move_item(self, direction: int) -> None:
        entry = self._selected_entry()
        if entry is not None and move_wishlist_item(entry.id, direction):
            self.rebuild()

    def action_move_item_up(self) -> None:
        self._move_item(-1)

    def action_move_item_down(self) -> None:
        self._move_item(1)

    # --------------- View -------------- #

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Input(placeholder="Add a wishlist item...", id="wishlist-input")
            yield ListView(id="wishlist-list")
