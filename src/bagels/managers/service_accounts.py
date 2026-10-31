from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from bagels.models.database.app import db_engine
from bagels.models.service_account import ServiceAccount

Session = sessionmaker(bind=db_engine)


def _required_value(data: dict, key: str) -> str:
    value = str(data.get(key, "") or "").strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _optional_value(value) -> str | None:
    value = str(value or "").strip()
    return value or None


def _normalized_data(data: dict) -> dict:
    return {
        "provider": _required_value(data, "provider"),
        "accountNumber": _required_value(data, "accountNumber"),
        "alias": _optional_value(data.get("alias")),
        "notes": _optional_value(data.get("notes")),
    }


def _find_duplicate(session, provider: str, account_number: str, exclude_id=None):
    stmt = select(ServiceAccount).where(
        ServiceAccount.deletedAt.is_(None),
        func.lower(ServiceAccount.provider) == provider.casefold(),
        func.lower(ServiceAccount.accountNumber) == account_number.casefold(),
    )
    if exclude_id is not None:
        stmt = stmt.where(ServiceAccount.id != exclude_id)
    return session.scalar(stmt)


# region Create


def create_service_account(data: dict) -> ServiceAccount:
    payload = _normalized_data(data)
    session = Session()
    try:
        if _find_duplicate(session, payload["provider"], payload["accountNumber"]):
            raise ValueError(
                "A service account with this provider and number already exists"
            )
        entry = ServiceAccount(**payload)
        session.add(entry)
        session.commit()
        session.refresh(entry)
        session.expunge(entry)
        return entry
    finally:
        session.close()


# region Read


def get_all_service_accounts() -> list[ServiceAccount]:
    session = Session()
    try:
        stmt = (
            select(ServiceAccount)
            .where(ServiceAccount.deletedAt.is_(None))
            .order_by(ServiceAccount.provider, ServiceAccount.alias, ServiceAccount.id)
        )
        return list(session.scalars(stmt).all())
    finally:
        session.close()


def get_service_account_by_id(account_id: int) -> ServiceAccount | None:
    session = Session()
    try:
        return session.get(ServiceAccount, account_id)
    finally:
        session.close()


# region Update


def update_service_account(account_id: int, data: dict) -> ServiceAccount | None:
    session = Session()
    try:
        entry = session.get(ServiceAccount, account_id)
        if not entry or entry.deletedAt is not None:
            return None

        merged = {
            "provider": data.get("provider", entry.provider),
            "accountNumber": data.get("accountNumber", entry.accountNumber),
            "alias": data.get("alias", entry.alias),
            "notes": data.get("notes", entry.notes),
        }
        payload = _normalized_data(merged)
        if _find_duplicate(
            session,
            payload["provider"],
            payload["accountNumber"],
            exclude_id=account_id,
        ):
            raise ValueError(
                "A service account with this provider and number already exists"
            )

        for key, value in payload.items():
            setattr(entry, key, value)
        session.commit()
        session.refresh(entry)
        session.expunge(entry)
        return entry
    finally:
        session.close()


# region Delete


def delete_service_account(account_id: int) -> bool:
    session = Session()
    try:
        entry = session.get(ServiceAccount, account_id)
        if not entry or entry.deletedAt is not None:
            return False
        entry.deletedAt = datetime.now()
        session.commit()
        return True
    finally:
        session.close()
