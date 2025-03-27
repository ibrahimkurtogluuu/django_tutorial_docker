from django.shortcuts import render, redirect
from .models import Standard, Customer, Answer, Report, Question, Sector, SectorCategory
from django.http import HttpResponseRedirect
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

# Create your views here.

from django.http import HttpResponse

load_dotenv()  # This loads the variables from .env

# Now access your environment variable
api_key = os.environ.get('OPENAI_API_KEY', "OPENAI_API_KEY")
# print("WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW", api_key)
if api_key is None:
    raise ValueError("API key is not set in the environment variables.")

client = OpenAI(api_key=api_key)



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


    reports = Report.objects.all()
    
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
    sessions_not_answered_all_questions = set(all_sessions) - set(sessions_with_all_questions_answered)

    
    answers = Answer.objects.all()
    first_answer_date = answers[0].submitted_at
    
    # Prepare a dictionary to check report existence for each session
    session_report_status = {
        session_id: Report.objects.filter(session_id=session_id).exists()
        for session_id in sessions_with_all_questions_answered
    }

    context = {
        'sessions_with_all_questions_answered': sessions_with_all_questions_answered,
        'all_sessions': all_sessions,
        'sessions_not_answered_all_questions': sessions_not_answered_all_questions,
        'date': first_answer_date,
        'session_report_status': session_report_status,
    }

    return render(request, 'grc/reports.html', context)

def create_report(request, session_id):
    if request.method == "POST":

        # Get all answers for the given session_id    
        answers = Answer.objects.filter(session_id=session_id)
        questions = Question.objects.all()
        answer_texts_list = answers.values_list('response', flat=True)
        question_texts_list = questions.values_list('text', flat=True)
        # pairing the questions and answers in a dictionary
        question_answer_pair = {
        question_texts_list[i]:answer_texts_list[i]
        for i in range(0,11)
        }

        # Prepare the prompt for the API
            # Define the prompt as discussed
        prompt = (
            "Analyze the following answers provided by the institution to identify deficiencies in governance, compliance, "
            "and information security across multiple areas. For each of the following topics, write a concise, well-thought-out "
            "a list of sentences, total 100 words at most as bullet items (3-4 sentences) that is specific, highlights potential areas for improvement, "
            "and provides tangible, actionable suggestions for strengthening each area. The topics to address are: "
            "decision support, regulatory requirements, stakeholder expectations, competitor analysis, risk surface, "
            "primary risks, governance focus, governance topics, minimum policy set, minimum solution set, and solution roadmap. "
            "Focus particularly on any governance inefficiencies, compliance shortfalls, and security vulnerabilities, offering "
            "practical recommendations wherever relevant. And give them a solution road map to deal with those inefficiencies. Here are the institution’s responses to asked questions:\n\n"
            f"{question_answer_pair}"
        )

        # Define structured output model for parsing the API response
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


        if Report.objects.filter(session_id=session_id).values('summary').exists() == True:
            messages.error(request, f"Report for session {session_id} already exists!")
            return redirect('reports')
        # Create a report for the given session_id
        else:

                # Call the API with structured response format
            try:
                completion = client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an analytical assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format=AnalysisResponse,
                    max_tokens=1500  # Adjust based on estimated need for longer outputs
                )

                # Access the structured response
                analysis_result = completion.choices[0].message.parsed

                Report.objects.create(
                    session_id=session_id,
                    completed_at=timezone.now(),
                    decision_support=analysis_result.decision_support,
                    regulatory_requirements=analysis_result.regulatory_requirements,
                    stakeholder_expectations=analysis_result.stakeholder_expectations,
                    competitor_analysis=analysis_result.competitor_analysis,
                    risk_surface=analysis_result.risk_surface,
                    primary_risks=analysis_result.primary_risks,
                    governance_focus=analysis_result.governance_focus,
                    governance_topics=analysis_result.governance_topics,
                    minimum_policy_set=analysis_result.minimum_policy_set,
                    minimum_solution_set=analysis_result.minimum_solution_set,
                    solution_roadmap=analysis_result.solution_roadmap
                )

            except Exception as e:
                print("Error generating structured output:", e)



            if Report.objects.filter(session_id=session_id).values('summary').exists():
                messages.success(request, f"Report for session {session_id} has been created successfully!")
        return redirect('reports')  # Redirect back to the reports page


def view_report(request, session_id):
    report = Report.objects.get(session_id=session_id)
    context = {'report': report}
    return render(request, 'grc/view_report.html', context)