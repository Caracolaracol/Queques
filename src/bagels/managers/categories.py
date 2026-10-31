from datetime import datetime

from rich.text import Text
from sqlalchemy import desc, func, select
from sqlalchemy.orm import joinedload, sessionmaker

from bagels.managers.utils import get_start_end_of_period
from bagels.models.category import Category
from bagels.models.database.app import db_engine
from bagels.models.record import Record

Session = sessionmaker(bind=db_engine)


# region Get
def get_categories_count():
    """Count all categories excluding deleted ones."""
    session = Session()
    try:
        stmt = select(Category)
        return len(session.scalars(stmt).all())
    finally:
        session.close()


def get_all_categories_tree() -> list[tuple[Category, Text, int]]:
    """Retrieve all categories in a hierarchical tree format."""
    session = Session()
    try:
        stmt = (
            select(Category)
            .options(joinedload(Category.parentCategory))
            .order_by(Category.id)
            .filter(Category.deletedAt.is_(None))
        )
        categories = session.scalars(stmt).all()

        def build_category_tree(parent_id=None, depth=0):
            result = []
            for category in categories:
                if category.parentCategoryId == parent_id:
                    if depth == 0:
                        node = Text("●", style=category.color)
                    else:
                        node = Text(
                            " " * (depth - 1)
                            + ("└" if is_last(category, parent_id) else "├"),
                            style=category.color,
                        )
                    result.append((category, node, depth))
                    result.extend(build_category_tree(category.id, depth + 1))
            return result

        def is_last(category, parent_id):
            siblings = [cat for cat in categories if cat.parentCategoryId == parent_id]
            return category == siblings[-1]

        return build_category_tree()
    finally:
        session.close()


def get_all_categories_by_freq():
    """Retrieve all categories ordered by the frequency of their usage in records."""
    session = Session()
    try:
        stmt = (
            select(Category, func.count(Category.records).label("record_count"))
            .outerjoin(Category.records)
            .group_by(Category.id)
            .order_by(desc("record_count"))
            .options(joinedload(Category.parentCategory))
            .filter(Category.deletedAt.is_(None))
        )
        return session.execute(stmt).all()
    finally:
        session.close()


def get_category_by_id(category_id):
    """Retrieve a category by its ID."""
    session = Session()
    try:
        stmt = (
            select(Category)
            .filter_by(id=category_id)
            .filter(Category.deletedAt.is_(None))
            .options(joinedload(Category.parentCategory))
        )
        return session.scalars(stmt).first()
    finally:
        session.close()


def get_all_categories_records(
    offset: int = 0,
    offset_type: str = "month",
    is_income: bool = True,
    subcategories: bool = False,
    account_id: int = None,
):
    """
    Retrieve all categories with their net income or expenses, sorted by total amount.
    """
    session = Session()
    try:
        start_of_period, end_of_period = get_start_end_of_period(offset, offset_type)

        stmt = select(Record).options(joinedload(Record.category))
        if account_id is not None:
            stmt = stmt.filter(Record.accountId == account_id)
        stmt = stmt.filter(
            Record.date >= start_of_period,
            Record.date < end_of_period,
            Record.isIncome == is_income,
        )

        category_totals = {}
        records = session.scalars(stmt).all()
        for record in records:
            split_total = sum(split.amount for split in record.splits)
            record_amount = record.amount - split_total

            if record.category is None:
                continue

            category_id = record.categoryId
            if not subcategories and record.category.parentCategoryId:
                category_id = record.category.parentCategoryId

            if category_id not in category_totals:
                category_totals[category_id] = 0
            category_totals[category_id] += record_amount

        stmt = (
            select(Category)
            .filter(
                Category.id.in_(category_totals.keys()), Category.deletedAt.is_(None)
            )
            .options(joinedload(Category.parentCategory))
        )
        categories = session.scalars(stmt).all()
        for category in categories:
            category.amount = category_totals[category.id]

        categories = [cat for cat in categories if cat.amount != 0]
        categories.sort(key=lambda cat: cat.amount, reverse=True)

        return categories
    finally:
        session.close()


# region Create
def create_category(data):
    """Create a new category."""
    session = Session()
    try:
        new_category = Category(**data)
        session.add(new_category)
        session.commit()
        session.refresh(new_category)
        session.expunge(new_category)
        return new_category
    finally:
        session.close()


