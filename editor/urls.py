from django.conf.urls import url

from editor.views import *


urlpatterns = [
    url(r'^$', DashboardView.as_view(), name='editor'),
    url(r'^manage/feedback/', ManageFeedbackView.as_view(), name='manage_feedback'),
    url(r'^manage/my/', ManageForUserView.as_view(), name='manage_for_user'),
    url(r'^manage/pending_deletes/', ManageDeletesView.as_view(), name='manage_pending_deletes'),
    url(r'^manage/pending_adds/', ManageAddsView.as_view(), name='manage_pending_adds'),
    url(r'^manage/pending_updates/', ManageUpdatesView.as_view(), name='manage_pending_updates'),
    url(r'^manage/rejected/', ManageRejectedView.as_view(), name='manage_rejected'),

    url(r'^manage/deal/approve_change/(?P<id>[0-9]+)/', ApproveActivityChangeView.as_view(),
        name='manage_approve_change_deal'),
    url(r'^manage/deal/reject_change/(?P<id>[0-9]+)/', RejectActivityChangeView.as_view(),
        name='manage_reject_change_deal'),
    url(r'^manage/deal/approve_delete/(?P<id>[0-9]+)/', ApproveActivityDeleteView.as_view(),
        name='manage_approve_delete_deal'),
    url(r'^manage/deal/reject_delete/(?P<id>[0-9]+)/', RejectActivityDeleteView.as_view(),
        name='manage_reject_delete_deal'),

    url(r'^manage/investor/approve_change/(?P<id>[0-9]+)/', ApproveInvestorChangeView.as_view(),
        name='manage_approve_change_investor'),
    url(r'^manage/investor/reject_change/(?P<id>[0-9]+)/', RejectInvestorChangeView.as_view(),
        name='manage_reject_change_investor'),
    url(r'^manage/investor/approve_delete/(?P<id>[0-9]+)/', ApproveInvestorDeleteView.as_view(),
        name='manage_approve_delete_investor'),
    url(r'^manage/investor/reject_delete/(?P<id>[0-9]+)/', RejectInvestorDeleteView.as_view(),
        name='manage_reject_delete_investor'),

    url(r'^manage/$', ManageRootView.as_view(), name='manage'),
    url(r'^log/latest_added/', LogAddedView.as_view(), name='log_added'),
    url(r'^log/latest_modified/', LogModifiedView.as_view(), name='log_modified'),
    url(r'^log/latest_deleted/', LogDeletedView.as_view(), name='log_deleted'),
    url(r'^log/$', login_required(RedirectView.as_view(pattern_name='log_added', permanent=False)), name='log'),
]