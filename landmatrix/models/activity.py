import re
from collections import defaultdict

from django.db.models.fields import BLANK_CHOICE_DASH
from django.db.models.functions import Coalesce
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.conf import settings

from landmatrix.models.default_string_representation import DefaultStringRepresentation
from landmatrix.models.activity_attribute_group import ActivityAttribute
from landmatrix.models.investor import Investor, InvestorActivityInvolvement, InvestorBase, \
    HistoricalInvestorVentureInvolvement
from landmatrix.models.country import Country
from landmatrix.models.crop import Crop
from grid.forms.choices import NATURE_CONCESSION, INTENTION_FOREST_LOGGING


class ActivityQuerySet(models.QuerySet):
    def public(self, user=None):
        '''
        Status public, not to be confused with is_public.
        '''
        if user and user.is_authenticated():
            return self.filter(models.Q(fk_status_id__in=ActivityBase.PUBLIC_STATUSES) |
                               models.Q(history_user=user))
        else:
            return self.filter(fk_status_id__in=ActivityBase.PUBLIC_STATUSES)

    def public_or_deleted(self, user=None):
        statuses = ActivityBase.PUBLIC_STATUSES + (
            ActivityBase.STATUS_DELETED,
        )
        if user and user.is_authenticated():
            return self.filter(models.Q(fk_status_id__in=statuses) |
                        models.Q(history_user=user))
        else:
            return self.filter(fk_status_id__in=statuses)

    def public_or_pending(self):
        statuses = ActivityBase.PUBLIC_STATUSES + (
            ActivityBase.STATUS_PENDING,
        )
        return self.filter(fk_status_id__in=statuses)

    def public_deleted_or_pending(self):
        statuses = ActivityBase.PUBLIC_STATUSES + (
            ActivityBase.STATUS_DELETED,
            ActivityBase.STATUS_PENDING,
        )
        return self.filter(fk_status_id__in=statuses)

    def pending(self):
        statuses = (ActivityBase.STATUS_PENDING, ActivityBase.STATUS_TO_DELETE)
        return self.filter(fk_status_id__in=statuses)

    def pending_only(self):
        return self.filter(fk_status_id=ActivityBase.STATUS_PENDING)

    def active(self):
        return self.filter(fk_status_id=ActivityBase.STATUS_ACTIVE)

    def overwritten(self):
        return self.filter(fk_status_id=ActivityBase.STATUS_OVERWRITTEN)

    def to_delete(self):
        return self.filter(fk_status_id=ActivityBase.STATUS_TO_DELETE)

    def deleted(self):
        return self.filter(fk_status_id=ActivityBase.STATUS_DELETED)

    def rejected(self):
        return self.filter(fk_status_id=ActivityBase.STATUS_REJECTED)

    def activity_identifier_count(self):
        return self.order_by('-id').values('activity_identifier').distinct().count()

    def overall_activity_count(self):
        return self.public().activity_identifier_count()

    def public_activity_count(self):
        return self.public().filter(is_public=False).activity_identifier_count()


class NegotiationStatusManager(models.Manager):
    '''
    Manager for Negotiation status grouped query. (used by API call)
    '''

    def get_queryset(self):
        deals_count = Coalesce(
            models.Count('activity_identifier'), models.Value(0))
        hectares_sum = Coalesce(models.Sum('deal_size'), models.Value(0))

        queryset = ActivityQuerySet(self.model, using=self._db)
        queryset = queryset.exclude(negotiation_status__isnull=True)
        queryset = queryset.values('negotiation_status')
        queryset = queryset.annotate(
            deals_count=deals_count, hectares_sum=hectares_sum)
        queryset = queryset.distinct()

        return queryset


