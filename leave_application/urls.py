from django.conf.urls import url, include
from leave_application.views import LeaveView, ApplyLeave, GetApplications, ProcessRequest, GetLeaves, generate_pdf
from django.contrib.auth.decorators import login_required

urlpatterns = [
    url(r'^$', login_required(LeaveView.as_view()), name='apply_for_leave'),
    url(r'^apply', login_required(ApplyLeave.as_view()), name='application_form'),
    # url(r'^getapplications', login_required(GetApplications.as_view()), name='get_applications'),
    url(r'^get-leaves/', login_required(GetLeaves.as_view()), name='get_leaves'),
    url(r'^process-request/(?P<id>[0-9]+)/', login_required(ProcessRequest.as_view()), name='process_request'),
    url(r'^getpdf/', generate_pdf, name='get_application_pdf'),
]