# region Update
def update_category(category_id, data):
    """Update a category by its ID."""
    session = Session()
    try:
        category = session.get(Category, category_id)
        if category:
            for key, value in data.items():
                setattr(category, key, value)
            session.commit()
            session.refresh(category)
            session.expunge(category)
        return category
    finally:
        session.close()


# region Delete
def delete_category(category_id):
    """Delete a category by marking it and its subcategories as deleted."""
    session = Session()
    try:
        category = session.get(Category, category_id)
        if category:
            category.deletedAt = datetime.now()

            # Delete subcategories
            subcategories = (
                session.query(Category).filter_by(parentCategoryId=category_id).all()
            )
            for subcategory in subcategories:
                subcategory.deletedAt = datetime.now()

            session.commit()
            session.refresh(category)
            session.expunge(category)
            return True
        return False
    finally:
        session.close()


# region Budget
def get_category_budget_rows(offset: int = 0):
    """Categories with their budget and spent this month.

    Returns a list of (category, spent_this_month, level, budget, editable):
    - top-level first (level 0), then their subcategories (level 1)
    - a parent's spent rolls up its subcategories
    - a parent's budget is the SUM of its subcategories' budgets (not editable);
      leaf categories and subcategories use their own monthlyBudget (editable)
    - income-only top-level categories (e.g. Salary) are excluded
    """
    session = Session()
    try:
        start_of_period, end_of_period = get_start_end_of_period(offset, "month")

        # own spent per category (expense records, no rollup yet)
        stmt = (
            select(Record)
            .options(joinedload(Record.category))
            .filter(
                Record.date >= start_of_period,
                Record.date < end_of_period,
                Record.isIncome == False,  # noqa: E712
                Record.isTransfer == False,  # noqa: E712
                Record.categoryId.isnot(None),
            )
        )
        own_spent: dict[int, float] = {}
        for record in session.scalars(stmt).all():
            split_total = sum(split.amount for split in record.splits)
            record_amount = record.amount - split_total
            cat_id = record.categoryId
            own_spent[cat_id] = own_spent.get(cat_id, 0.0) + record_amount

        all_categories = session.scalars(
            select(Category).filter(Category.deletedAt.is_(None))
        ).all()
        parent_of = {c.id: c.parentCategoryId for c in all_categories}

        # Classify top-level categories: those used ONLY for income (e.g. Salary)
        # are excluded from the expense budget list.
        def top_id(cat_id: int) -> int:
            while parent_of.get(cat_id) is not None:
                cat_id = parent_of[cat_id]
            return cat_id

        used_for_income: set[int] = set()
        used_for_expense: set[int] = set()
        record_rows = session.execute(
            select(Record.categoryId, Record.isIncome).filter(
                Record.categoryId.isnot(None),
                Record.isTransfer == False,  # noqa: E712
            )
        ).all()
        for cat_id, is_income in record_rows:
            if cat_id not in parent_of:
                continue
            t = top_id(cat_id)
            (used_for_income if is_income else used_for_expense).add(t)

        parents = [
            c
            for c in all_categories
            if c.parentCategoryId is None
            and not (c.id in used_for_income and c.id not in used_for_expense)
        ]
        parents.sort(key=lambda c: c.id)

        rows: list[tuple[Category, float, int, float | None, bool]] = []
        for parent in parents:
            children = [
                c for c in all_categories if c.parentCategoryId == parent.id
            ]
            children.sort(key=lambda c: c.id)
            rollup = own_spent.get(parent.id, 0.0) + sum(
                own_spent.get(c.id, 0.0) for c in children
            )
            if children:
                # Parent budget = sum of its subcategories' budgets (read-only).
                parent_budget = sum(
                    c.monthlyBudget for c in children if c.monthlyBudget is not None
                )
                rows.append((parent, round(rollup, 2), 0, parent_budget, False))
            else:
                rows.append((parent, round(rollup, 2), 0, parent.monthlyBudget, True))
            for child in children:
                rows.append((child, round(own_spent.get(child.id, 0.0), 2), 1, child.monthlyBudget, True))

        return rows
    finally:
        session.close()


def update_category_budget(category_id: int, amount: float | None):
    """Set or clear the monthly budget for a category."""
    session = Session()
    try:
        category = session.get(Category, category_id)
        if category:
            category.monthlyBudget = amount
            session.commit()
            return True
        return False
    finally:
        session.close()
# endregion