class ActivityBase(DefaultStringRepresentation, models.Model):
    ACTIVITY_IDENTIFIER_DEFAULT = 2147483647  # Max safe int

    # FIXME: Replace fk_status with Choice Field
    STATUS_PENDING = 1
    STATUS_ACTIVE = 2
    STATUS_OVERWRITTEN = 3
    STATUS_DELETED = 4
    STATUS_REJECTED = 5
    STATUS_TO_DELETE = 6
    PUBLIC_STATUSES = (STATUS_ACTIVE, STATUS_OVERWRITTEN)
    STATUS_CHOICES = (
        (STATUS_PENDING, _('Pending')),
        (STATUS_ACTIVE, _('Active')),
        (STATUS_OVERWRITTEN, _('Overwritten')),
        (STATUS_DELETED, _('Deleted')),
        (STATUS_REJECTED, _('Rejected')),
        (STATUS_TO_DELETE, _('To delete')),
    )

    DEAL_SCOPE_DOMESTIC = 'domestic'
    DEAL_SCOPE_TRANSNATIONAL = 'transnational'
    DEAL_SCOPE_CHOICES = (
        (DEAL_SCOPE_DOMESTIC, _('Domestic')),
        (DEAL_SCOPE_DOMESTIC, _('Transnational')),
    )

    NEGOTIATION_STATUS_EXPRESSION_OF_INTEREST = 'Expression of interest'
    NEGOTIATION_STATUS_UNDER_NEGOTIATION = 'Under negotiation'
    NEGOTIATION_STATUS_MEMO_OF_UNDERSTANDING = 'Memorandum of understanding'
    NEGOTIATION_STATUS_ORAL_AGREEMENT = 'Oral agreement'
    NEGOTIATION_STATUS_CONTRACT_SIGNED = 'Contract signed'
    NEGOTIATION_STATUS_NEGOTIATIONS_FAILED = 'Negotiations failed'
    NEGOTIATION_STATUS_CONTRACT_CANCELLED = 'Contract canceled'
    NEGOTIATION_STATUS_CONTRACT_EXPIRED = 'Contract expired'
    NEGOTIATION_STATUS_CHANGE_OF_OWNERSHIP = 'Change of ownership'

    # These groupings are used for determining filter behaviour
    NEGOTIATION_STATUSES_INTENDED = (
        NEGOTIATION_STATUS_EXPRESSION_OF_INTEREST,
        NEGOTIATION_STATUS_UNDER_NEGOTIATION,
        NEGOTIATION_STATUS_MEMO_OF_UNDERSTANDING,
    )
    NEGOTIATION_STATUSES_CONCLUDED = (
        NEGOTIATION_STATUS_ORAL_AGREEMENT,
        NEGOTIATION_STATUS_CONTRACT_SIGNED,
    )
    NEGOTIATION_STATUSES_FAILED = (
        NEGOTIATION_STATUS_NEGOTIATIONS_FAILED,
        NEGOTIATION_STATUS_CONTRACT_CANCELLED,
        NEGOTIATION_STATUS_CONTRACT_EXPIRED,
    )
    NEGOTIATION_STATUS_CHOICES = (
        BLANK_CHOICE_DASH[0],
        (
            NEGOTIATION_STATUS_EXPRESSION_OF_INTEREST,
            _("Intended (Expression of interest)"),
        ),
        (
            NEGOTIATION_STATUS_UNDER_NEGOTIATION,
            _("Intended (Under negotiation)"),
        ),
        (
            NEGOTIATION_STATUS_MEMO_OF_UNDERSTANDING,
            _("Intended (Memorandum of understanding)"),
        ),
        (
            NEGOTIATION_STATUS_ORAL_AGREEMENT,
            _("Concluded (Oral Agreement)"),
        ),
        (
            NEGOTIATION_STATUS_CONTRACT_SIGNED,
            _("Concluded (Contract signed)"),
        ),
        (
            NEGOTIATION_STATUS_NEGOTIATIONS_FAILED,
            _("Failed (Negotiations failed)"),
        ),
        (
            NEGOTIATION_STATUS_CONTRACT_CANCELLED,
            _("Failed (Contract cancelled)"),
        ),
        (
            NEGOTIATION_STATUS_CONTRACT_EXPIRED, _("Contract expired"),
        ),
        (
            NEGOTIATION_STATUS_CHANGE_OF_OWNERSHIP, _("Change of ownership"),
        )
    )

    IMPLEMENTATION_STATUS_PROJECT_NOT_STARTED = 'Project not started'
    IMPLEMENTATION_STATUS_STARTUP_PHASE = 'Startup phase (no production)'
    IMPLEMENTATION_STATUS_IN_OPERATION = 'In operation (production)'
    IMPLEMENTATION_STATUS_PROJECT_ABANDONED = 'Project abandoned'
    IMPLEMENTATION_STATUS_CHOICES = (
        BLANK_CHOICE_DASH[0],
        (
            IMPLEMENTATION_STATUS_PROJECT_NOT_STARTED,
            _("Project not started"),
        ),
        (
            IMPLEMENTATION_STATUS_STARTUP_PHASE,
            _("Startup phase (no production)"),
        ),
        (
            IMPLEMENTATION_STATUS_IN_OPERATION,
            _("In operation (production)"),
        ),
        (
            IMPLEMENTATION_STATUS_PROJECT_ABANDONED,
            _("Project abandoned"),
        ),
    )

    AGRICULTURAL_PRODUCE_MULTI = 'Multi Crop'

    activity_identifier = models.IntegerField(_("Activity identifier"), db_index=True)
    # FIXME: Availability should be moved to HistoricalActivity
    availability = models.FloatField(_("availability"), blank=True, null=True)
    fk_status = models.ForeignKey("Status", verbose_name=_("Status"), default=1)

    objects = ActivityQuerySet.as_manager()
    negotiation_status_objects = NegotiationStatusManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        '''
        If there's no identifier, set it to a default, and update it to the id
        post save.

        This is pretty much just for import, which keeps trying to get the
        next id and getting it wrong.
        '''
        if self.activity_identifier is None:
            self.activity_identifier = self.ACTIVITY_IDENTIFIER_DEFAULT

        super().save(*args, **kwargs)

        if self.activity_identifier == self.ACTIVITY_IDENTIFIER_DEFAULT:
            kwargs['update_fields'] = ['activity_identifier']
            self.activity_identifier = self.__class__.get_next_activity_identifier()
            # re-save
            super().save(*args, **kwargs)

    @classmethod
    def get_next_activity_identifier(cls):
        queryset = HistoricalActivity.objects#.using('v2')
        queryset = queryset.exclude(activity_identifier=cls.ACTIVITY_IDENTIFIER_DEFAULT)
        queryset = queryset.aggregate(models.Max('activity_identifier'))
        return (queryset['activity_identifier__max'] or 0) + 1

    @classmethod
    def get_latest_activity(cls, activity_identifier):
        return cls.objects.filter(activity_identifier=activity_identifier).order_by('-id').first()

    @classmethod
    def get_latest_active_activity(cls, activity_identifier):
        queryset = cls.objects.public_or_deleted()
        queryset = queryset.filter(activity_identifier=activity_identifier)
        item = queryset.order_by('-id').first()

        return item

    @property
    def operational_stakeholder(self):
        if self.involvements.count() == 0:
            return
            raise ObjectDoesNotExist('No OP for activity %s: %s' % (str(self), str(involvement)))
        else:
            involvement = self.involvements.order_by('-id')[0]
        return involvement.fk_investor

    @property
    def stakeholders(self):
        operational_stakeholder = self.operational_stakeholder
        if operational_stakeholder:
            return [involvement.fk_investor_id
                    for involvement in operational_stakeholder.venture_involvements.all()]
        else:
            return []

    def get_history(self, user=None):
        """
        Returns all deal versions
        """
        queryset = HistoricalActivity.objects.filter(activity_identifier=self.activity_identifier).all()
        if not (user and user.is_authenticated()):
            queryset = queryset.filter(fk_status__in=(HistoricalActivity.STATUS_ACTIVE,
                                                      HistoricalActivity.STATUS_OVERWRITTEN))
        return queryset.order_by('-history_date')

    def get_latest(self, user=None):
        """
        Returns latest historical investor
        """
        queryset = self.get_history(user)
        return queryset.latest()

    def is_editable(self, user=None):
        if self.get_latest(user) != self:
            # Only superuser are allowed to edit old versions
            if user and user.is_superuser:
                return True
            return False
        if user:
            # Status: Pending
            is_editor = user.has_perm('landmatrix.review_activity')
            is_author = self.history_user_id == user.id
            # Only Editors and Administrators are allowed to edit pending deals
            if not is_editor:
                if self.fk_status_id in (self.STATUS_PENDING, self.STATUS_TO_DELETE) \
                        or (self.fk_status_id == self.STATUS_REJECTED and not is_author):
                    return False
        return True

    @property
    def target_country(self):
        country = self.attributes.filter(name='target_country')
        if country.count() > 0:
            country = country.first()
            try:
                return Country.objects.defer('geom').get(id=country.value)
            except Country.DoesNotExist:
                return None
            # Deprecated: Was necessary because of wrong values in the database
            except:
                return None
        else:
            return None

    @property
    def attributes_as_dict(self):
        '''
        Returns all attributes, *grouped* as a nested dict.
        '''
        attrs = defaultdict(dict)
        for attr in self.attributes.select_related('fk_group'):
            attrs[attr.fk_group.name][attr.name] = attr.value

        return attrs

    def get_top_investors(self):
        """
        Get list of highest parent companies (all right-hand side parent companies of the network
        visualisation)
        """
        # Operating company
        queryset = self.involvements.filter(fk_investor__fk_status_id__in=(Investor.STATUS_ACTIVE,
                                                                           Investor.STATUS_OVERWRITTEN))
        operating_companies = [i.fk_investor for i in queryset]
        top_investors = []
        if len(operating_companies) > 0:
            top_investors = operating_companies[0].get_top_investors()
        return top_investors

    def get_parent_companies(self):
        """
        Get list of next parent companies
        """
        # Operating company
        queryset = self.involvements.filter(fk_investor__fk_status_id__in=(Investor.STATUS_ACTIVE,
                                                                           Investor.STATUS_OVERWRITTEN))
        operating_companies = [i.fk_investor for i in queryset]
        parent_companies = []
        if len(operating_companies) > 0:
            parent_companies = [ivi.fk_investor for ivi in operating_companies[0].venture_involvements.filter(
                                    fk_investor__fk_status__in=(InvestorBase.STATUS_ACTIVE,
                                                                InvestorBase.STATUS_OVERWRITTEN),
                                    role=HistoricalInvestorVentureInvolvement.STAKEHOLDER_ROLE)]
        return parent_companies

    def get_investor_countries(self):
        countries = []
        country_ids = set(i.fk_country_id for i in self.get_top_investors())
        for country_id in country_ids:
            try:
                country = Country.objects.defer('geom').select_related('fk_region')
                country = country.get(id=country_id)
                countries.append(country)
            except Country.DoesNotExist:
                pass
        return countries

    def get_deal_size(self):
        # FIXME: This should probably not sort by -date but by -id (latest element instead of newest)
        intended_size = self._get_current("intended_size")
        contract_size = self._get_current("contract_size")
        production_size = self._get_current("production_size")

        negotiation_status = self.get_negotiation_status()
        # 1) IF Negotiation status IS Intended
        if negotiation_status in Activity.NEGOTIATION_STATUSES_INTENDED:
            # USE Intended size OR Contract size OR Production size (in the given order)
            value = intended_size or contract_size or production_size or 0
        # 2) IF Negotiation status IS Concluded
        elif negotiation_status in Activity.NEGOTIATION_STATUSES_CONCLUDED:
            # USE Contract size or Production size (in the given order)
            value = contract_size or production_size or 0
        # 3) IF Negotiation status IS Failed (Negotiations failed)
        elif negotiation_status == Activity.NEGOTIATION_STATUS_NEGOTIATIONS_FAILED:
            # USE Intended size OR Contract size OR Production size (in the given order)
            value = intended_size or contract_size or production_size or 0
        # 4) IF Negotiation status IS Failed (Contract canceled)
        elif negotiation_status == Activity.NEGOTIATION_STATUS_CONTRACT_CANCELLED:
            # USE Contract size OR Production size (in the given order)
            value = contract_size or production_size or 0
        # 5) IF Negotiation status IS Contract expired
        elif negotiation_status == Activity.NEGOTIATION_STATUS_CONTRACT_EXPIRED:
            # USE Contract size OR Production size (in the given order)
            value = contract_size or production_size or 0
        # 6) IF Negotiation status IS Change of ownership
        elif negotiation_status == Activity.NEGOTIATION_STATUS_CHANGE_OF_OWNERSHIP:
            # USE Contract size OR Production size (in the given order)
            value = contract_size or production_size or 0
        else:
            value = 0

        if value:
            # Legacy: There shouldn't be any comma separated values anymore in the database
            if ',' in value:
                return int(value.split(',')[0])
            elif '.' in value:
                return int(value.split('.')[0])
            else:
                return int(value)
        else:
            return 0

    def _get_current(self, attribute):
        """
        Returns the relevant state for the deal.
        Uses
        - Current checkbox, if given
        - Last given entry if it has no year
        - Most recent year/date given
        """
        attributes = self.attributes.filter(name=attribute)
        attributes = attributes.extra(order_by=['-is_current', '-id'])
        if attributes.count() == 0:
            return None
        current = attributes.first()
        if not current.is_current and current.date:
            attributes = attributes.exclude(date__isnull=True).exclude(date='')
            attributes = attributes.extra(order_by=['-is_current', '-date', '-id'])
            current = attributes.first()
        return current.value

    def get_negotiation_status(self):
        return self._get_current('negotiation_status')

    def get_implementation_status(self):
        return self._get_current('implementation_status')

    def get_contract_size(self):
        contract_size = self._get_current('contract_size')
        if contract_size:
            return int(float(contract_size))
        return 0

    def get_production_size(self):
        production_size = self._get_current('production_size')
        if production_size:
            return int(float(production_size))
        return 0

    def get_agricultural_produce(self):
        crop_ids = set(a.value for a in self.attributes.filter(name='crops'))
        crops = Crop.objects.select_related('fk_agricultural_produce').filter(id__in=crop_ids)
        agricultural_produce = set(c.fk_agricultural_produce.name for c in crops if
                                   c.fk_agricultural_produce)
        if len(agricultural_produce) > 1:
            return self.AGRICULTURAL_PRODUCE_MULTI
        else:
            return list(agricultural_produce)


