import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bagels.managers import service_accounts
from bagels.models.database.db import Base


@pytest.fixture(scope="function")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service_accounts.Session = sessionmaker(bind=engine)
    yield engine
    Base.metadata.drop_all(engine)


def test_create_and_list_service_accounts(test_db):
    created = service_accounts.create_service_account(
        {
            "provider": "Enel",
            "accountNumber": "00123-45",
            "alias": "Casa",
            "notes": "Medidor principal",
        }
    )

    entries = service_accounts.get_all_service_accounts()

    assert created.id is not None
    assert created.provider == "Enel"
    assert created.accountNumber == "00123-45"
    assert created.alias == "Casa"
    assert entries[0].id == created.id


def test_duplicate_provider_and_number_is_rejected(test_db):
    service_accounts.create_service_account(
        {"provider": "Enel", "accountNumber": "123"}
    )

    with pytest.raises(ValueError, match="already exists"):
        service_accounts.create_service_account(
            {"provider": "enel", "accountNumber": "123"}
        )


def test_update_service_account(test_db):
    created = service_accounts.create_service_account(
        {"provider": "Enel", "accountNumber": "123"}
    )

    updated = service_accounts.update_service_account(
        created.id,
        {"provider": "Aguas Andinas", "accountNumber": "456", "alias": "Casa"},
    )

    assert updated.provider == "Aguas Andinas"
    assert updated.accountNumber == "456"
    assert updated.alias == "Casa"
    assert updated.notes is None


def test_delete_archives_service_account(test_db):
    created = service_accounts.create_service_account(
        {"provider": "Enel", "accountNumber": "123"}
    )

    assert service_accounts.delete_service_account(created.id) is True
    assert service_accounts.get_all_service_accounts() == []
    assert service_accounts.delete_service_account(created.id) is False
