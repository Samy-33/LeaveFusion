from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import HttpResponse, Http404, JsonResponse
from leave_application.forms import (FacultyLeaveForm,
                                     StaffLeaveForm,
                                     StudentLeaveForm,)

from user_app.models import Administration, Replacement, ExtraInfo
from leave_application.models import (Leave, CurrentLeaveRequest,
                                      LeaveRequest, LeavesCount,
                                      LeaveMigration,)
from django.contrib.auth.models import User
from leave_application.helpers import FormData, get_object_or_none
from django.db.models import Q
from django.db import transaction

class LeaveView(View):

    def get(self, request):
        cake = request.GET.get('cake')

        if not cake:
            leaves_count = LeavesCount.objects.get(user=request.user)
            applications = GetApplications.get_reps(request)
            message = request.GET.get('message', None)
            form = ApplyLeave.get_form(request) if not message else None
            context = {
                'form': form,
                'leaves_count': leaves_count,
                'message': message,
            }
            context.update(applications)
            return render(request, 'fusion/leaveModule0/leave.html', context)

        elif cake == 'form':
            form = ApplyLeave.get_form(request)
            leaves_count = LeavesCount.objects.get(user=request.user)
            context = {
                'form': form,
                'leaves_count': leaves_count,
            }
            return render(request, 'fusion/leaveModule0/leaveapplicationform.html', context)

        elif cake == 'status':
            user_leaves = Leave.objects.filter(applicant=request.user)
            # print(user_leaves)
            context = {
                'user_leaves': user_leaves
            }

            return render(request, 'fusion/leaveModule0/leavestatus.html', context)

        elif cake == 'approve':
            context = GetApplications.get_to_approve(request)
            return render(request, 'fusion/leaveModule0/leaveapprove.html', context)

        else:
            return HttpResponse('Are you a dick?')

class ApplyLeave(View):
    """
        A Class Based View which handles user applying for leave
    """
    def get(self, request):
        """
            view to handle get request to /leave/apply
        """
        # TODO: Check if leave not rejected or accepted and leave instance belongs to user
        # TODO: Take another value as action so that action can specify edit or delete with same constraint

        # id = request.GET.get('id')
        # if id:
        #     leave = get_object_or_404(Leave, id=id)
        #     user_type = self.get_user_type(request)
        #     if user_type == 'faculty':
        #         form = FacultyLeaveForm(leave, user=request.user)
        #     elif user_type == 'staff':
        #         form = StaffLeaveForm(leave, user=request.user)
        #     else:
        #         form = StudentLeaveForm(leave)
        #     return render(request, 'leave_application/apply_for_leave.html', {'form': form, 'title': 'Leave', 'action':'Edit'})
        # form = ApplyLeave.get_form(request)
        # # user_leaves = Leave.objects.filter(applicant=request.user)
        # leaves_count = LeavesCount.objects.get(user=request.user)
        # context ={
        #     'form': form,
        #     # 'user_leaves': user_leaves,
        #     'leaves_count': leaves_count,
        # }
        #
        # # applications = GetApplications.get(request)
        # # context.update(applications)
        # # return render(request, 'leave_application/apply_for_leave.html', {'form': form, 'title': 'Leave', 'action':'Apply'})
        # return render(request, 'fusion/leaveModule0/leaveapplicationform.html', context)
        return redirect('/leave/')

    def post(self, request):
        """
            view to handle post request to /leave/apply
        """
        form = ApplyLeave.get_form(request)
        if form.is_valid():
            type_of_leave = form.cleaned_data.get('type_of_leave', 'casual')
            acad_done = False if form.cleaned_data.get('acad_rep', False) else True
            admin_done = False if form.cleaned_data.get('admin_rep', False) else True
            academic_replacement = get_object_or_none(User, username=form.cleaned_data.get('acad_rep'))
            administrative_replacement = get_object_or_none(User,
                                                            username=form.cleaned_data.get('admin_rep'))
            try:
                leave_obj = Leave.objects.create(
                    applicant = request.user,
                    type_of_leave = type_of_leave,
                    academic_replacement = academic_replacement,
                    administrative_replacement = administrative_replacement,
                    purpose = form.cleaned_data['purpose'],
                    acad_done = acad_done,
                    admin_done = admin_done,
                    leave_address = form.cleaned_data.get('leave_address', ''),
                    start_date = form.cleaned_data['start_date'],
                    end_date = form.cleaned_data['end_date'],
                    station = form.cleaned_data.get('station_leave'),
                )

            except Exception as e:
                return render(request,
                              'leave_application/apply_for_leave.html',
                              {'form': form, 'message': 'Failed'})
            # return render(request, 'leave_application/apply_for_leave.html', {'message': 'success', 'title': 'Leave', 'action':'Apply'})
            return redirect('/leave/?message=success')
            # return render(request, 'fusion/leaveModule0/leave.html', {'message': 'success', 'title': 'Leave', 'action':'Apply'})
        else:
            context = {'form': form, 'title': 'Leave', 'action':'Apply'}
            leaves_count = LeavesCount.objects.get(user=request.user)
            context['leaves_count'] = leaves_count
            context.update(GetApplications.get_reps(request))
            leaves_count = LeavesCount.objects.get(user=request.user)
            return render(request, 'fusion/leaveModule0/leave.html', context)

    @classmethod
    def get_user_type(cls, request):
        return request.user.extrainfo.user_type

    @classmethod
    def get_form(cls, request):

        user_type = cls.get_user_type(request)

        if user_type == 'faculty':
            form = cls.get_form_object(FacultyLeaveForm, request)
        elif user_type == 'staff':
            form = cls.get_form_object(StaffLeaveForm, request)
        else:
            form = cls.get_form_object(StudentLeaveForm, request)

        return form

    @classmethod
    def get_form_object(ccls, cls, request):

        if request.method == 'GET':
            return cls(initial={}, user=request.user)
        else:
            return cls(request.POST, user=request.user)


