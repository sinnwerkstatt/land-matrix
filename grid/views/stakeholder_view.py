from collections import OrderedDict
import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.views.generic.edit import CreateView, UpdateView
from django.http import Http404, HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse_lazy
from django.utils.timezone import utc

from grid.forms.investor_formset import InvestorForm
from grid.forms.parent_stakeholder_formset import (
    ParentStakeholderFormSet, ParentInvestorFormSet,
)
from landmatrix.models.investor import Investor, InvestorVentureInvolvement


class StakeholderFormsMixin:
    '''
    Handle the shared form behaviour for create and update.
    '''

    def get_formset_kwargs(self):
        kwargs = {}
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })

        return kwargs

    def get_stakeholders_formset(self):
        kwargs = self.get_formset_kwargs()
        kwargs['prefix'] = 'parent-stakeholder-form'

        if self.object:
            queryset = self.object.venture_involvements.all()
            queryset = queryset.active().stakeholders()
        else:
            queryset = InvestorVentureInvolvement.objects.none()
        kwargs['queryset'] = queryset

        formset = ParentStakeholderFormSet(**kwargs)

        return formset

    def get_investors_formset(self):
        kwargs = self.get_formset_kwargs()
        kwargs['prefix'] = 'parent-investor-form'

        if self.object:
            queryset = self.object.venture_involvements.all()
            queryset = queryset.active().investors()
        else:
            queryset = InvestorVentureInvolvement.objects.none()
        kwargs['queryset'] = queryset

        formset = ParentInvestorFormSet(**kwargs)

        return formset

    def get_investor_history(self):
        def _investor_history(investor):
            date_and_investor = []
            history_items = investor.history.all().order_by('history_date')
            for investor in list(history_items):
                date_and_investor.append(
                    (investor.history_date.timestamp(), investor))

            return sorted(date_and_investor, key=lambda entry: entry[0])

        try:
            history = _investor_history(self.object)
            history = OrderedDict(
                reversed(sorted(history, key=lambda item: item[0])))
        except AttributeError:
            history = None

        return history

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if 'form' not in context:
            context['form'] = self.get_form(form_class=self.get_form_class())

        if 'parent_stakeholders' not in context:
            context['parent_stakeholders'] = self.get_stakeholders_formset()

        if 'parent_investors' not in context:
            context['parent_investors'] = self.get_investors_formset()

        if 'history' not in context:
            context['history'] = self.get_investor_history()

        return context

    def form_invalid(self, investor_form, stakeholders_formset,
                     investors_formset):
        context = self.get_context_data(
            form=investor_form, parent_stakeholders=stakeholders_formset,
            parent_investors=investors_formset)

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        '''
        Override standard post behaviour to check all three forms.
        '''
        self.object = self.get_object()

        investor_form = self.get_form()
        stakeholders_formset = self.get_stakeholders_formset()
        investors_formset = self.get_investors_formset()
        forms_valid = [
            form.is_valid() for form in
            (investor_form, stakeholders_formset, investors_formset)
        ]
        if all(forms_valid):
            response = self.form_valid(investor_form, stakeholders_formset,
                                       investors_formset)
        else:
            response = self.form_invalid(investor_form, stakeholders_formset,
                                         investors_formset)

        return response


class ChangeStakeholderView(StakeholderFormsMixin, UpdateView):
    template_name = 'stakeholder.html'
    pk_url_kwarg = 'investor_id'
    context_object_name = 'investor'
    model = Investor
    form_class = InvestorForm

    def get_object(self, queryset=None):
        '''
        Handle retrieval of old versions via id_timestamp url key.
        TODO: test this works.
        '''
        pk = self.kwargs.get(self.pk_url_kwarg)

        if pk and '_' in pk:
            investor_id, timestamp = pk.split('_')
            investor_date = datetime.datetime.utcfromtimestamp(
                float(timestamp), tzinfo=utc)

            if queryset is None:
                queryset = self.get_queryset()

            try:
                investor = queryset.get(pk=investor_id)
                old_versions = investor.history.filter(
                    history_date__lte=investor_date)
                obj = old_versions.get()
            except queryset.model.DoesNotExist:
                raise Http404(_("No matching stakeholder found."))
        elif pk:
            obj = super().get_object(queryset=queryset)

        return obj

    def form_valid(self, investor_form, stakeholders_formset,
                   investors_formset):
        self.object = investor_form.save()
        stakeholders_formset.save(self.object)
        investors_formset.save(self.object)
        context = self.get_context_data(
            form=investor_form, parent_stakeholders=stakeholders_formset,
            parent_investors=investors_formset)

        return self.render_to_response(context)


class AddStakeholderView(StakeholderFormsMixin, CreateView):
    model = Investor
    form_class = InvestorForm
    template_name = 'stakeholder.html'
    context_object_name = 'investor'

    def get_success_url(self):
        return reverse_lazy('stakeholder_form',
                            kwargs={'investor_id': self.object.pk})

    def get_object(self, queryset=None):
        return None

    def form_valid(self, investor_form, stakeholders_formset,
                   investors_formset):
        self.object = investor_form.save()
        stakeholders_formset.save(self.object)
        investors_formset.save(self.object)

        return HttpResponseRedirect(self.get_success_url())


# TODO: remove in future. These methods are imported and used elsewhere
# currently however.

def investor_from_id(investor_id):
    try:
        if '_' in investor_id:
            return _investor_from_id_and_timestamp(investor_id)
        else:
            return Investor.objects.get(pk=investor_id)
    except ObjectDoesNotExist:
        return None


def _investor_from_id_and_timestamp(id_and_timestamp):
    from datetime import datetime
    from dateutil.tz import tzlocal
    if '_' in id_and_timestamp:
        investor_id, timestamp = id_and_timestamp.split('_')

        investor = Investor.objects.get(pk=investor_id)

        old_version = investor.history.filter(
            history_date__lte=datetime.fromtimestamp(float(timestamp), tz=tzlocal())
        ).last()
        if old_version is None:
            raise ObjectDoesNotExist('Investor %s as of timestamp %s' % (investor_id, timestamp))

        return old_version

    raise RuntimeError('should contain _ separating investor id and timestamp: ' + id_and_timestamp)
