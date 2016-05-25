
from landmatrix.models.activity_attribute_group import ActivityAttributeGroup
from landmatrix.models.investor import Investor
from .land_observatory_objects.tag_groups import A_Tag_Group, SH_Tag_Group
from .land_observatory_objects.stakeholder import Stakeholder
from .land_observatory_objects.changeset import Changeset
from .land_observatory_objects.involvement import Involvement
from .map_lo_model import MapLOModel
from .map_lo_activities import MapLOActivities

from migrate import V2

from django.db import transaction

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class MapLandObservatory:
    """
    Preparing the land observatory data:
    cat cdelokp-unibe-ch_data_20160510.backup | sed s/lokpeditor/<db_user>/g > cdelokp-unibe-ch_data_20160510.backup.lm
    pg_restore -c cdelokp-unibe-ch_data_20160510.backup.lm
    psql -U<db_user> -c 'ALTER USER <db_user> SET SEARCH_PATH = data, public;'
    """

    @classmethod
    @transaction.atomic(using=V2)
    def map_all(cls, save=False, verbose=False):
        MapLOActivities.map_all(save, verbose)
        # MapLOStakeholders.map_all(save, verbose)
        # MapLOSTagGroups.map_all(save, verbose)
        # MapLOChangesets.map_all(save, verbose)
        # MapLOInvolvements.map_all(save, verbose)


class MapLOATagGroups(MapLOModel):

    old_class = A_Tag_Group
    new_class = ActivityAttributeGroup

    @classmethod
    def all_records(cls):
        return A_Tag_Group.objects.using('lo').all().values()

    @classmethod
    def save_record(cls, new, save):
        print(new)


class MapLOStakeholders(MapLOModel):

    old_class = Stakeholder
    new_class = Investor

    @classmethod
    def all_records(cls):
        return Stakeholder.objects.using('lo').all().values()

    @classmethod
    def save_record(cls, new, save):
        print(new)


class MapLOSTagGroups(MapLOModel):

    old_class = SH_Tag_Group
    new_class = Investor

    @classmethod
    def all_records(cls):
        return SH_Tag_Group.objects.using('lo').all().values()

    @classmethod
    def save_record(cls, new, save):
        print(new)


class MapLOChangesets(MapLOModel):

    old_class = Changeset

    @classmethod
    def all_records(cls):
        return Changeset.objects.using('lo').all().values()

    @classmethod
    def save_record(cls, new, save):
        print(new)


class MapLOInvolvements(MapLOModel):

    old_class = Involvement

    @classmethod
    def all_records(cls):
        return Involvement.objects.using('lo').all().values()

    @classmethod
    def save_record(cls, new, save):
        print(new)