from google import genai
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Standard, Customer, Answer, Report, Question, Sector, SectorCategory, AnswerSelection
from django.contrib.auth.models import User, Group
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
from .forms import StandardForm, SubmittedAnswerForm, CustomUserCreationForm
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden
from django.http import HttpResponse 
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.views import LoginView

# Custom decorator to check if user is in a specific group and redirect to form submission if not
def group_required(group_name, redirect_to='reports'):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                # Redirect unauthenticated users to login page
                return HttpResponseRedirect(reverse('login'))
            if not request.user.groups.filter(name=group_name).exists():
                # Redirect authenticated users without group to formsubmission
                return HttpResponseRedirect(reverse(redirect_to))
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# Custom decorator to check if user is in a specific group

# def group_required(group_name):
#     def in_group(user):
#         return user.is_authenticated and user.groups.filter(name=group_name).exists()
#     return user_passes_test(in_group)




load_dotenv()  # This loads the variables from .env

# Now access your environment variable
api_key = os.environ.get('OPENAI_API_KEY', "OPENAI_API_KEY")
# print("WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW", api_key)
if api_key is None:
    raise ValueError("API key is not set in the environment variables.")

client = OpenAI(api_key=api_key)


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data.get('email')
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.save()

            # Add user to 'CUSTOMERS' group
            group, created = Group.objects.get_or_create(name='CUSTOMERS')
            user.groups.add(group)

            login(request, user)
            return redirect('chatbot')  # redirect to chatbot page
    else:
        form = CustomUserCreationForm()
    return render(request, 'grc/register_all.html', {'form': form})


# def register(request):
#     if request.method == 'POST':
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             username = form.cleaned_data.get('username')
#             password = form.cleaned_data.get('password1')
#             email_address = form.cleaned_data.get('email')
#             user = authenticate(username=username, password=password, email=email_address)
#             login(request, user)
#             return redirect('index')
#     else:
#         form = UserCreationForm()
#     return render(request, 'grc/register_all.html', {'form': form})



class CustomLoginView(LoginView):
    def get_success_url(self):
        if self.request.user.groups.filter(name="CUSTOMERS").exists():
            return reverse('chatbot')
        return reverse('index')




def index(request):
    return render(request, 'grc/index.html')

@group_required('NORMATURK')
@login_required
def standards(request):
    standards_list = Standard.objects.all()
    context = {'standards_list': standards_list}
    return render(request, 'grc/standards.html', context)

@group_required('NORMATURK')
@login_required
def customers(request):
    customers_list = Customer.objects.all()
    context = {'customers_list': customers_list, 'request': request}
    return render(request, 'grc/customers.html', context)

@group_required('NORMATURK')
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

@group_required('NORMATURK')
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
            "decision_support, regulatory_requirements, stakeholder_expectations, competitor_analysis, risk_surface, "
            "primary_risks, governance_focus, governance_topics, minimum_policy_set, minimum_solution_set, and solution_roadmap. "
            "Focus particularly on any governance inefficiencies, compliance shortfalls, and security vulnerabilities, offering "
            "practical recommendations wherever relevant. Return the response in JSON format according to the provided schema. "
            "Here are the institution’s responses to asked questions:\n\n"
            f"{question_answer_pair}"
        )

        try:
            client = genai.Client(api_key="AIzaSyAtq5_gUknCT4D6ZHzp7EePKk0Bl-30sGk")  # Replace with your Gemini API key
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': AnalysisResponse,
                },
            )

            # Parse the JSON response
            analysis_result = AnalysisResponse.parse_raw(response.text)

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

# @group_required('NORMATURK')
# @login_required
# def create_report(request):
#     user = request.user
#     total_questions = Question.objects.count()
#     answered_questions = Answer.objects.filter(user=user).count()

#     # Check prerequisites
#     if total_questions == 0:
#         messages.error(request, "No questions available to answer.")
#         return redirect('reports')
#     if answered_questions != total_questions:
#         messages.error(request, "You must answer all questions before creating or updating a report.")
#         return redirect('reports')

#     # Get user’s answers (available for both GET and POST)
#     answers = Answer.objects.filter(user=user).select_related('question')
#     question_answer_pair = {answer.question.text: answer.response for answer in answers}

