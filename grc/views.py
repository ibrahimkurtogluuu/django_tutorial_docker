from django.shortcuts import render
from .models import Standard, Customer

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