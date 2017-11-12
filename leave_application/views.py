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
from leave_application.helpers import FormData, get_object_or_none, count_work_days
from django.db.models import Q
from django.db import transaction
import datetime
import json

class LeaveView(View):

    def get(self, request):
        cake = request.GET.get('cake')
        curr_year = datetime.date.today().year
        if not cake:
            leaves_count = LeavesCount.objects.get(user=request.user, year=curr_year)
            applications = GetApplications.get_reps(request)
            message = request.GET.get('message', None)
            form = ApplyLeave.get_form(request) if not message else None
            received_requests = GetApplications.get_count(request)
            context = {
                'form': form,
                'leaves_count': leaves_count,
                'message': message,
                'show_approve': received_requests
            }
            context.update(applications)
            return render(request, 'fusion/leaveModule0/leave.html', context)

        elif cake == 'form':
            form = ApplyLeave.get_form(request)
            leaves_count = LeavesCount.objects.get(user=request.user, year=curr_year)
            context = {
                'form': form,
                'leaves_count': leaves_count,
            }
            return render(request, 'fusion/leaveModule0/leaveapplicationform.html', context)

        elif cake == 'status':
            user_leaves = Leave.objects.filter(applicant=request.user)

            context = {
                'user_leaves': user_leaves
            }

            return render(request, 'fusion/leaveModule0/leavestatus.html', context)

        elif cake == 'approve':
            context = GetApplications.get_to_approve(request)
            return render(request, 'fusion/leaveModule0/leaveapprove.html', context)

        elif cake == 'detail':
            pk = request.GET.get('pk')
            leave = Leave.objects.get(pk=pk)

            return render(request, 'fusion/leaveModule0/details.html', {'leave': leave})

        else:
            return HttpResponse('You can\'t see this page.')

