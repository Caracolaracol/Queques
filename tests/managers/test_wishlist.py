import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bagels.models.database.db import Base
from bagels.models.wishlist import WishlistItem
from bagels.managers import wishlist


@pytest.fixture(scope="function")
def test_db():
    # In-memory SQLite, session factory swapped in (same pattern as the other
    # manager tests) so nothing touches the real database.
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    wishlist.Session = sessionmaker(bind=engine)
    yield engine
    Base.metadata.drop_all(engine)


def _items():
    return [entry.item for entry in wishlist.get_wishlist_items()]


def test_add_keeps_insertion_order(test_db):
    wishlist.add_wishlist_item("c")
    wishlist.add_wishlist_item("a")
    wishlist.add_wishlist_item("b")
    assert _items() == ["c", "a", "b"]


def test_move_down_swaps_with_next_item(test_db):
    for item in ["a", "b", "c"]:
        wishlist.add_wishlist_item(item)
    items = wishlist.get_wishlist_items()
    assert wishlist.move_wishlist_item(items[0].id, 1) is True
    assert _items() == ["b", "a", "c"]


def test_move_up_swaps_with_previous_item(test_db):
    for item in ["a", "b", "c"]:
        wishlist.add_wishlist_item(item)
    items = wishlist.get_wishlist_items()
    assert wishlist.move_wishlist_item(items[2].id, -1) is True
    assert _items() == ["a", "c", "b"]


def test_move_at_edges_is_a_noop(test_db):
    for item in ["a", "b"]:
        wishlist.add_wishlist_item(item)
    items = wishlist.get_wishlist_items()
    assert wishlist.move_wishlist_item(items[0].id, -1) is False
    assert wishlist.move_wishlist_item(items[-1].id, 1) is False
    assert _items() == ["a", "b"]


def test_move_unknown_item_is_false(test_db):
    assert wishlist.move_wishlist_item(999, 1) is False


def test_backfill_orders_pre_existing_rows_by_id(test_db):
    # Rows that predate the `position` column come back with NULL position.
    session = wishlist.Session()
    try:
        session.add_all([WishlistItem(item="x"), WishlistItem(item="y")])
        session.commit()
    finally:
        session.close()
    assert _items() == ["x", "y"]
    items = wishlist.get_wishlist_items()
    assert all(entry.position is not None for entry in items)


def test_moves_work_after_backfill(test_db):
    session = wishlist.Session()
    try:
        session.add_all([WishlistItem(item="x"), WishlistItem(item="y")])
        session.commit()
    finally:
        session.close()
    items = wishlist.get_wishlist_items()
    assert wishlist.move_wishlist_item(items[0].id, 1) is True
    assert _items() == ["y", "x"]


def test_done_state_is_preserved_when_moving(test_db):
    wishlist.add_wishlist_item("a")
    wishlist.add_wishlist_item("b")
    items = wishlist.get_wishlist_items()
    wishlist.toggle_wishlist_item(items[0].id)
    assert wishlist.move_wishlist_item(items[0].id, 1) is True
    after = wishlist.get_wishlist_items()
    assert after[0].item == "b"
    assert after[1].done is True