class ProcessRequest(View):

    # def post(self, request, id):
    #     print(request.POST)
    #     return JsonResponse({'response': 'ok'}, status=200)

    def post(self, request, id):
        leave_request = get_object_or_404(CurrentLeaveRequest, id=id)
        #print(request.POST)
        do = request.POST.get('do')

        response = JsonResponse({'response': 'Failed'}, status=400)

        rep_user = get_object_or_none(Replacement, replacee=leave_request.requested_from,
                                                   replacement_type='administrative')
        if rep_user:
            rep_user = rep_user.replacer

        if request.user in [leave_request.requested_from, rep_user] \
           and do in ['accept', 'reject', 'forward']:

            response = getattr(self, do)(request, leave_request) or response

        return response


    def accept(self, request, leave_request):
        type_of_leave = leave_request.leave.type_of_leave
        sanc_auth = leave_request.applicant.extrainfo.sanctioning_authority
        sanc_officer = leave_request.applicant.extrainfo.sanctioning_officer
        remark = request.GET.get('remark', '')
        response = JsonResponse({'response': 'ok'}, status=200)

        if leave_request.permission in ['academic', 'admin']:

            if leave_request.permission == 'academic':
                leave_request.leave.acad_done = True
            else:
                leave_request.leave.admin_done = True

            leave_request.leave.save()
            leave_request = self.create_leave_request(leave_request, False, accept=True, remark=remark)

            if leave_request.leave.replacement_confirm and leave_request.leave.status == 'processing':
                position = leave_request.applicant.extrainfo.sanctioning_authority
                next_user = ExtraInfo.objects.filter(designation=position).first().user
                CurrentLeaveRequest.objects.create(
                    applicant = leave_request.applicant,
                    requested_from = next_user,
                    permission = 'sanc_auth',
                    position = position,
                    leave = leave_request.leave,
                    station = leave_request.station,
                )

        elif sanc_auth == sanc_officer or leave_request.permission == 'sanc_officer':
            leave_request = self.create_leave_request(leave_request, True, accept=True, remark=remark)
            leave_request.leave.status = 'accepted'
            leave_request.leave.save()

        elif leave_request.permission == 'sanc_auth':
            if type_of_leave in ['casual', 'restricted']:
                leave_request = self.create_leave_request(leave_request, True, accept=True, remark=remark)
            else:
                response = None

        return response

    def reject(self, request, leave_request):
        remark = request.GET.get('remark', '')

        type_of_leave = leave_request.leave.type_of_leave
        response = JsonResponse({'response': 'ok',}, status=200)
        sanc_auth = leave_request.applicant.extrainfo.sanctioning_authority
        sanc_officer = leave_request.applicant.extrainfo.sanctioning_officer

        condition = sanc_officer == sanc_auth

        if not leave_request.leave.replacement_confirm or leave_request.permission == 'sanc_officer' \
            or condition:
            leave_request = self.create_leave_request(leave_request, True, accept=False, remark=remark)
            list(map(lambda x: x.delete(), leave_request.leave.cur_requests.all()))

        elif leave_request.permission == 'sanc_auth':
            if type_of_leave in ['casual', 'restricted']:
                leave_request = self.create_leave_request(leave_request, True, accept=False, remark=remark)
            else:
                response = None
        else:
            response = None
        return response

    def forward(self, request, leave_request):

        remark = request.GET.get('remark', '')
        type_of_leave = leave_request.leave.type_of_leave

        response = JsonResponse({'response': 'ok',}, status=200)

        if leave_request.permission == 'sanc_auth' and \
            type_of_leave not in ['casual', 'restricted']:

            leave_request = self.create_leave_request(leave_request, False, accept=False, remark=remark)

            if leave_request.leave.status == 'processing':
                position = leave_request.applicant.extrainfo.sanctioning_officer

                next_user = ExtraInfo.objects.filter(designation=position).first().user

                CurrentLeaveRequest.objects.create(
                    applicant = leave_request.applicant,
                    requested_from = next_user,
                    position = position,
                    station = leave_request.station,
                    leave = leave_request.leave,
                    permission = 'sanc_officer',
                )
        else:
            response = None

        return response

    @transaction.atomic
    def create_leave_request(self, cur_leave_request, final, accept=False, remark=''):
        leave_request = LeaveRequest.objects.create(
            leave = cur_leave_request.leave,
            applicant = cur_leave_request.applicant,
            requested_from = cur_leave_request.requested_from,
            remark = remark,
            position = cur_leave_request.position,
            status = accept,
        )

        if not accept and final:
            cur_leave_request.leave.status = 'rejected'
        elif final:

            count = LeavesCount.objects.get(user=cur_leave_request.applicant)

            remain = getattr(count, cur_leave_request.leave.type_of_leave)
            required_leaves = cur_leave_request.leave.count_work_days
            # print(required_leaves, remain)
            # return True
            if remain < required_leaves:
                cur_leave_request.leave.status = 'rejected'
            else:
                setattr(count, cur_leave_request.leave.type_of_leave,
                               remain - required_leaves)
                count.save()
                self.create_migration(cur_leave_request.leave)
                cur_leave_request.leave.status = 'accepted'
        cur_leave_request.leave.save()
        cur_leave_request.delete()
        return leave_request

    def process_student_request(self, sanc_auth, leave_request, remark, process):

        outcome = 'accepted' if process else 'rejected'
        new_leave_request = LeaveRequest.objects.create(
            applicant = leave_request.applicant,
            requested_from = leave_request.requested_from,
            position = leave_request.position,
            leave = leave_request.leave,
            status = process,
            remark = remark,
        )
        new_leave_request.leave.status = outcome
        new_leave_request.leave.save()
        leave_request.delete()
        return JsonResponse({'response': 'ok'}, status=200)

    @transaction.atomic
    def create_migration(self, leave):
        import datetime

        if leave.start_date <= datetime.date.today():
            # Replacement.objects.create(
            #     replacee = leave.applicant,
            #     replacer = leave.academic_replacement,
            #     replacement_type = 'academic',
            # )
            # Replacement.objects.create(
            #     replacee = leave.applicant,
            #     replacer = leave.administrative_replacement,
            #     replacement_type = 'administrative',
            # )
            if leave.applicant.extrainfo.user_type == 'faculty':
                r1 = Replacement.objects.create(
                    replacee = leave.applicant,
                    replacer = leave.academic_replacement,
                    replacement_type = 'academic',
                )
                LeaveMigration.objects.create(
                    replacee = leave.applicant,
                    replacer = leave.academic_replacement,
                    rep = r1,
                    start_date = leave.end_date + datetime.timedelta(days=1),
                    type = 'del',
                )

            r2 = Replacement.objects.create(
                replacee = leave.applicant,
                replacer = leave.administrative_replacement,
                replacement_type = 'administrative',
            )
            LeaveMigration.objects.create(
                replacee = leave.applicant,
                replacer = leave.administrative_replacement,
                rep = r2,
                start_date = leave.end_date + datetime.timedelta(days=1),
                type = 'del',
            )

        else:
            # if leave.start_date not in to_be.migrations.keys():
                # to_be.migrations[leave.start_date] = []
            if leave.applicant.extrainfo.user_type == 'faculty':
                LeaveMigration.objects.create(
                    type = 'add',
                    replacee = leave.applicant,
                    replacer = leave.academic_replacement,
                    start_date = leave.start_date,
                    end_date = leave.end_date,
                    replacement_type = 'academic',
                )

            LeaveMigration.objects.create(
                type = 'add',
                replacee = leave.applicant,
                replacer = leave.administrative_replacement,
                start_date = leave.start_date,
                end_date = leave.end_date,
                replacement_type = 'administrative',
            )

    def is_problematic(self, leave):
        #TODO: Add automatic hadling of outdated or problematic leave requests
        pass

