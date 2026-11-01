from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, Label, Static
from rich.text import Text

from bagels.config import CONFIG
from bagels.utils.format import money_str
from bagels.managers.categories import get_category_budget_rows, update_category_budget
from bagels.managers.utils import (
    dynamic_cache,
    get_income_to_use,
    get_period_figures,
)
from bagels.models.category import Nature


class Budgets(Static):
    can_focus = True

    def __init__(self, page_parent, *args, **kwargs) -> None:
        super().__init__(
            *args, **kwargs, id="budgets-container", classes="module-container"
        )
        super().__setattr__("border_title", "Budgeting")
        self.page_parent = page_parent

    # --------------- Hooks -------------- #

    def on_mount(self) -> None:
        self.rebuild()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Persist a category budget when the user presses Enter in its input."""
        if event.input.id.startswith("budget-"):
            category_id = int(event.input.id.split("-")[1])
            value = event.value.strip()
            amount = float(value) if value else None
            update_category_budget(category_id, amount)
            self.app.notify(
                f"Budget {'saved: ' + money_str(amount) if amount is not None else 'cleared (no limit)'}",
                title="Category budget",
                timeout=2,
            )
            self.rebuild()

    # region Builders
    # ------------- Builders ------------- #

    def rebuild(self) -> None:
        budget_rows = dynamic_cache(get_category_budget_rows, self.page_parent.offset)
        self._rebuild_income_bar(budget_rows)
        self._rebuild_category_budgets(budget_rows)

    def _rebuild_category_budgets(self, budget_rows) -> None:
        restrict_amount = (
            r"\d*" if CONFIG.defaults.round_decimals == 0 else r"\d*\.?\d{0,2}"
        )
        total_budget = 0.0
        total_spent = 0.0
        for category, spent, level, budget, editable in budget_rows:
            spent_label = self.query_one(f"#budget-spent-{category.id}", Label)
            spent_label.update(f"spent {money_str(spent)}")

            left_label = self.query_one(f"#budget-left-{category.id}", Label)
            if budget is not None:
                remaining = round(budget - spent, 2)
                left_label.update(f"left {money_str(remaining)}")
                left_label.styles.color = "green" if remaining >= 0 else "red"
            else:
                left_label.update("-")

            if editable:
                input = self.query_one(f"#budget-{category.id}", Input)
                input.restrict = restrict_amount
                input.value = money_str(budget) if budget is not None else ""
            else:
                # Parent category: budget = sum of its subcategories (read-only)
                sum_label = self.query_one(f"#budget-sum-{category.id}", Label)
                sum_label.update(money_str(budget) if budget else "0")

            if level == 0 and budget is not None:
                total_budget += budget
                total_spent += spent
            elif level == 0:
                total_spent += spent

        total_budget_label = self.query_one("#budget-total-budget", Label)
        total_budget_label.update(money_str(total_budget))
        total_spent_label = self.query_one("#budget-total-spent", Label)
        total_spent_label.update(f"spent {money_str(total_spent)}")
        total_left_label = self.query_one("#budget-total-left", Label)
        total_remaining = round(total_budget - total_spent, 2)
        total_left_label.update(f"left {money_str(total_remaining)}")
        total_left_label.styles.color = (
            "green" if total_remaining >= 0 else "red"
        )

    def _rebuild_income_bar(self, budget_rows) -> None:
        offset = self.page_parent.offset
        net_income = dynamic_cache(get_income_to_use, offset)
        net_expenses = dynamic_cache(
            get_period_figures, isIncome=False, offset=offset, offset_type="month"
        )
        budget_total = round(
            sum(
                budget
                for _category, _spent, level, budget, _editable in budget_rows
                if level == 0 and budget is not None
            ),
            CONFIG.defaults.round_decimals,
        )

        income_bar_container = self.query_one("#income-bar")
        empty_bar = self.query_one(".empty-bar")

        income_bar_container.display = not not net_income
        empty_bar.display = not net_income

        if not net_income:
            return

        # The income splits into: spent (real expenses), budgeted (what is left
        # to spend of the sum of category budgets) and remaining (income minus
        # the sum of budgets = not covered by any budget).
        spent = round(net_expenses, CONFIG.defaults.round_decimals)
        budgeted_left = round(
            max(budget_total - spent, 0), CONFIG.defaults.round_decimals
        )
        remaining = round(net_income - budget_total, CONFIG.defaults.round_decimals)

        p_spent = min(round(spent / net_income * 100), 100)
        p_budgeted = min(round(budgeted_left / net_income * 100), 100 - p_spent)

        row1 = income_bar_container.query_one("#row-1")
        row1.styles.grid_columns = f"{p_spent}% {p_budgeted}% 1fr"

        label_spent_amount = income_bar_container.query_one("#label-spent-amount")
        label_spent_amount.update(money_str(spent))
        label_budgeted_amount = income_bar_container.query_one(
            "#label-budgeted-amount"
        )
        label_budgeted_amount.update(money_str(budgeted_left))
        remaining_label = income_bar_container.query_one("#label-remaining-amount")
        remaining_label.update(money_str(remaining))
        remaining_label.styles.color = "green" if remaining >= 0 else "red"

        # Expenses breakdown by category nature (Must / Need / Want).
        row3 = income_bar_container.query_one("#row-3")
        row4 = income_bar_container.query_one("#row-4")
        row3.display = not not net_expenses
        row4.display = not not net_expenses

        if not not net_expenses:
            expenses_must = round(
                dynamic_cache(
                    get_period_figures,
                    isIncome=False,
                    offset=offset,
                    offset_type="month",
                    nature=Nature.MUST,
                ),
                CONFIG.defaults.round_decimals,
            )
            expenses_need = round(
                dynamic_cache(
                    get_period_figures,
                    isIncome=False,
                    offset=offset,
                    offset_type="month",
                    nature=Nature.NEED,
                ),
                CONFIG.defaults.round_decimals,
            )
            expenses_want = round(
                net_expenses - expenses_must - expenses_need,
                CONFIG.defaults.round_decimals,
            )

            label_spent_must_amount = row3.query_one("#label-spent-must-amount")
            label_spent_must_amount.update(money_str(expenses_must))
            label_spent_need_amount = row3.query_one("#label-spent-need-amount")
            label_spent_need_amount.update(money_str(expenses_need))
            label_want_amount = row3.query_one("#label-want-amount")
            label_want_amount.update(money_str(expenses_want))

            p_must = round(expenses_must / net_expenses * 100)
            p_need = round(expenses_need / net_expenses * 100)
            p_want = round(expenses_want / net_expenses * 100)
            row4.styles.grid_columns = f"{p_must}% {p_need}% {p_want}%"

    # region View
    # --------------- View --------------- #
    def compose(self) -> ComposeResult:
        with Container(id="income-bar"):
            with Container(id="row-0"):
                with Horizontal():
                    yield Label("╭ Spent: ")
                    yield Label("0.0", id="label-spent-amount")
                with Horizontal(id="remaining"):
                    yield Label("Remaining: ")
                    yield Label("0.0", id="label-remaining-amount")
                    yield Label(" ╮")
            with Container(id="row-1"):
                yield Static(id="bar-spent")
                yield Static(id="bar-budgeted")
                yield Static(id="bar-remaining")
            with Container(id="row-2"):
                yield Static()
                with Horizontal():
                    yield Label("╰ Budgeted: ")
                    yield Label("0.0", id="label-budgeted-amount")
            with Container(id="row-3"):
                with Horizontal():
                    yield Label("╭ Must: ")
                    yield Label("0.0", id="label-spent-must-amount")
                with Horizontal():
                    yield Label("╭ Need: ")
                    yield Label("0.0", id="label-spent-need-amount")
                with Horizontal(id="want"):
                    yield Label("Want: ")
                    yield Label("0.0", id="label-want-amount")
                    yield Label(" ╮")
            with Container(id="row-4"):
                yield Static(id="bar-spent-must")
                yield Static(id="bar-spent-need")
                yield Static(id="bar-spent-want")
        with Container(id="category-budgets", classes="budget-section"):
            yield Label("Category budgets (monthly)", id="category-budgets-title")
            yield Label(
                "Set a budget per category and press Enter. Left = budget - spent this month.",
                classes="budget-hint",
            )
            with Horizontal(classes="budget-table-header"):
                yield Label("Category", classes="budget-name")
                yield Label("Budget", classes="budget-input")
                yield Label("Spent", classes="budget-spent")
                yield Label("Left", classes="budget-left")
            with Vertical(id="budget-rows", classes="budget-rows-container"):
                for i, (category, _spent, level, _budget, editable) in enumerate(
                    dynamic_cache(get_category_budget_rows, 0)
                ):
                    zebra = "zebra-a" if i % 2 == 0 else "zebra-b"
                    indent = "   " * level
                    with Horizontal(classes=f"budget-row {zebra}"):
                        yield Label(
                            Text(indent + category.name, style=category.color),
                            classes="budget-name",
                            id=f"budget-name-{category.id}",
                        )
                        if editable:
                            yield Input(
                                placeholder="0.0",
                                id=f"budget-{category.id}",
                                classes="budget-input",
                            )
                        else:
                            # Parent with subcategories: budget is read-only
                            # (auto-sum of its subcategories).
                            yield Label(
                                "",
                                id=f"budget-sum-{category.id}",
                                classes="budget-input budget-sum",
                            )
                        yield Label(
                            "",
                            id=f"budget-spent-{category.id}",
                            classes="budget-spent",
                        )
                        yield Label(
                            "", id=f"budget-left-{category.id}", classes="budget-left"
                        )
        # Total row docked to the bottom of the whole module so it is always visible.
        with Horizontal(id="budget-total-row", classes="budget-row budget-total"):
            yield Label("Total", classes="budget-name")
            yield Label("", id="budget-total-budget", classes="budget-input")
            yield Label("", id="budget-total-spent", classes="budget-spent")
            yield Label("", id="budget-total-left", classes="budget-left")
        with Container(classes="empty-bar"):
            yield Label("Nothing to display. Budgeting depends on your income!")
