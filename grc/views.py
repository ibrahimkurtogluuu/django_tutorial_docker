from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Standard, Customer, Answer, Report, Question, Sector, SectorCategory
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count
from django.db.models import Q
from django.db.models import Sum    
from django.contrib import messages
from openai import OpenAI
import os
from dotenv import load_dotenv
from openai import Completion
from pydantic import BaseModel
import uuid
from .forms import StandardForm
# Create your views here.

from django.http import HttpResponse

load_dotenv()  # This loads the variables from .env

# Now access your environment variable
api_key = os.environ.get('OPENAI_API_KEY', "OPENAI_API_KEY")
# print("WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW", api_key)
if api_key is None:
    raise ValueError("API key is not set in the environment variables.")

client = OpenAI(api_key=api_key)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'grc/register.html', {'form': form})

def index(request):
    return render(request, 'grc/index.html')

@login_required
def standards(request):
    standards_list = Standard.objects.all()
    context = {'standards_list': standards_list}
    return render(request, 'grc/standards.html', context)

@login_required
def customers(request):
    customers_list = Customer.objects.all()
    context = {'customers_list': customers_list}
    return render(request, 'grc/customers.html', context)


@login_required
def form_standards(request):
    if request.method == 'POST':
        form = StandardForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('standards')
    else:
        form = StandardForm()
    return render(request, 'grc/form_standards.html', {'form': form})


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Question, Answer
from .forms import SubmittedAnswerForm

@login_required
def form_submission(request):
    questions = Question.objects.all()
    user = request.user

    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        try:
            question = Question.objects.get(id=question_id)
            form = SubmittedAnswerForm(request.POST)
            if form.is_valid():
                # Check if answer exists
                answer, created = Answer.objects.get_or_create(
                    user=user,
                    question=question,
                    defaults={'response': form.cleaned_data['response']}
                )
                if not created:
                    # Update existing answer
                    answer.response = form.cleaned_data['response']
                    answer.save()
                messages.success(request, f"Answer saved for question: {question.text[:20]}...")
                return redirect('form_submission')
        except Question.DoesNotExist:
            messages.error(request, "Invalid question selected.")
        except Exception as e:
            messages.error(request, f"Error saving answer: {str(e)}")
    else:
        form = SubmittedAnswerForm()

    # Prepare question forms with prefilled answers
    question_forms = []
    for question in questions:
        answer = Answer.objects.filter(user=user, question=question).first()
        initial = {'response': answer.response if answer else None}
        question_forms.append({
            'question': question,
            'form': SubmittedAnswerForm(initial=initial),
            'answered': answer is not None
        })

    context = {
        'question_forms': question_forms,
    }
    return render(request, 'grc/form_submission.html', context)

    

# Structured output model for API response
class AnalysisResponse(BaseModel):
    decision_support: str
    regulatory_requirements: str
    stakeholder_expectations: str
    competitor_analysis: str
    risk_surface: str
    primary_risks: str
    governance_focus: str
    governance_topics: str
    minimum_policy_set: str
    minimum_solution_set: str
    solution_roadmap: str

@login_required
def reports(request):
    user = request.user
    total_questions = Question.objects.count()
    answered_questions = Answer.objects.filter(user=user).count()
    has_all_answers = answered_questions == total_questions
    report_exists = Report.objects.filter(user=user).exists()

    context = {
        'total_questions': total_questions,
        'answered_questions': answered_questions,
        'has_all_answers': has_all_answers,
        'report_exists': report_exists,
    }
    return render(request, 'grc/reports.html', context)




@login_required
def create_report(request):
    user = request.user
    total_questions = Question.objects.count()
    answered_questions = Answer.objects.filter(user=user).count()

    # Check prerequisites
    if total_questions == 0:
        messages.error(request, "No questions available to answer.")
        return redirect('reports')
    if answered_questions != total_questions:
        messages.error(request, "You must answer all questions before creating or updating a report.")
        return redirect('reports')

    # Get user’s answers (available for both GET and POST)
    answers = Answer.objects.filter(user=user).select_related('question')
    question_answer_pair = {answer.question.text: answer.response for answer in answers}

    if request.method == "POST":
        # Prepare API prompt
        prompt = (
            "Analyze the following answers provided by the institution to identify deficiencies in governance, compliance, "
            "and information security across multiple areas. For each of the following topics, write a concise, well-thought-out "
            "list of sentences, total 100 words at most as bullet items (3-4 sentences) that is specific, highlights potential areas for improvement, "
            "and provides tangible, actionable suggestions for strengthening each area. The topics to address are: "
            "decision support, regulatory requirements, stakeholder expectations, competitor analysis, risk surface, "
            "primary_risks, governance focus, governance topics, minimum policy set, minimum solution set, and solution roadmap. "
            "Focus particularly on any governance inefficiencies, compliance shortfalls, and security vulnerabilities, offering "
            "practical recommendations wherever relevant. Here are the institution’s responses to asked questions:\n\n"
            f"{question_answer_pair}"
        )

        try:
            client = OpenAI()  # Initialize with your API key
            completion = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an analytical assistant."},
                    {"role": "user", "content": prompt}
                ],
                response_format=AnalysisResponse,
                max_tokens=1500
            )
            analysis_result = completion.choices[0].message.parsed

            # Update or create report
            report, created = Report.objects.get_or_create(
                user=user,
                defaults={
                    'completed_at': timezone.now(),
                    'decision_support': analysis_result.decision_support,
                    'regulatory_requirements': analysis_result.regulatory_requirements,
                    'stakeholder_expectations': analysis_result.stakeholder_expectations,
                    'competitor_analysis': analysis_result.competitor_analysis,
                    'risk_surface': analysis_result.risk_surface,
                    'primary_risks': analysis_result.primary_risks,
                    'governance_focus': analysis_result.governance_focus,
                    'governance_topics': analysis_result.governance_topics,
                    'minimum_policy_set': analysis_result.minimum_policy_set,
                    'minimum_solution_set': analysis_result.minimum_solution_set,
                    'solution_roadmap': analysis_result.solution_roadmap,
                }
            )
            if not created:
                # Update existing report
                report.completed_at = timezone.now()
                report.decision_support = analysis_result.decision_support
                report.regulatory_requirements = analysis_result.regulatory_requirements
                report.stakeholder_expectations = analysis_result.stakeholder_expectations
                report.competitor_analysis = analysis_result.competitor_analysis
                report.risk_surface = analysis_result.risk_surface
                report.primary_risks = analysis_result.primary_risks
                report.governance_focus = analysis_result.governance_focus
                report.governance_topics = analysis_result.governance_topics
                report.minimum_policy_set = analysis_result.minimum_policy_set
                report.minimum_solution_set = analysis_result.minimum_solution_set
                report.solution_roadmap = analysis_result.solution_roadmap
                report.save()

            messages.success(request, "Report created successfully!" if created else "Report updated successfully!")
        except Exception as e:
            messages.error(request, f"Error generating report: {str(e)}")

        return redirect('reports')

    # For GET: render the template with answers
    return render(request, 'grc/create_report.html', {'question_answer_pair': question_answer_pair})





@login_required
def view_report(request):
    user = request.user
    try:
        report = Report.objects.get(user=user)
    except Report.DoesNotExist:
        messages.error(request, "No report exists for you.")
        return redirect('reports')
    context = {'report': report}
    return render(request, 'grc/view_report.html', context)