#     if request.method == "POST":
#         # Prepare API prompt
#         prompt = (
#             "Analyze the following answers provided by the institution to identify deficiencies in governance, compliance, "
#             "and information security across multiple areas. For each of the following topics, write a concise, well-thought-out "
#             "list of sentences, total 100 words at most as bullet items (3-4 sentences) that is specific, highlights potential areas for improvement, "
#             "and provides tangible, actionable suggestions for strengthening each area. The topics to address are: "
#             "decision support, regulatory requirements, stakeholder expectations, competitor analysis, risk surface, "
#             "primary_risks, governance focus, governance topics, minimum policy set, minimum solution set, and solution roadmap. "
#             "Focus particularly on any governance inefficiencies, compliance shortfalls, and security vulnerabilities, offering "
#             "practical recommendations wherever relevant. Here are the institution’s responses to asked questions:\n\n"
#             f"{question_answer_pair}"
#         )

#         try:
#             client = OpenAI()  # Initialize with your API key
#             completion = client.beta.chat.completions.parse(
#                 model="gpt-4o-mini",
#                 messages=[
#                     {"role": "system", "content": "You are an analytical assistant."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 response_format=AnalysisResponse,
#                 max_tokens=1500
#             )
#             analysis_result = completion.choices[0].message.parsed

#             # Update or create report
#             report, created = Report.objects.get_or_create(
#                 user=user,
#                 defaults={
#                     'completed_at': timezone.now(),
#                     'decision_support': analysis_result.decision_support,
#                     'regulatory_requirements': analysis_result.regulatory_requirements,
#                     'stakeholder_expectations': analysis_result.stakeholder_expectations,
#                     'competitor_analysis': analysis_result.competitor_analysis,
#                     'risk_surface': analysis_result.risk_surface,
#                     'primary_risks': analysis_result.primary_risks,
#                     'governance_focus': analysis_result.governance_focus,
#                     'governance_topics': analysis_result.governance_topics,
#                     'minimum_policy_set': analysis_result.minimum_policy_set,
#                     'minimum_solution_set': analysis_result.minimum_solution_set,
#                     'solution_roadmap': analysis_result.solution_roadmap,
#                 }
#             )
#             if not created:
#                 # Update existing report
#                 report.completed_at = timezone.now()
#                 report.decision_support = analysis_result.decision_support
#                 report.regulatory_requirements = analysis_result.regulatory_requirements
#                 report.stakeholder_expectations = analysis_result.stakeholder_expectations
#                 report.competitor_analysis = analysis_result.competitor_analysis
#                 report.risk_surface = analysis_result.risk_surface
#                 report.primary_risks = analysis_result.primary_risks
#                 report.governance_focus = analysis_result.governance_focus
#                 report.governance_topics = analysis_result.governance_topics
#                 report.minimum_policy_set = analysis_result.minimum_policy_set
#                 report.minimum_solution_set = analysis_result.minimum_solution_set
#                 report.solution_roadmap = analysis_result.solution_roadmap
#                 report.save()

#             messages.success(request, "Report created successfully!" if created else "Report updated successfully!")
#         except Exception as e:
#             messages.error(request, f"Error generating report: {str(e)}")

#         return redirect('reports')

#     # For GET: render the template with answers
#     return render(request, 'grc/create_report.html', {'question_answer_pair': question_answer_pair})


@group_required('NORMATURK')
@login_required
def user_create_report(request, user_id):
    user = User.objects.get(id=user_id)
    total_questions = Question.objects.count()
    answered_questions = Answer.objects.filter(user=user).count()

    # Check prerequisites
    if total_questions == 0:
        messages.error(request, "No questions available to answer.")
        return redirect('users')
    if answered_questions != total_questions:
        messages.error(request, "You must answer all questions before creating or updating a report.")
        return redirect('users')

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
            "decision_support, regulatory_requirements, stakeholder_expectations, competitor_analysis, risk_surface, "
            "primary_risks, governance_focus, governance_topics, minimum_policy_set, minimum_solution_set, and solution_roadmap. "
            "Focus particularly on any governance inefficiencies, compliance shortfalls, and security vulnerabilities, offering "
            "practical recommendations wherever relevant. Return the response in JSON format according to the provided schema. "
            "Here are the institution’s responses to asked questions:\n\n"
            f"{question_answer_pair}"
        )

        try:
            client = genai.Client(api_key="AIzaSyAtq5_gUknCT4D6ZHzp7EePKk0Bl-30sGk")  # Replace with your Gemini API key
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': AnalysisResponse,
                },
            )

            # Parse the JSON response
            analysis_result = AnalysisResponse.parse_raw(response.text)

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

        return redirect('users')

    return render(request, 'grc/user_create_report.html')


