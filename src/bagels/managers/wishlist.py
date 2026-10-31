from sqlalchemy import delete, func, select
from sqlalchemy.orm import sessionmaker

from bagels.models.database.app import db_engine
from bagels.models.wishlist import WishlistItem

Session = sessionmaker(bind=db_engine)


# region Get
def get_wishlist_items():
    """All wishlist items in priority order (position, then id)."""
    session = Session()
    try:
        _backfill_positions(session)
        stmt = select(WishlistItem).order_by(
            WishlistItem.position, WishlistItem.id
        )
        return list(session.scalars(stmt).all())
    finally:
        session.close()


# region Write
def add_wishlist_item(item: str) -> WishlistItem | None:
    """Add a new wishlist item at the bottom of the priority order."""
    session = Session()
    try:
        _backfill_positions(session)
        max_position = session.scalar(select(func.max(WishlistItem.position)))
        entry = WishlistItem(item=item.strip(), position=(max_position or 0) + 1)
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry
    finally:
        session.close()


def move_wishlist_item(item_id: int, direction: int) -> bool:
    """Reorder an item by swapping its position with the neighbour.

    `direction` is -1 to move up (toward the top / higher priority) or +1 to
    move down. Returns `False` when the item doesn't exist or is already at
    the edge of the list.
    """
    session = Session()
    try:
        _backfill_positions(session)
        items = list(
            session.scalars(
                select(WishlistItem).order_by(
                    WishlistItem.position, WishlistItem.id
                )
            ).all()
        )
        idx = next((i for i, entry in enumerate(items) if entry.id == item_id), None)
        if idx is None:
            return False
        neighbor_idx = idx + direction
        if neighbor_idx < 0 or neighbor_idx >= len(items):
            return False
        items[idx].position, items[neighbor_idx].position = (
            items[neighbor_idx].position,
            items[idx].position,
        )
        session.commit()
        return True
    finally:
        session.close()


def toggle_wishlist_item(item_id: int) -> bool:
    """Toggle the done state of a wishlist item."""
    session = Session()
    try:
        entry = session.get(WishlistItem, item_id)
        if not entry:
            return False
        entry.done = not entry.done
        session.commit()
        return True
    finally:
        session.close()


def delete_wishlist_item(item_id: int) -> bool:
    """Delete a wishlist item."""
    session = Session()
    try:
        entry = session.get(WishlistItem, item_id)
        if not entry:
            return False
        session.delete(entry)
        session.commit()
        return True
    finally:
        session.close()


# region Helpers
def _backfill_positions(session) -> None:
    """One-time self-healing for rows that predate the `position` column.

    The schema auto-migrates (`ALTER TABLE ... ADD COLUMN`) but existing rows
    come back with NULL position. Give them their id so the first fetch sees a
    stable order (creation order, as before this feature).
    """
    has_null = session.scalar(
        select(WishlistItem.id).where(WishlistItem.position.is_(None)).limit(1)
    )
    if has_null is None:
        return
    for entry in session.scalars(select(WishlistItem)).all():
        if entry.position is None:
            entry.position = entry.id
    session.commit()