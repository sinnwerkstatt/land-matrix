import mock

from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from grid.templatetags.custom_tags import get_user_role
from django.test import TestCase, RequestFactory

from api.elasticsearch import es_search
from landmatrix.models.investor import InvestorBase


class TestDealBase(TestCase):

    fixtures = [
        'languages',
        'countries_and_regions',
        'users_and_groups',
        'status',
        'investors',
        'venture_involvements',
    ]

    DEAL_DATA = {
        # Location
        "location-TOTAL_FORMS": 1,
        "location-INITIAL_FORMS": 0,
        "location-MIN_NUM_FORMS": 1,
        "location-MAX_NUM_FORMS": 1,
        "location-0-level_of_accuracy": "Exact location",
        "location-0-location": "Rakhaing-Staat, Myanmar (Birma)",
        "location-0-location-map": "Rakhaing-Staat, Myanmar (Birma)",
        "location-0-point_lat": 19.810093,
        "location-0-point_lon": 93.98784269999999,
        "location-0-target_country": 104,
        # General info
        "id_negotiation_status_0": "Contract signed",
        "id_negotiation_status_1": None,
        "id_negotiation_status_2": None,
        # Contract
        "contract-TOTAL_FORMS": 0,
        "contract-INITIAL_FORMS": 0,
        "contract-MIN_NUM_FORMS": 0,
        "contract-MAX_NUM_FORMS": 0,
        # Data source
        "data_source-TOTAL_FORMS": 1,
        "data_source-INITIAL_FORMS": 0,
        "data_source-MIN_NUM_FORMS": 1,
        "data_source-MAX_NUM_FORMS": 1,
        "data_source-0-type": "Media report",
        # Investor
        "operational_stakeholder": 10,
    }
    INVESTOR_CREATED = 20
    INVESTOR_UPDATED = 31

    def setUp(self):
        self.users = {
            'reporter': User.objects.get(username='reporter'),
            'editor': User.objects.get(username='editor'),
            'administrator': User.objects.get(username='administrator'),
        }
        self.groups = {
            'reporter': Group.objects.get(name='Reporters'),
            'editor': Group.objects.get(name='Editors'),
            'administrator': Group.objects.get(name='Administrators'),
        }
        self.factory = RequestFactory()

        # Create group permissions
        # This not possible in fixtures, because permissions and content types are created on run-time
        perm_review_activity = Permission.objects.get(codename='review_activity')
        perm_review_investor = Permission.objects.get(codename='review_investor')
        self.groups['editor'].permissions.add(perm_review_activity)
        self.groups['editor'].permissions.add(perm_review_investor)
        perm_add_activity = Permission.objects.get(codename='add_activity')
        perm_change_activity = Permission.objects.get(codename='change_activity')
        perm_delete_activity = Permission.objects.get(codename='delete_activity')
        perm_add_investor = Permission.objects.get(codename='add_investor')
        perm_change_investor = Permission.objects.get(codename='change_investor')
        perm_delete_investor = Permission.objects.get(codename='delete_investor')
        self.groups['administrator'].permissions.add(perm_review_activity)
        self.groups['administrator'].permissions.add(perm_review_investor)
        self.groups['administrator'].permissions.add(perm_add_activity)
        self.groups['administrator'].permissions.add(perm_change_activity)
        self.groups['administrator'].permissions.add(perm_delete_activity)
        self.groups['administrator'].permissions.add(perm_add_investor)
        self.groups['administrator'].permissions.add(perm_change_investor)
        self.groups['administrator'].permissions.add(perm_delete_investor)

        settings.CELERY_ALWAYS_EAGER = True
        settings.ELASTICSEARCH_INDEX_NAME = 'landmatrix_test'

        es_search.create_index()

    def get_username_and_role(self, user):
        """
        Get username and role for specified user (for comparison in dashboard/manage section)
        :return:
        """
        user = self.users[user].username
        role = get_user_role(self.users[user])
        if role:
            user += ' (%s)' % role
        return user

    def run_commit_hooks(self):
        """
        Fake transaction commit to run delayed on_commit functions
        see: https://medium.com/gitux/speed-up-django-transaction-hooks-tests-6de4a558ef96
        :return:
        """
        for db_name in reversed(self._databases_names()):
            with mock.patch('django.db.backends.base.base.BaseDatabaseWrapper.validate_no_atomic_block', lambda a: False):
                transaction.get_connection(using=db_name).run_and_clear_commit_hooks()

    def assert_deal_in_list(self, response, activity, role=None):
        items = list(filter(lambda i: i['history_id'] == activity.id, response.context_data['items']))
        self.assertEqual(len(items), 1, msg='Deal does not appear in Manage section')
        if role:
            self.assertEqual(items[0]['user'], self.get_username_and_role(role),
                             msg='Deal has wrong user in Manage section')

    def assert_deal_not_in_list(self, response, activity):
        items = list(filter(lambda i: i['history_id'] == activity.id, response.context_data['items']))
        self.assertEqual(len(items), 0, msg='Deal does appear in Manage section (but it should not)')

    @staticmethod
    def _get_investors(involvements):
        """
        Get investor chain for involvements
        :param involvements:
        :return:
        """
        investors = set()
        for involvement in involvements:
            investor = involvement.fk_investor
            if not investor or investor in investors:
                continue
            investors.add(investor)
            if investor.venture_involvements.count() > 0:
                investors.update(TestDealBase._get_investors(investor.venture_involvements.all()))
        return investors

    @staticmethod
    def _get_investor_status_list(involvements):
        """
        Get investor statuses of investor chain
        :param involvements:
        :return:
        """
        return set([i.fk_status_id for i in TestDealBase._get_investors(involvements)])

    def assert_investors_approved(self, activity):
        """
        Assert investors have been approved with deal approval
        :param activity:
        :param approved:
        :return:
        """
        investor_status = TestDealBase._get_investor_status_list(activity.involvements.all())
        self.assertNotIn(InvestorBase.STATUS_PENDING, investor_status,
                         msg='Pending investors have not been approved with deal approval')

    def assert_investors_not_approved(self, activity):
        """
        Assert investors have not been approved with deal approval
        :param activity:
        :param approved:
        :return:
        """
        investor_status = TestDealBase._get_investor_status_list(activity.involvements.all())
        self.assertIn(InvestorBase.STATUS_PENDING, investor_status,
                      msg='Pending investors have been approved with deal approval (but they should not)')