class Activity(ActivityBase):
    """
    Just the most recent approved version of an activity
    (for simple queries in the public interface).

    There should only be one activity per activity_identifier.
    """
    is_public = models.BooleanField(_('Is public'), default=False, db_index=True)
    deal_scope = models.CharField(_('Deal scope'), max_length=16,
                                  choices=ActivityBase.DEAL_SCOPE_CHOICES, blank=True,
                                  null=True, db_index=True)
    negotiation_status = models.CharField(_('Negotiation status'), max_length=64,
        choices=ActivityBase.NEGOTIATION_STATUS_CHOICES, blank=True, null=True, db_index=True)
    implementation_status = models.CharField(
        verbose_name=_('Implementation status'), max_length=64,
        choices=ActivityBase.IMPLEMENTATION_STATUS_CHOICES, blank=True, null=True, db_index=True)
    contract_size = models.IntegerField(verbose_name=_('Current size under contract'),
                                        blank=True, null=True, db_index=True)
    production_size = models.IntegerField(verbose_name=_('Current size in operation (production)'),
                                          blank=True, null=True, db_index=True)
    deal_size = models.IntegerField(verbose_name=_('Deal size'), blank=True, null=True, db_index=True)
    init_date = models.CharField(verbose_name=_('Initiation year or date'), max_length=10,
                                 blank=True, null=True, db_index=True)
    fully_updated_date = models.DateField(_("Fully updated date"), blank=True, null=True)
    top_investors = models.TextField(verbose_name=_("Top parent companies"), blank=True)
    forest_concession = models.BooleanField(_('Forest concession'), default=False)

    def refresh_cached_attributes(self):
        self.implementation_status = self.get_implementation_status()
        self.negotiation_status = self.get_negotiation_status()
        self.contract_size = self.get_contract_size()
        self.production_size = self.get_production_size()
        self.deal_size = self.get_deal_size()
        self.deal_scope = self.get_deal_scope()
        self.init_date = self.get_init_date()
        self.fully_updated_date = self.get_fully_updated_date()
        self.is_public = self.is_public_deal()
        top_investors = self.get_top_investors()
        self.top_investors = self.format_investors(top_investors)
        self.availability = self.get_availability()
        self.forest_concession = self.get_forest_concession()
        self.save()

    def is_public_deal(self):
        # 1. Flag „not public“ set?
        if self.has_flag_not_public():
            return False
        # 2. Minimum information missing?
        if self.missing_information():
            return False
        # 3. Involvements missing?
        involvements = self.involvements.all()
        if involvements.count() == 0:
            return False
        # 4A. Invalid Operating company name?
        # 4B. Invalid Parent companies/investors?
        if self.has_invalid_operating_company(involvements) and self.has_invalid_parents(involvements):
            return False
        # 6. High income country?
        if self.is_high_income_target_country():
            return False
        return True

    def get_not_public_reason(self):
        # Presets:
        # >= 2000
        # Size given and size > 200 ha
        # 5. has subinvestors
        # 6. has valid investor (not unknown)
        # 7. Intention is not Mining
        # 8. Target country is no high income country

        # 1. Flag „not public“ set?
        if self.has_flag_not_public():
            return '1. Flag not public set'
        # 2. Minimum information missing?
        if self.missing_information():
            return '2. Minimum information missing'
        # 3. Involvements missing?
        involvements = self.involvements.all()
        if involvements.count() == 0:
            return '3. involvements missing'
        # 4. Invalid Operating company name?
        if self.has_invalid_operating_company(involvements):
            return ''
        # 4. Invalid Operating company name?
        # 5. Invalid Parent companies/investors?
        if self.has_invalid_operating_company(involvements) and self.has_invalid_parents(involvements):
            return '4. Invalid Operating company name or 5. Invalid Parent companies/investors'
        # 6. High income country
        if self.is_high_income_target_country():
            return '6. High income country'
        return 'Filters passed (public)'

    def is_high_income_target_country(self):
        for tc in self.attributes.filter(name="target_country"):
            country = Country.objects.get(id=tc.value)
            if country.high_income:
                return True
        return False

    #def is_mining_deal(self):
    #    mining = A_Key_Value_Lookup.objects.filter(activity_identifier=activity_identifier, key="intention",
    #                                               value="Mining")
    #    intentions = A_Key_Value_Lookup.objects.filter(activity_identifier=activity_identifier, key="intention")
    #    is_mining_deal = len(mining) > 0 and len(intentions) == 1
    #    return is_mining_deal

    def has_invalid_operating_company(self, involvements):
        for i in involvements:
            if not i.fk_investor:
                continue
            investor_name = i.fk_investor.name
            invalid_name = "^(unknown|unnamed)( \(([, ]*(unnamed investor [0-9]+)*)+\))?$"
            if investor_name and not re.match(invalid_name, investor_name.lower()):
                return False
        return True

    def has_invalid_parents(self, involvements):
        for i in involvements:
            if not i.fk_investor:
                continue
            # Operating company name given?
            # investor_name = i.fk_investor.name
            # invalid_name = "(unknown|unnamed)"
            # if not investor_name:
            #     return True
            # elif not re.search(invalid_name, investor_name.lower()):
            #     return True
            for pi in i.fk_investor.venture_involvements.all():
                # Parent investor/company name given?
                investor_name = pi.fk_investor.name
                invalid_name = "(unknown|unnamed)"
                if investor_name and not re.search(invalid_name, investor_name.lower()):
                    return False
        return True

    def missing_information(self):
        target_country = self.attributes.filter(name="target_country")
        ds_type = self.attributes.filter(name="type")
        return len(target_country) == 0 or len(ds_type) == 0


    #def is_size_invalid(self):
    #    intended_size = latest_attribute_value_for_activity(activity_identifier, "intended_size") or 0
    #    contract_size = latest_attribute_value_for_activity(activity_identifier, "contract_size") or 0
    #    production_size = latest_attribute_value_for_activity(activity_identifier, "production_size") or 0
    #    # Filter B2 (area size >= 200ha AND at least one area size is given)
    #    no_size_set = (not intended_size and not contract_size and not production_size)
    #    size_too_small = int(intended_size) < MIN_DEAL_SIZE and int(contract_size) < MIN_DEAL_SIZE and int(production_size) < MIN_DEAL_SIZE
    #    return no_size_set or size_too_small


    def has_flag_not_public(self):
        # Filter B1 (flag is unreliable not set):
        not_public = self.attributes.filter(name="not_public")
        not_public = len(not_public) > 0 and not_public[0].value or None
        return not_public and not_public in ("True", "on")

    def get_init_date(self):
        init_dates = []
        negotiation_stati = self.attributes.filter(name="negotiation_status", value__in=(
            #NEGOTIATION_STATUS_EXPRESSION_OF_INTEREST, - removed, see #1154
            self.NEGOTIATION_STATUS_UNDER_NEGOTIATION,
            self.NEGOTIATION_STATUS_ORAL_AGREEMENT,
            self.NEGOTIATION_STATUS_CONTRACT_SIGNED,
            self.NEGOTIATION_STATUS_NEGOTIATIONS_FAILED,
            self.NEGOTIATION_STATUS_CONTRACT_CANCELLED
            )).order_by("date")
        implementation_stati = self.attributes.filter(name="implementation_status", value__in=(
            self.IMPLEMENTATION_STATUS_STARTUP_PHASE,
            self.IMPLEMENTATION_STATUS_IN_OPERATION,
            self.IMPLEMENTATION_STATUS_PROJECT_ABANDONED
        )).order_by("date")
        if negotiation_stati.count() > 0:
            if negotiation_stati[0].date:
                init_dates.append(negotiation_stati[0].date)
        if implementation_stati.count() > 0:
            if implementation_stati[0].date:
                init_dates.append(implementation_stati[0].date)
        if init_dates:
            return min(init_dates)
        else:
            return None

    def get_deal_scope(self):
        def get_investor_countries(involvement, investors=None):
            if not investors:
                investors = set()
            countries = set()
            # Check if investor already processed to prevent infinite loops
            if involvement.fk_investor_id in investors:
                return countries
            else:
                investors.add(involvement.fk_investor_id)
            if involvement.fk_investor.fk_status_id in (Investor.STATUS_ACTIVE, Investor.STATUS_OVERWRITTEN):
                if involvement.fk_investor.fk_country_id:
                    countries.add(str(involvement.fk_investor.fk_country_id))
            sinvolvements = involvement.fk_investor.venture_involvements.stakeholders()
            sinvolvements = sinvolvements.filter(fk_investor__fk_status_id__in=(Investor.STATUS_ACTIVE,
                                                                                Investor.STATUS_OVERWRITTEN))
            for sinvolvement in sinvolvements:
                countries.update(get_investor_countries(sinvolvement, investors))
            return countries

        target_countries = {c.value for c in self.attributes.filter(name="target_country")}
        involvements = self.involvements.all()
        investor_countries = set()
        for oc_involvement in involvements:
            investor_countries.update(get_investor_countries(oc_involvement))
        if len(target_countries) > 0 and len(investor_countries) > 0:
            if len(target_countries.symmetric_difference(investor_countries)) == 0:
                return "domestic"
            else:
                return "transnational"
        elif len(target_countries) > 0 and len(investor_countries) == 0:
            # treat deals without investor country as transnational
            return "transnational"
        else:
            return None

    def get_updated_date(self):
        try:
            activity = HistoricalActivity.objects.filter(activity_identifier=self.activity_identifier).latest()
            return activity.history_date
        except:
            return None

    def get_updated_user(self):
        try:
            activity = HistoricalActivity.objects.filter(activity_identifier=self.activity_identifier).latest()
            return activity.history_user.id
        except:
            return None

    def get_fully_updated_date(self):
        try:
            activity = HistoricalActivity.objects.filter(activity_identifier=self.activity_identifier,
                                                         fully_updated=True).latest()
            return activity.history_date
        except:
            return None

    def get_fully_updated_user(self):
        try:
            activity = HistoricalActivity.objects.filter(activity_identifier=self.activity_identifier,
                                                         fully_updated=True).latest()
            return activity.history_user.id
        except:
            return None

    def format_investors(self, investors):
        # First name, then ID to be able to sort by name
        return '|'.join(['#'.join([i.name.replace('#', '').replace("\n", '').strip(),
                                   str(i.investor_identifier),
                                   (i.fk_country and i.fk_country.name or '')])
                         for i in investors])

    def get_availability(self):
        queryset = self.attributes
        queryset = queryset.filter(models.Q(value__isnull=False) | models.Q(value2__isnull=False))
        queryset = set(queryset.values_list('name', flat=True))
        return len(queryset) / self.get_availability_total() * 100

    def get_availability_total(self):
        from django.apps import apps
        return len(apps.get_app_config('grid').VARIABLES.keys())

    def get_forest_concession(self):
        nature_concession = self.attributes.filter(name='nature', value=NATURE_CONCESSION)
        intention_logging = self.attributes.filter(name='intention', value=INTENTION_FOREST_LOGGING)
        return nature_concession.count() > 0 and intention_logging.count() > 0

    class Meta:
        verbose_name = _('Activity')
        verbose_name_plural = _('Activities')
        index_together = [
            ['is_public', 'deal_scope'],
            ['is_public', 'deal_scope', 'negotiation_status'],
            ['is_public', 'deal_scope', 'implementation_status'],
            ['is_public', 'deal_scope', 'negotiation_status', 'implementation_status'],
        ]
        permissions = (
            ("review_activity", "Can review activity changes"),
        )


