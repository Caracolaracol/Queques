from datetime import datetime

from rich.cells import cell_len
from rich.text import Text

from bagels.components.datatable import DataTable
from bagels.components.indicators import EmptyIndicator
from bagels.config import CONFIG
from bagels.managers.records import (
    get_record_total_split_amount,
    get_records,
)
from bagels.utils.format import format_date_to_readable, money_str

# Display caps (terminal cells) for the non-elastic columns. The Label column
# absorbs whatever width remains, so the table always fits the module without
# horizontal scrolling — full text lives in the details bar below the table.
CATEGORY_CAP = 18
ACCOUNT_CAP = 12
LABEL_MIN = 6


class DisplayMode:
    DATE = "d"


def _truncate(text: str, max_width: int) -> str:
    """Truncate plain text to max_width display cells, ending with an ellipsis."""
    if cell_len(text) <= max_width:
        return text
    if max_width <= 1:
        return "…"
    cut = text[: max_width - 1]
    while cell_len(cut) > max_width - 1:
        cut = cut[:-1]
    return cut + "…"


class RecordTableBuilder:
    def rebuild(self, focus=True) -> None:
        if not hasattr(self, "table"):
            return
        table = self.table
        empty_indicator: EmptyIndicator = self.query_one(".empty-indicator")
        self._row_details = {}
        self._initialize_table(table)
        records = self._fetch_records()

        match self.displayMode:
            case DisplayMode.DATE:
                self._build_date_view(table, records)
            case _:
                pass

        if hasattr(self, "current_row_index"):
            table.move_cursor(row=self.current_row_index)
        elif getattr(self, "_first_detail_row", None) is not None:
            # First build: land the cursor on the first row that has details so
            # the details bar is populated without any interaction.
            table.move_cursor(row=self._first_detail_row)
        empty_indicator.display = not table.rows
        table.display = not not table.rows
        self._update_details(
            getattr(self, "current_row", None) or next(iter(self._row_details), None)
        )
        if focus:
            if table.display:
                table.focus()
            else:
                self.focus()

    def _fetch_records(self):
        params = {
            "offset": self.page_parent.filter["offset"],
            "offset_type": self.page_parent.filter["offset_type"],
        }
        if self.page_parent.filter["byAccount"]:
            params["account_id"] = self.page_parent.mode["accountId"]["default_value"]
        return get_records(
            **params,
        )

    def _initialize_table(self, table: DataTable) -> None:
        table.clear()
        table.columns.clear()
        match self.displayMode:
            case DisplayMode.DATE:
                table.add_columns(" ", "Date", "Category", "Amount", "Label", "Account")

    def _table_width(self) -> int:
        """Usable width (in cells) for the table inside its module."""
        width = self.table.size.width or self.size.width or self.app.size.width
        return max(width, 20)

    # region Date view
    def _build_date_view(self, table: DataTable, records: list) -> None:
        # Column caps adapt to the module width so the table fits even in
        # narrow windows; the Label column absorbs whatever remains. First
        # reserve room for the non-flexible cells (icon, date, amount), all
        # cell paddings and the minimum Label; the rest is shared by Category
        # and Account (60/40) through their truncation caps.
        width = self._table_width()
        date_width = cell_len(datetime.now().strftime(CONFIG.defaults.date_format))
        reserved = 2 + date_width + 9 + LABEL_MIN + 12
        rest = max(width - reserved, 10)
        self._cat_cap = min(CATEGORY_CAP, max(6, (rest * 3) // 5))
        self._acc_cap = min(ACCOUNT_CAP, max(5, (rest * 2) // 5))

        # First pass: build every row with its display width so the elastic
        # Label column can be sized to make the whole table fit.
        rows = []  # (kind, key, cells, details)
        widths = {"icon": 2, "date": 4, "category": 0, "amount": 0, "account": 0}
        for record in records:
            flow_icon = self._get_flow_icon(len(record.splits) > 0, record.isIncome)
            flow_plain = "+" if record.isIncome else "-"

            date_string = record.date.strftime(CONFIG.defaults.date_format)
            category_string, amount_string, account_string = self._format_record_fields(
                record, flow_icon
            )
            widths["date"] = max(widths["date"], cell_len(date_string))
            widths["category"] = max(
                widths["category"], self._plain_width(category_string)
            )
            widths["amount"] = max(widths["amount"], self._plain_width(amount_string))
            widths["account"] = max(widths["account"], cell_len(account_string))

            rows.append(
                (
                    "record",
                    f"r-{str(record.id)}",
                    (
                        None,
                        date_string,
                        category_string,
                        amount_string,
                        record.label,
                        account_string,
                    ),
                    self._record_details(record, flow_plain),
                )
            )

            # Add split rows if applicable
            if record.splits and self.show_splits:
                rows.extend(self._split_rows(record, widths))

        if not rows:
            return

        # Second pass: fit columns to the module and add the rows. Each column
        # is as wide as its (capped) content, but headers set a floor.
        widths["icon"] = max(widths["icon"], cell_len(" "))
        widths["date"] = max(widths["date"], cell_len("Date"))
        widths["category"] = max(
            min(widths["category"], self._cat_cap), cell_len("Category")
        )
        widths["amount"] = max(widths["amount"], cell_len("Amount"))
        widths["account"] = max(
            min(widths["account"], self._acc_cap), cell_len("Account")
        )
        fixed = (
            (widths["icon"] + 2)
            + (widths["date"] + 2)
            + (widths["category"] + 2)
            + (widths["amount"] + 2)
            + (widths["account"] + 2)
            + 2  # the Label cell's own padding
        )
        label_budget = max(self._table_width() - fixed, LABEL_MIN)

        self._first_detail_row = None
        for row_index, (kind, key, cells, details) in enumerate(rows):
            icon, date, category, amount, label, account = cells
            if label is not None:
                if isinstance(label, Text):
                    label.truncate(label_budget, overflow="ellipsis")
                else:
                    label = _truncate(str(label), label_budget)
            if details is not None and key:
                self._row_details[key] = details
                if self._first_detail_row is None:
                    self._first_detail_row = row_index
            style_name = {"net": "net"}.get(kind)
            table.add_row(
                icon or " ",
                date,
                category,
                amount,
                label or "",
                account,
                style_name=style_name,
                key=key,
            )

    def _plain_width(self, cell) -> int:
        """Display width of a cell (markup string or Text)."""
        if isinstance(cell, Text):
            return cell_len(cell.plain)
        return cell_len(Text.from_markup(cell).plain)

    def _record_details(self, record, flow_plain: str) -> tuple[str, str]:
        title = record.label
        date_string = format_date_to_readable(record.date)
        if record.isTransfer:
            meta = (
                f"{date_string} · {record.account.name} → "
                f"{record.transferToAccount.name} · {money_str(record.amount)}"
            )
        else:
            meta = (
                f"{date_string} · {record.category.name} · {record.account.name} · "
                f"{flow_plain} {money_str(record.amount)}"
            )
            if record.splits:
                paid = sum(1 for split in record.splits if split.isPaid)
                meta += f" · {len(record.splits)} splits ({paid} paid)"
        return title, meta

    def _split_rows(self, record, widths: dict) -> list:
        color = record.category.color.lower()
        amount_self = round(
            record.amount - get_record_total_split_amount(record.id),
            CONFIG.defaults.round_decimals,
        )
        split_flow_icon = (
            f"[red]{CONFIG.symbols.amount_negative}[/red]"
            if record.isIncome
            else f"[green]{CONFIG.symbols.amount_positive}[/green]"
        )
        split_flow_plain = "-" if record.isIncome else "+"
        line_char = f"[{color}]{CONFIG.symbols.line_char}[/{color}]"
        finish_line_char = f"[{color}]{CONFIG.symbols.finish_line_char}[/{color}]"

        rows = []
        for split in record.splits:
            paid_status_icon = self._get_split_status_icon(split)
            date_string = (
                Text(
                    split.paidDate.strftime(CONFIG.defaults.date_format), style="italic"
                )
                if split.paidDate
                else Text("-")
            )
            person_name = _truncate(split.person.name, self._cat_cap - 4)
            category_string = f"{line_char} {paid_status_icon} {person_name}"
            amount_string = f"{split_flow_icon} {money_str(split.amount)}"
            account_string = (
                _truncate(split.account.name, self._acc_cap) if split.account else "-"
            )
            widths["date"] = max(widths["date"], cell_len(date_string.plain))
            widths["category"] = max(
                widths["category"], self._plain_width(category_string)
            )
            widths["amount"] = max(widths["amount"], self._plain_width(amount_string))
            widths["account"] = max(widths["account"], cell_len(account_string))

            status = (
                f"Paid {format_date_to_readable(split.paidDate)}"
                if split.paidDate
                else "Unpaid"
            )
            details = (
                f"Split · {split.person.name}",
                f"{status} · {account_string} · {split_flow_plain} {money_str(split.amount)}",
            )
            rows.append(
                (
                    "split",
                    f"s-{str(split.id)}",
                    (" ", date_string, category_string, amount_string, "", account_string),
                    details,
                )
            )

        # Add net amount row
        net_category = f"{finish_line_char} {_truncate('Self total', self._cat_cap - 2)}"
        net_amount = f"= {money_str(amount_self)}"
        widths["category"] = max(widths["category"], self._plain_width(net_category))
        widths["amount"] = max(widths["amount"], self._plain_width(net_amount))
        rows.append(
            (
                "net",
                None,
                ("", "", net_category, net_amount, "", ""),
                ("Self total", f"= {money_str(amount_self)}"),
            )
        )
        return rows

    def _get_flow_icon(self, recordHasSplits: bool, is_income: bool) -> str:
        if recordHasSplits and not self.show_splits:
            flow_icon_positive = "[green]=[/green]"
            flow_icon_negative = "[red]=[/red]"
        else:
            flow_icon_positive = f"[green]{CONFIG.symbols.amount_positive}[/green]"
            flow_icon_negative = f"[red]{CONFIG.symbols.amount_negative}[/red]"
        return flow_icon_positive if is_income else flow_icon_negative

    def _format_record_fields(self, record, flow_icon: str) -> tuple[str, str]:
        if record.isTransfer:
            category_string = Text()
            category_string.append(
                record.account.name, style="italic" if record.account.hidden else ""
            )
            category_string.append(" → ")
            category_string.append(
                record.transferToAccount.name,
                style="italic" if record.transferToAccount.hidden else "",
            )
            category_string.truncate(self._cat_cap, overflow="ellipsis")
            amount_string = money_str(record.amount)
            account_string = "-"
        else:
            color_tag = record.category.color.lower()
            category_name = _truncate(record.category.name, self._cat_cap)
            category_string = (
                f"[{color_tag}]{CONFIG.symbols.category_color}[/{color_tag}] {category_name}"
            )

            if record.splits and not self.show_splits:
                amount_self = round(
                    record.amount - get_record_total_split_amount(record.id), 2
                )
                amount_string = f"{flow_icon} {money_str(amount_self)}"
            else:
                amount_string = f"{flow_icon} {money_str(record.amount)}"

            account_string = _truncate(record.account.name, self._acc_cap)

        return category_string, amount_string, account_string

    def _get_split_status_icon(self, split) -> str:
        if split.isPaid:
            return f"[green]{CONFIG.symbols.split_paid}[/green]"
        else:
            return f"[grey]{CONFIG.symbols.split_unpaid}[/grey]"