# @group_required('NORMATURK')
# @login_required
# def user_create_report(request, user_id):
#     user = User.objects.get(id=user_id)
#     total_questions = Question.objects.count()
#     answered_questions = Answer.objects.filter(user=user).count()

#     # Check prerequisites
#     if total_questions == 0:
#         messages.error(request, "No questions available to answer.")
#         return redirect('users')
#     if answered_questions != total_questions:
#         messages.error(request, "You must answer all questions before creating or updating a report.")
#         return redirect('users')

#     # Get user’s answers (available for both GET and POST)
#     answers = Answer.objects.filter(user=user).select_related('question')
#     question_answer_pair = {answer.question.text: answer.response for answer in answers}

#     if request.method == "POST":
#         # Prepare API prompt
#         prompt = (
#             "Analyze the following answers provided by the institution to identify deficiencies in governance, compliance, "
#             "and information security across multiple areas. For each of the following topics, write a concise, well-thought-out "
#             "list of sentences, total 100 words at most as bullet items (3-4 sentences) that is specific, highlights potential areas for improvement, "
#             "and provides tangible, actionable suggestions for strengthening each area. The topics to address are: "
#             "decision support, regulatory requirements, stakeholder expectations, competitor analysis, risk surface, "
#             "primary_risks, governance focus, governance topics, minimum policy set, minimum solution set, and solution roadmap. "
#             "Focus particularly on any governance inefficiencies, compliance shortfalls, and security vulnerabilities, offering "
#             "practical recommendations wherever relevant. Here are the institution’s responses to asked questions:\n\n"
#             f"{question_answer_pair}"
#         )

#         try:
#             client = OpenAI()  # Initialize with your API key
#             completion = client.beta.chat.completions.parse(
#                 model="gpt-4o-mini",
#                 messages=[
#                     {"role": "system", "content": "You are an analytical assistant."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 response_format=AnalysisResponse,
#                 max_tokens=1500
#             )
#             analysis_result = completion.choices[0].message.parsed

#             # Update or create report
#             report, created = Report.objects.get_or_create(
#                 user=user,
#                 defaults={
#                     'completed_at': timezone.now(),
#                     'decision_support': analysis_result.decision_support,
#                     'regulatory_requirements': analysis_result.regulatory_requirements,
#                     'stakeholder_expectations': analysis_result.stakeholder_expectations,
#                     'competitor_analysis': analysis_result.competitor_analysis,
#                     'risk_surface': analysis_result.risk_surface,
#                     'primary_risks': analysis_result.primary_risks,
#                     'governance_focus': analysis_result.governance_focus,
#                     'governance_topics': analysis_result.governance_topics,
#                     'minimum_policy_set': analysis_result.minimum_policy_set,
#                     'minimum_solution_set': analysis_result.minimum_solution_set,
#                     'solution_roadmap': analysis_result.solution_roadmap,
#                 }
#             )
#             if not created:
#                 # Update existing report
#                 report.completed_at = timezone.now()
#                 report.decision_support = analysis_result.decision_support
#                 report.regulatory_requirements = analysis_result.regulatory_requirements
#                 report.stakeholder_expectations = analysis_result.stakeholder_expectations
#                 report.competitor_analysis = analysis_result.competitor_analysis
#                 report.risk_surface = analysis_result.risk_surface
#                 report.primary_risks = analysis_result.primary_risks
#                 report.governance_focus = analysis_result.governance_focus
#                 report.governance_topics = analysis_result.governance_topics
#                 report.minimum_policy_set = analysis_result.minimum_policy_set
#                 report.minimum_solution_set = analysis_result.minimum_solution_set
#                 report.solution_roadmap = analysis_result.solution_roadmap
#                 report.save()

#             messages.success(request, "Report created successfully!" if created else "Report updated successfully!")
#         except Exception as e:
#             messages.error(request, f"Error generating report: {str(e)}")

#         return redirect('users')
#     return render(request, 'grc/user_create_report.html')




@group_required('NORMATURK')
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


@group_required('NORMATURK')
@login_required
def user_view_report(request, user_id):
    report = Report.objects.get(user = user_id)
    print("Report:", report)
    return render(request, 'grc/user_view_report.html', {'report': report})