class HistoricalActivityQuerySet(ActivityQuerySet):

    def get_for_user(self, user):
        qs = self.filter(history_user=user).values_list('activity_identifier', flat=True)
        return self.filter(activity_identifier__in=qs).filter(id__in=self.latest_ids())

    def _single_revision_identifiers(self):
        '''
        Get all activity identifiers (as values) that only have a single
        revision.

        This query looks a bit strange, but the order of operations is required
        in order to construct the group by correctly.
        '''
        queryset = HistoricalActivity.objects.values('activity_identifier') # don't use 'self' here
        queryset = queryset.annotate(
            revisions_count=models.Count('activity_identifier'),
        )
        queryset = queryset.order_by('activity_identifier')
        queryset = queryset.exclude(revisions_count__gt=1)
        queryset = queryset.values_list('activity_identifier', flat=True)

        return queryset

    def with_multiple_revisions(self):
        '''
        Get only new activities (without any other historical instances).
        '''
        subquery = self._single_revision_identifiers()
        queryset = self.exclude(activity_identifier__in=subquery)
        return queryset.filter(id__in=self.latest_ids())

    def without_multiple_revisions(self):
        '''
        Get only new activities (without any other historical instances).
        '''
        subquery = self._single_revision_identifiers()
        queryset = self.filter(activity_identifier__in=subquery)
        return queryset.filter(id__in=self.latest_ids())

    def latest_ids(self):
        queryset = HistoricalActivity.objects.values('activity_identifier').annotate(
            max_id=models.Max('id'),
        ).order_by().values_list('max_id', flat=True)
        return queryset

    def latest_only(self):
        return self.filter(id__in=self.latest_ids())