class TestInvestorBase(TestDealBase):

    INVESTOR_DATA = {
        # Investor
        "name": "Testinvestor",
        "fk_country": "104",
        "classification": "10",
        "homepage": "https://www.example.com",
        #"opencorporates_link": None,
        "comment": "Test comment",
        # Parent companies
        "parent-company-form-TOTAL_FORMS": 1,
        "parent-company-form-INITIAL_FORMS": 0,
        "parent-company-form-MIN_NUM_FORMS": 0,
        "parent-company-form-MAX_NUM_FORMS": 1,
        "parent-company-form-0-fk_investor": "10",
        "parent-company-form-0-percentage": 100,
        "parent-company-form-0-loans_amount": 0,
        "parent-company-form-0-loans_date": None,
        "parent-company-form-0-comment": "Test comment",
        "parent-company-form-0-id": "",
        "parent-company-form-0-DELETE": None,
        # Tertiary investors/lenders
        "parent-investor-form-TOTAL_FORMS": 0,
        "parent-investor-form-INITIAL_FORMS": 0,
        "parent-investor-form-MIN_NUM_FORMS": 0,
        "parent-investor-form-MAX_NUM_FORMS": 1,
        "parent-investor-form-0-fk_investor": None,
        "parent-investor-form-0-percentage": None,
        "parent-investor-form-0-loans_amount": None,
        "parent-investor-form-0-loans_date": None,
        "parent-investor-form-0-comment": None,
        "parent-investor-form-0-id": None,
        "parent-investor-form-0-DELETE": None,
    }

    def assert_investor_in_list(self, response, investor, role=None):
        items = list(filter(lambda i: i['history_id'] == investor.id, response.context_data['items']))
        self.assertEqual(len(items), 1, msg='Investor does not appear in Manage section')
        if role:
            self.assertEqual(items[0]['user'], self.get_username_and_role(role),
                             msg='Deal has wrong user in Manage section')

    def assert_investor_not_in_list(self, response, investor):
        items = list(filter(lambda i: i['history_id'] == investor.id, response.context_data['items']))
        self.assertEqual(len(items), 0, msg='Investor does appear in Manage section (but it should not)')