@group_required('NORMATURK')
@login_required
def users(request):
    groups = Group.objects.all()
    users = User.objects.all()
    # customer_users = User.objects.filter(groups = 2) # group id 2 refers to "customers" group

    customer_form_info = []
    for customer_user in users:
        if str(customer_user.answers.count()) == str(Question.objects.count()):
            is_form_completed = True
        else:
            is_form_completed = False

        if Report.objects.filter(user=customer_user).exists():
            is_report_created = True
        else:   
            is_report_created = False
        customer_form_info.append(
            {
            'customer_user': customer_user,
            'is_form_completed': is_form_completed,
            'is_report_created': is_report_created,
        }
        )
    print("Customer Form Info:", customer_form_info)

    context = {'users': users,
               'groups': groups,
               'customer_form_info': customer_form_info,
            }
    return render(request, 'grc/users.html', context)

@group_required('NORMATURK')
@login_required
def update_user_form(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User does not exist.")
        return redirect('users')

    questions = Question.objects.all()
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
                return redirect('update_user_form', user_id=user.id)
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
        'user': user,
    }
    return render(request, 'grc/update_user_form.html', context)














@group_required('NORMATURK')
@login_required
def update_user_form_test(request, user_id):
    user = User.objects.get(id = user_id)
    form = SubmittedAnswerForm()
    questions = Question.objects.all()

    if request.method == 'POST':
        
        question_id = request.POST.get('question_id')
        form = SubmittedAnswerForm(request.POST)
        if form.is_valid():
            answer = Answer.objects.filter(user= user, question=question_id).first()
            if answer:
                answer.response = form.cleaned_data['response']
                answer.save()
            else:
                answer = Answer(user=user,question = question_id, response = form.cleaned_data['response'])
                answer.save()
            messages.success(request, f"Answer saved successfully! for {question_id}. question")
            return redirect('update_user_form_test', user_id=user.id)
    question_forms = []
    for question in questions:
        answer = Answer.objects.filter(user = user, question = question.id).first()
        initial = {'response': answer.response if answer else None}
        context = {
            'form': SubmittedAnswerForm(initial=initial),
            'user': user,
            'question': question,
        }
        question_forms.append(context)

    return render(request, 'grc/update_user_form_test.html', {'question_forms': question_forms})


@login_required
def chatbot(request):
    user = request.user # Get all questions ordered by ID 
    questions = Question.objects.all().order_by('id')

    if not questions:
        messages.error(request, "No questions available.")
        return redirect('reports')

    # Find the first unanswered question
    current_question = None
    for question in questions:
        if not Answer.objects.filter(user=user, question=question).exists():
            current_question = question
            break

    if request.method == "POST":
        question_id = request.POST.get('question_id')
        selected_answers = request.POST.getlist('answer_selections')  # Get list of selected answer IDs
        custom_answer = request.POST.get('custom_answer', '').strip()
        
        try:
            question = Question.objects.get(id=question_id)
            # Combine selected answers and custom answer
            answer_text = []
            if selected_answers:
                selected_texts = AnswerSelection.objects.filter(id__in=selected_answers).values_list('answer_text', flat=True)
                answer_text.extend(selected_texts)
            if custom_answer:
                answer_text.append(custom_answer)
            response = "; ".join(answer_text) if answer_text else ""
            
            if not response:
                messages.error(request, "Please select at least one option or provide a custom answer.")
                return render(request, 'grc/chatbot.html', {
                    'question': question,
                    'answer_selections': AnswerSelection.objects.filter(question=question),
                    'selected_answers': selected_answers,
                    'custom_answer': custom_answer
                })
            
            # Save or update the answer
            Answer.objects.update_or_create(
                user=user,
                question=question,
                defaults={'response': response}
            )
            messages.success(request, "Answer saved successfully!")
            
            # Redirect to the next unanswered question or reports page
            next_question = None
            for q in questions:
                if not Answer.objects.filter(user=user, question=q).exists():
                    next_question = q
                    break
            if next_question:
                return redirect('chatbot')
            else:
                messages.success(request, "All questions answered!")
                return redirect('reports')
                
        except Question.DoesNotExist:
            messages.error(request, "Invalid question.")
            return redirect('chatbot')

    # For GET request or after answering
    if not current_question:
        # All questions answered
        messages.info(request, "You have answered all questions.")
        return redirect('reports')

    return render(request, 'grc/chatbot.html', {
        'question': current_question,
        'answer_selections': AnswerSelection.objects.filter(question=current_question)
    })