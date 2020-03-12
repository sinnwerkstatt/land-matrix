from typing import Any

from graphql import GraphQLResolveInfo

from apps.greennewdeal.documents import InvestorDocument


def get_fields(info: GraphQLResolveInfo):
    fields = set()
    for fnode in info.field_nodes:
        fields.update({f.name.value for f in fnode.selection_set.selections})
    return list(fields)


def resolve_investor(obj: Any, info: GraphQLResolveInfo, id):
    investor = InvestorDocument.search().filter("term", id=id)

    fields = get_fields(info)
    if fields:
        investor.source(fields)

    return list(investor)[0]


def resolve_investors(obj: Any, info: GraphQLResolveInfo, sort):
    investors = InvestorDocument.search().filter("terms", status=[2, 3]).sort(sort)

    fields = get_fields(info)
    if fields:
        investors.source(fields)

    return list(investors[:100])