class GetApplications():

    @classmethod
    def get_to_approve(cls, request):
        processed_request_list = LeaveRequest.objects.filter(requested_from=request.user).order_by('-id')

        replacement = Replacement.objects.filter(Q(replacer=request.user)
                                                 & Q(replacement_type='administrative'))
        replacee = replacement.first().replacee if replacement else None
        request_list = CurrentLeaveRequest.objects.filter((Q(requested_from=request.user)
                                                          | Q(requested_from=replacee))
                                                          & ~(Q(permission='academic')
                                                          | Q(permission='admin')))
        request_list = [cls.should_forward(request, q_obj) for q_obj in request_list]

        # print(rep_requests)
        context = {
            'processed_request_list': processed_request_list,
            'request_list': request_list,
        }
        return context

        #count = len(request_list)
        # return render(request, 'leave_application/get_requests.html', {'requests': request_list,
        #                                                               'title':'Leave',
        #                                                               'action':'ViewRequests',
        #                                                               'count':count,
        #                                                               'prequests':prequest_list})

    @classmethod
    def get_reps(cls, request):
        rep_requests = CurrentLeaveRequest.objects.filter(Q(requested_from=request.user) &
                                                          (Q(permission='academic') | Q(permission='admin')))
        return {'rep_requests': rep_requests}

    @classmethod
    def should_forward(cls, request, query_obj):

        obj = FormData(request, query_obj)
        sanc_auth = query_obj.applicant.extrainfo.sanctioning_authority
        sanc_officer = query_obj.applicant.extrainfo.sanctioning_officer
        type_of_leave = query_obj.leave.type_of_leave

        designation = query_obj.requested_from.extrainfo.designation
        if sanc_auth == sanc_officer:
            obj.forward = False
        elif (sanc_auth == designation and type_of_leave not in ['casual', 'restricted']) \
             and query_obj.permission not in ['academic', 'admin']:

             obj.forward = True

        else:
            obj.forward = False
        return obj

class GetLeaves(View):

    def get(self, request):

        leave_list = Leave.objects.filter(applicant=request.user).order_by('-id')
        count = len(list(leave_list))
        return render(request, 'leave_application/get_leaves.html', {'leaves':leave_list,
                                                                     'count':count,
                                                                     'title':'Leave',
                                                                     'action':'ViewLeaves'})



"""

$.ajax({
    type: 'delete',
    url: '/leave/apply',
    data: {'id': 17},
    success: function(data){
        alert(data.message);
    },
    error: function(err){
        alert('error');
    }
});

"""
