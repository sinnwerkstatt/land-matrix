__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from landmatrix.models import Activity, ActivityAttributeGroup, Involvement, PrimaryInvestor, Stakeholder, StakeholderAttributeGroup, Country

from django.db.models import Max


class Deal:

    def __init__(self, id):
        self.id = id

        activity = get_latest_activity(id)
        self.attributes = get_activity_attributes(activity)

        primary_investor_ids, stakeholder_ids = get_pi_and_sh_id(activity)

        self.primary_investor = PrimaryInvestor.objects.filter(id__in=primary_investor_ids).last()

        sh = Stakeholder.objects.filter(id__in=stakeholder_ids).last()
        self.stakeholder = get_stakeholder_attributes(sh)


def get_latest_activity(deal_id):
    version_max = _get_latest_version(deal_id)
    return Activity.objects.filter(activity_identifier=deal_id, version=version_max).last()


def get_activity_attributes(activity):
    attributes = ActivityAttributeGroup.objects.filter(fk_activity=activity).values('attributes')
    attributes_list = [a['attributes'] for a in attributes]
    return aggregate_activity_attributes(attributes_list, {})


def get_pi_and_sh_id(activity):
    queryset = Involvement.objects.select_related().filter(fk_activity=activity)
    involvements = queryset.values('fk_primary_investor_id', 'fk_stakeholder_id')
    return [i['fk_primary_investor_id'] for i in involvements], [i['fk_stakeholder_id'] for i in involvements]


def aggregate_activity_attributes(attributes_list, already_set_attributes):
    if not attributes_list:
        return already_set_attributes

    for key, value in attributes_list.pop(0).items():
        update_attributes(already_set_attributes, key, value)

    return aggregate_activity_attributes(attributes_list, already_set_attributes)


def update_attributes(attributes, key, value):
    if key in ['type', 'url', 'file']:
        attributes[key] = attributes.get(key, []) + [value]
    else:
        attributes[key] = resolve_country(key, value)


def resolve_country(key, value):
    return Country.objects.get(id=int(value)).name if 'country' in key else value


def get_stakeholder_attributes(stakeholder):
    attributes = StakeholderAttributeGroup.objects.filter(fk_stakeholder=stakeholder).values('attributes')
    return {key: resolve_country(key, value) for a in attributes for key, value in a['attributes'].items()}


def _get_latest_version(deal_id):
    return Activity.objects.filter(activity_identifier=deal_id).values().aggregate(Max('version'))['version__max']


def _get_latest_stakeholder_version(deal_id):
    return Activity.objects.filter(activity_identifier=deal_id).values().aggregate(Max('version'))['version__max']

