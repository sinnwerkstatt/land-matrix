from typing import Any

from django.utils import translation
from graphql import GraphQLResolveInfo

from apps.landmatrix.forms.deal import DealForm
from apps.landmatrix.forms.deal_submodels import (
    LocationForm,
    ContractForm,
    DataSourceForm,
)
from apps.landmatrix.forms.investor import InvestorForm, InvestorVentureInvolvementForm


def resolve_formfields(obj: Any, info: GraphQLResolveInfo, language="en"):
    with translation.override(language):
        return {
            "deal": DealForm().get_fields(),
            "location": LocationForm().get_fields(),
            "contract": ContractForm().get_fields(),
            "datasource": DataSourceForm().get_fields(),
            "investor": InvestorForm().get_fields(),
            "involvement": InvestorVentureInvolvementForm().get_fields(),
        }
