import traceback

from django.core.exceptions import ImproperlyConfigured

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


def load_project(proj_path, app_name):

    import os, sys

    # This is so Django knows where to find stuff.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", app_name + ".settings")
    sys.path.append(proj_path)

    # This is so my local_settings.py gets loaded.
    os.chdir(proj_path)

    # This is so models get loaded.
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

V1, V2 = 'v1_my', 'v2'

BASE_PATH = '/home/lene/workspace/landmatrix'

load_project(BASE_PATH+'/land-matrix-2', 'landmatrix')
load_project(BASE_PATH+'/land-matrix', 'old_editor')


def map_classes(*args):
    for map_class in args:
        map_class.map_all(save=True)


def read_options():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--save", action='store_true',
        help="Actually save the objects created during the migration, otherwise dry run"
    )
    parser.add_argument(
        "--verbose", action='store_true', help="Print info about the migrated objects"
    )
    parser.add_argument(
        "--country", action='store_true', help="Migrate countries and regions"
    )
    parser.add_argument(
        "--produce", action='store_true', help="Migrate crops, animals and minerals"
    )
    parser.add_argument(
        "--investor", action='store_true', help="Migrate investors and relations"
    )
    parser.add_argument(
        "--deal", action='store_true', help="Migrate deals and dependent objects"
    )
    parser.add_argument(
        "--comment", action='store_true', help="Migrate comments on deals"
    )
    parser.add_argument(
        "--stuff", action='store_true', help="Migrate other tables"
    )
    parser.add_argument(
        "--activity", action='store_true', help="Migrate activities only"
    )
    parser.add_argument(
        "--old_comment", action='store_true', help="Migrate activity & stakeholder comments only"
    )
    parser.add_argument(
        "--lo", action='store_true', help="Migrate land observatory data"
    )
    parser.add_argument(
        "--all", action='store_true', help="Migrate all tables"
    )
    return parser.parse_args()


if __name__ == '__main__':

    from django.db.utils import ConnectionDoesNotExist

    try:

        from mapping import *
        from mapping.aux_functions import get_country_id_for_stakeholder
        if V1 == 'v1_pg':
            from editor.models import ActivityAttributeGroup

        options = read_options()
        print(options)

        if options.lo:
            MapLandObservatory.map_all(save=options.save, verbose=options.verbose)

        if options.old_comment:
            MapActivityAttributeGroup.map_all(save=options.save, verbose=options.verbose)
            MapComment.map_all(save=options.save, verbose=options.verbose)
            MapStakeholderInvestor.map_all(save=options.save, verbose=options.verbose)
            MapStakeholderComment.map_all(save=options.save, verbose=options.verbose)

        if options.activity:
            MapStatus._done = True
            MapActivity.map_all(save=options.save, verbose=options.verbose)
            MapActivityAttributeGroup.map_all(save=options.save, verbose=options.verbose)

        if options.deal or options.all:
            MapStatus.map_all(save=options.save, verbose=options.verbose)
            MapLanguage.map_all(save=options.save, verbose=options.verbose)
            MapActivity.map_all(save=options.save, verbose=options.verbose)
            MapActivityChangeset.map_all(save=options.save, verbose=options.verbose)
            MapActivityAttributeGroup.map_all(save=options.save, verbose=options.verbose)
            MapPublicInterfaceCache.map_all(save=options.save, verbose=options.verbose)
            MapComment.map_all(save=options.save, verbose=options.verbose)

        if options.country or options.all:
            MapCountry.map_all(save=options.save, verbose=options.verbose)

        if options.investor or options.all:
            if not MapStatus._done: MapStatus.map_all(save=options.save, verbose=options.verbose)
            MapInvestor.map_all(save=options.save, verbose=options.verbose)
            if not MapActivity._done: MapActivity.map_all(save=options.save, verbose=options.verbose)
            MapInvestorActivityInvolvement.map_all(save=options.save, verbose=options.verbose)
            MapStakeholderInvestor.map_all(save=options.save, verbose=options.verbose)
            MapStakeholderVentureInvolvement.map_all(save=options.save, verbose=options.verbose)
            MapStakeholderComment.map_all(save=options.save, verbose=options.verbose)

        if options.comment or options.all:
            MapDjangoComments.map_all(save=options.save, verbose=options.verbose)
            MapThreadedComments.map_all(save=options.save, verbose=options.verbose)

        if options.produce or options.all:
            MapAgriculturalProduce.map_all(save=options.save, verbose=options.verbose)
            MapCrop.map_all(save=options.save, verbose=options.verbose)
            MapAnimal.map_all(save=options.save, verbose=options.verbose)
            MapMineral.map_all(save=options.save, verbose=options.verbose)
            MapCurrency.map_all(save=options.save, verbose=options.verbose)

        if options.stuff or options.all:
            MapBrowseRule.map_all(save=options.save, verbose=options.verbose)
            MapBrowseCondition.map_all(save=options.save, verbose=options.verbose)

        # a number of possible uses listed here as examples
        if False:
            for map_class in [
                MapLanguage, MapStatus,
                MapActivity,
                MapActivityAttributeGroup,
                MapRegion,
                MapCountry,
                MapBrowseRule, MapBrowseCondition,
                MapAgriculturalProduce, MapCrop,
                MapComment,
                MapInvestor, MapInvestorActivityInvolvement,
                MapStakeholderInvestor,
            ]:
                map_class.map_all(save=True)

        if False:
            MapActivity._done = True
            MapLanguage._done = True
            MapActivityAttributeGroup.map_all(save=True)
            MapAgriculturalProduce.map_all(save=True)
            MapCrop.map_all(save=True)

        if False:   # example for migrating just one record
            MapActivityAttributeGroup.map(ActivityAttributeGroup.objects.using(V1).last().id)

    except ConnectionDoesNotExist as e:
        print('You need to set CONVERT_DB to True in settings.py!')
        print(e)
    # except AttributeError as e:
    #     print('You need to check out branch "postgres" of the old land-matrix project under')
    #     print(BASE_PATH+'/land-matrix!')
    #     print(e)
    except (AttributeError, ImportError) as e:
        print('To migrate the original MySQL data you need to check out branch "master" of the')
        print('old land-matrix project under '+BASE_PATH+'/land-matrix!')
        print(e)
        raise
    except ImproperlyConfigured:
        print('Do a "pip install mysqlclient" to install mysql drivers!')