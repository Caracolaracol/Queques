from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Label, ListItem, ListView, Static
from textual.binding import Binding

from bagels.config import CONFIG
from bagels.forms.service_account_forms import ServiceAccountForm
from bagels.managers.service_accounts import (
    create_service_account,
    delete_service_account,
    get_all_service_accounts,
    update_service_account,
)
from bagels.modals.confirmation import ConfirmationModal
from bagels.modals.input import InputModal


class ServiceAccounts(Static):
    """Manage customer numbers for external service providers."""

    can_focus = True

    BINDINGS = [
        Binding(CONFIG.hotkeys.new, "new", "New account"),
        Binding(CONFIG.hotkeys.edit, "edit", "Edit account"),
        Binding(CONFIG.hotkeys.delete, "delete", "Archive account"),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args,
            **kwargs,
            id="service-accounts-container",
            classes="module-container",
        )
        super().__setattr__("border_title", "Service accounts")
        super().__setattr__(
            "border_subtitle",
            f"{CONFIG.hotkeys.new} add  {CONFIG.hotkeys.edit} edit  {CONFIG.hotkeys.delete} archive",
        )
        self.entries = []
        self.service_account_form = ServiceAccountForm()

    def on_mount(self) -> None:
        self.rebuild()

    # --------------- Helpers -------------- #

    def _selected_entry(self):
        list_view = self.query_one("#service-accounts-list", ListView)
        if list_view.index is None or list_view.index >= len(self.entries):
            return None
        return self.entries[list_view.index]

    def _notify_no_selected(self) -> None:
        self.app.notify(
            title="Error",
            message="No service account selected",
            severity="error",
            timeout=3,
        )

    # --------------- Builders -------------- #

    def rebuild(self) -> None:
        list_view = self.query_one("#service-accounts-list", ListView)
        previous_id = None
        selected = self._selected_entry()
        if selected is not None:
            previous_id = selected.id

        list_view.clear()
        self.entries = get_all_service_accounts()
        empty = self.query_one("#service-accounts-empty", Label)
        empty.display = not self.entries

        for entry in self.entries:
            details = entry.alias or entry.notes or ""
            list_view.append(
                ListItem(
                    Container(
                        Label(entry.provider, classes="provider"),
                        Label(entry.accountNumber, classes="account-number"),
                        Label(details, classes="details"),
                        classes="service-account-item-content",
                    ),
                    id=f"service-account-{entry.id}",
                    classes="service-account-item",
                )
            )

        if self.entries:
            target = next(
                (
                    index
                    for index, entry in enumerate(self.entries)
                    if entry.id == previous_id
                ),
                None,
            )
            list_view.index = target if target is not None else 0

    # --------------- Callbacks -------------- #

    def on_descendant_focus(self, event) -> None:
        if event.widget.id and event.widget.id.startswith("service-account-"):
            self.query_one(
                "#service-accounts-list", ListView
            ).index = self.entries.index(
                next(
                    entry
                    for entry in self.entries
                    if entry.id == int(event.widget.id.split("-")[-1])
                )
            )

    # --------------- CRUD -------------- #

    def action_new(self) -> None:
        def check_result(result) -> None:
            if not result:
                return
            try:
                create_service_account(result)
            except Exception as error:
                self.app.notify(
                    title="Error", message=str(error), severity="error", timeout=10
                )
            else:
                self.app.notify(
                    title="Success",
                    message="Service account created",
                    severity="information",
                    timeout=3,
                )
                self.rebuild()

        self.app.push_screen(
            InputModal("New Service Account", self.service_account_form.get_form()),
            callback=check_result,
        )

    def action_edit(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            self._notify_no_selected()
            return

        def check_result(result) -> None:
            if not result:
                return
            try:
                update_service_account(entry.id, result)
            except Exception as error:
                self.app.notify(
                    title="Error", message=str(error), severity="error", timeout=10
                )
            else:
                self.app.notify(
                    title="Success",
                    message="Service account updated",
                    severity="information",
                    timeout=3,
                )
                self.rebuild()

        self.app.push_screen(
            InputModal(
                "Edit Service Account",
                self.service_account_form.get_filled_form(entry.id),
            ),
            callback=check_result,
        )

    def action_delete(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            self._notify_no_selected()
            return

        def check_delete(result) -> None:
            if not result:
                return
            delete_service_account(entry.id)
            self.app.notify(
                title="Success",
                message="Service account archived",
                severity="information",
                timeout=3,
            )
            self.rebuild()

        self.app.push_screen(
            ConfirmationModal(
                f"Archive service account '{entry.provider} {entry.accountNumber}'?"
            ),
            check_delete,
        )

    # --------------- View -------------- #

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(
                "No service accounts. Press the add shortcut to create one.",
                id="service-accounts-empty",
                classes="empty",
            )
            yield ListView(id="service-accounts-list")