class ApplyLeave(View):
    """
        A Class Based View which handles user applying for leave
    """
    def get(self, request):
        """
            view to handle get request to /leave/apply
        """
        # TODO: Check if leave not rejected or accepted and leave instance belongs to user
        # TODO: Take another value as action so that action can specify edit or delete with same
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
                    station_start_date = form.cleaned_data.get('station_start_date'),
                    station_end_date = form.cleaned_data.get('station_end_date'),
                    end_date = form.cleaned_data['end_date'],
                    station = form.cleaned_data.get('station_leave'),
                )

            except Exception as e:
                return render(request,
                              'leave_application/apply_for_leave.html',
                              {'form': form, 'message': 'Failed'})

            return redirect('/leave/?message=success')

        else:
            context = {'form': form, 'title': 'Leave', 'action':'Apply'}
            year = datetime.date.today().year
            leaves_count = LeavesCount.objects.get(user=request.user, year=year)
            context['leaves_count'] = leaves_count
            context.update(GetApplications.get_reps(request))
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

    def post(self, request, id):
        leave_request = get_object_or_404(CurrentLeaveRequest, id=id)

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
        remark = request.POST.get('remark', '')
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
        remark = request.POST.get('remark', '')

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

        remark = request.POST.get('remark', '')
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
                    leave = leave_request.leave,
                    permission = 'sanc_officer',
                )
        else:
            response = None

        return response



    @transaction.atomic
    def create_leave_request(self, cur_leave_request, final, accept=False, remark=''):
        if cur_leave_request.leave.type_of_leave not in ['casual', 'restricted'] and \
            cur_leave_request.permission == 'sanc_auth':
            status = True
        else:
            status = accept

        leave_request = LeaveRequest.objects.create(
            leave = cur_leave_request.leave,
            applicant = cur_leave_request.applicant,
            requested_from = cur_leave_request.requested_from,
            remark = remark,
            permission = cur_leave_request.permission,
            position = cur_leave_request.position,
            status = status,
        )

        if not accept and final:
            cur_leave_request.leave.status = 'rejected'
        elif final:
            curr_year = datetime.date.today().year
            start_date = cur_leave_request.leave.start_date
            end_date = cur_leave_request.leave.end_date
            if curr_year == start_date.year and curr_year == end_date.year:
                count = LeavesCount.objects.get(user=cur_leave_request.applicant, year=curr_year)

                remain = getattr(count, cur_leave_request.leave.type_of_leave)
                required_leaves = cur_leave_request.leave.count_work_days

                if remain < required_leaves:
                    cur_leave_request.leave.status = 'rejected'
                else:
                    setattr(count, cur_leave_request.leave.type_of_leave,
                                   remain - required_leaves)
                    count.save()
                    self.create_migration(cur_leave_request.leave)
                    cur_leave_request.leave.status = 'accepted'
            elif curr_year == start_date.year and end_date.year == curr_year + 1:
                final_date = datetime.date(curr_year, 12, 31)

                days_in_curr_year = count_work_days(start_date, final_date)
                final_date += datetime.timedelta(days=1)
                days_in_next_year = count_work_days(final_date, end_date)
                curr_count = LeavesCount.objects.get(user=cur_leave_request.applicant,
                                                     year=start_date.year)
                next_count = LeavesCount.objects.get(user=cur_leave_request.applicant,
                                                     year=end_date.year)

                curr_remaining = getattr(curr_count, cur_leave_request.leave.type_of_leave)
                next_remaining = getattr(next_count, cur_leave_request.leave.type_of_leave)

                if curr_remaining >= days_in_curr_year and next_remaining >= days_in_next_year:
                    setattr(curr_count, cur_leave_request.leave.type_of_leave,
                            curr_remaining - days_in_curr_year)
                    curr_count.save()
                    setattr(next_count, cur_leave_request.leave.type_of_leave,
                            next_remaining - days_in_next_year)
                    next_count.save()
                    self.create_migration(cur_leave_request.leave)
                    cur_leave_request.leave.status = 'accepted'
                else:
                    cur_leave_request.leave.status = 'rejected'

            elif start_date.year + 1 == crr_year and end_date.year + 1 == curr_year:
                count = LeavesCount.objects.get(user=cur_leave_request.applicant, year=curr_year+1)

                remain = getattr(count, cur_leave_request.leave.type_of_leave)
                required_leaves = cur_leave_request.leave.count_work_days
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

        if leave.start_date <= datetime.date.today():

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

        replacements = Replacement.objects.filter(Q(replacer=request.user)
                                                 & Q(replacement_type='administrative'))
        reqs = CurrentLeaveRequest.objects.filter(Q(requested_from=request.user)
                                                          & ~(Q(permission='academic')
                                                          | Q(permission='admin')))
        request_list = [cls.should_forward(request, q_obj) for q_obj in reqs]
        for replacement in replacements:
            replacee = replacement.replacee
            reqs = CurrentLeaveRequest.objects.filter((Q(requested_from=request.user)
                                                              | Q(requested_from=replacee))
                                                              & ~(Q(permission='academic')
                                                              | Q(permission='admin')))
            request_list += [cls.should_forward(request, q_obj) for q_obj in reqs]


        context = {
            'processed_request_list': processed_request_list,
            'request_list': request_list,
        }
        return context

    @classmethod
    def get_count(cls, request):
        processed_request_list_exists = LeaveRequest.objects.filter(requested_from=request.user).exists()

        if processed_request_list_exists:
            return True

        replacements = Replacement.objects.filter(Q(replacer=request.user)
                                                 & Q(replacement_type='administrative'))
        reqs = CurrentLeaveRequest.objects.filter(Q(requested_from=request.user)
                                                  & ~(Q(permission='academic')
                                                    | Q(permission='admin'))).exists()
        if reqs:
            return reqs

        for replacement in replacements:
            replacee = replacement.replacee
            reqs = CurrentLeaveRequest.objects.filter((Q(requested_from=request.user)
                                                              | Q(requested_from=replacee))
                                                              & ~(Q(permission='academic')
                                                              | Q(permission='admin'))).exists()

            if reqs:
                return True

        return False

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
