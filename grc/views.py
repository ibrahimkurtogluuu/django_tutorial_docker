from django.shortcuts import render
from .models import Standard, Customer, Answer, Report, Question, Sector, SectorCategory
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count
from django.db.models import Q
from django.db.models import Sum    

# Create your views here.

from django.http import HttpResponse


def index(request):
    return render(request, 'grc/index.html')

def standards(request):
    standards_list = Standard.objects.all()
    context = {'standards_list': standards_list}
    return render(request, 'grc/standards.html', context)

def customers(request):
    customers_list = Customer.objects.all()
    context = {'customers_list': customers_list}
    return render(request, 'grc/customers.html', context)


def reports(request):
    # Get all questions
    total_questions = Question.objects.count()

    # Get sessions where all questions have been answered
    sessions_with_all_questions_answered = (
        Answer.objects.values('session_id')
        .annotate(answered_questions=Count('question', distinct=True))
        .filter(answered_questions=total_questions)
        .values_list('session_id', flat=True)
    )

    # Get all unique session values in the Answer table
    all_sessions = Answer.objects.values_list('session_id', flat=True).distinct()

    # Get sessions in all_sessions but not in sessions_with_all_questions_answered
    sessions_not_answered_all_questions = all_sessions.exclude(
        id__in=sessions_with_all_questions_answered
    )

    context = {
        'sessions_with_all_questions_answered': sessions_with_all_questions_answered,
        'all_sessions': all_sessions,
        'sessions_not_answered_all_questions': sessions_not_answered_all_questions,
    }

    return render(request, 'grc/reports.html', context)