class HistoricalActivity(ActivityBase):
    """
    All versions (including the current) of activities
    
    Only the current historical activity should have a public version set.
    """
    public_version = models.OneToOneField(
        Activity, blank=True, null=True, related_name='historical_version', on_delete=models.SET_NULL)
    history_date = models.DateTimeField(default=timezone.now)
    history_user = models.ForeignKey('auth.User', blank=True, null=True)
    comment = models.TextField(_('Comment'), blank=True, null=True)
    fully_updated = models.BooleanField(_("Fully updated"), default=False)

    objects = HistoricalActivityQuerySet.as_manager()

    def approve_change(self, user=None, comment=None):
        assert self.fk_status_id == HistoricalActivity.STATUS_PENDING

        # Only approvals of administrators should go public
        if user.has_perm('landmatrix.change_activity'):
            # TODO: this logic is taken from changeset protocol
            # but it won't really work properly. We need to determine behaviour
            # when updates happen out of order. There can easily be many edits,
            # and not the latest one is approved.
            latest_public_version = self.__class__.get_latest_active_activity(
                self.activity_identifier)
            if latest_public_version:
                self.fk_status_id = HistoricalActivity.STATUS_OVERWRITTEN
            else:
                self.fk_status_id = HistoricalActivity.STATUS_ACTIVE
            self.save(update_fields=['fk_status'])

            try:
                investor = self.involvements.all()[0].fk_investor
            except IndexError:
                pass
            else:
                investor.approve()

            self.update_public_activity()

        self.changesets.create(fk_user=user, comment=comment)

    def reject_change(self, user=None, comment=None):
        assert self.fk_status_id == HistoricalActivity.STATUS_PENDING
        self.fk_status_id = HistoricalActivity.STATUS_REJECTED
        self.save(update_fields=['fk_status'])
        #self.update_public_activity() - don't update public activity

        try:
            investor = self.involvements.all()[0].fk_investor
        except IndexError:
            pass
        else:
            investor.reject()

        self.changesets.create(fk_user=user, comment=comment)

    def approve_delete(self, user=None, comment=None):
        assert self.fk_status_id == HistoricalActivity.STATUS_TO_DELETE

        # Only approvals of administrators should be deleted
        if user.has_perm('landmatrix.delete_activity'):
            self.fk_status_id = HistoricalActivity.STATUS_DELETED
            self.save(update_fields=['fk_status'])
            self.update_public_activity()

        self.changesets.create(fk_user=user, comment=comment)

    def reject_delete(self, user=None, comment=None):
        assert self.fk_status_id == HistoricalActivity.STATUS_TO_DELETE
        self.fk_status_id = HistoricalActivity.STATUS_REJECTED
        self.save(update_fields=['fk_status'])

        try:
            investor = self.involvements.all()[0].fk_investor
        except IndexError:
            pass
        else:
            investor.reject()

        self.changesets.create(fk_user=user, comment=comment)

    def compare_attributes_to(self, version):
        changed_attrs = []  # (group_id, key, current_val, other_val)

        def get_lookup(attr):
            return (attr.fk_group_id, attr.name)

        current_attrs = list(self.attributes.all())
        current_lookups = {
            get_lookup(attr) for attr in current_attrs
        }
        # Build a dict of attrs for quick lookup with one query
        other_attrs = {}
        if version:
            for attr in version.attributes.all():
                other_attrs[get_lookup(attr)] = attr.value

        for attr in current_attrs:
            lookup = get_lookup(attr)
            if lookup not in other_attrs:
                changes = (attr.fk_group_id, attr.name, attr.value, None)
                changed_attrs.append(changes)
            elif lookup in other_attrs and attr.value != other_attrs[lookup]:
                other_val = other_attrs[lookup]
                changes = (attr.fk_group_id, attr.name, attr.value, other_val)
                changed_attrs.append(changes)

        # Check attributes that are not in this version
        for lookup in set(other_attrs.keys()) - current_lookups:
            group_id, key = lookup
            changes = (group_id, key, None, other_attrs[lookup])
            changed_attrs.append(changes)

        return changed_attrs

    def update_public_activity(self):
        """Update public activity based upon newest confirmed historical activity"""
        #user = user or self.history_user
        # Update status of historical activity
        if self.fk_status_id == self.STATUS_PENDING:
            self.fk_status_id = self.STATUS_OVERWRITTEN
        elif self.fk_status_id == self.STATUS_TO_DELETE:
            self.fk_status_id = self.STATUS_DELETED
        self.save(update_elasticsearch=False)

        # Historical activity already is the newest version of activity?
        #if self.public_version:
        #    return False

        activity = Activity.objects.filter(activity_identifier=self.activity_identifier).order_by('-id').first()

        # Activity has been deleted?
        if self.fk_status_id == self.STATUS_DELETED:
            if activity:
                activity.delete()
            return True
        elif self.fk_status_id == self.STATUS_REJECTED:
            # Activity add has been rejected?
            activities = HistoricalActivity.objects.filter(activity_identifier=self.activity_identifier)
            if len(activities) == 1:
                activity.delete()
                return True

        if not activity:
            activity = Activity.objects.create(
                activity_identifier=self.activity_identifier)

        activity.fully_updated = self.fully_updated
        activity.fk_status_id = self.fk_status_id
        activity.save()

        # Delete old and create new activity attributes
        activity.attributes.all().delete()

        for hattribute in self.attributes.all():
            ActivityAttribute.objects.create(
                fk_activity_id=activity.id,
                fk_group_id=hattribute.fk_group_id,
                fk_language_id=hattribute.fk_language_id,
                name=hattribute.name,
                value=hattribute.value,
                value2=hattribute.value2,
                date=hattribute.date,
                is_current=hattribute.is_current,
                polygon=hattribute.polygon)

        # Confirm pending investors and involvement
        hinvolvement = self.involvements.all()
        if hinvolvement.count() > 0:
            # Confirm involvement
            hinvolvement = hinvolvement[0]
            hinvolvement.fk_status_id = hinvolvement.STATUS_OVERWRITTEN
            hinvolvement.save()

            # Confirm pending investors
            hinvestor = hinvolvement.fk_investor
            investor = hinvestor.update_public_investor()

            # Update public involvement
            InvestorActivityInvolvement.objects.filter(
                fk_activity__activity_identifier=self.activity_identifier
            ).delete()
            InvestorActivityInvolvement.objects.create(
                fk_activity=activity,
                fk_investor=investor,
                fk_status_id=InvestorActivityInvolvement.STATUS_OVERWRITTEN
            )
        activity.refresh_cached_attributes()

        # Keep public version relation up to date
        HistoricalActivity.objects.filter(public_version=activity).update(public_version=None)
        self.public_version = activity
        self.save(update_fields=['public_version'], update_elasticsearch=True)

        return activity

    @property
    def changeset_comment(self):
        '''
        Previously in changeset protocol there was some voodoo around getting
        a changeset with the same datetime as history_date. That doesn't work,
        because history_date is set when the activity is revised, and the
        changeset is timestamped when it is reviewed.

        So, just grab the most recent one.
        '''

        changeset = self.changesets.first()
        comment = changeset.comment if changeset else ''

        return comment

    def save(self, *args, **kwargs):
        update_elasticsearch = kwargs.pop('update_elasticsearch', True)
        super().save(*args, **kwargs)
        if update_elasticsearch and not settings.CONVERT_DB:
            from ..tasks import index_activity, delete_activity
            if self.fk_status_id == self.STATUS_DELETED:
                transaction.on_commit(lambda: delete_activity.delay(self.activity_identifier))
            else:
                transaction.on_commit(lambda: index_activity.delay(self.activity_identifier))

    class Meta:
        verbose_name = _('Historical activity')
        verbose_name_plural = _('Historical activities')
        get_latest_by = 'history_date'
        ordering = ('-history_date',)
        get_latest_by = 'id'
