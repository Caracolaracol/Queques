import copy

from bagels.forms.form import Form, FormField
from bagels.managers.service_accounts import get_service_account_by_id


class ServiceAccountForm:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    FORM = Form(
        fields=[
            FormField(
                placeholder="Enel",
                title="Provider",
                key="provider",
                type="string",
                is_required=True,
            ),
            FormField(
                placeholder="Número de cliente o cuenta",
                title="Account number",
                key="accountNumber",
                type="string",
                is_required=True,
            ),
            FormField(
                placeholder="(Optional) Casa, oficina, etc.",
                title="Alias",
                key="alias",
                type="string",
            ),
            FormField(
                placeholder="(Optional) Notes",
                title="Notes",
                key="notes",
                type="string",
            ),
        ]
    )

    def get_form(self):
        return copy.deepcopy(self.FORM)

    def get_filled_form(self, account_id: int):
        form = copy.deepcopy(self.FORM)
        account = get_service_account_by_id(account_id)
        if account is None:
            return form
        for field in form.fields:
            value = getattr(account, field.key)
            field.default_value = str(value) if value is not None else ""
        return form
