from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.contrib.auth.models import User
import uuid

# Create your models here.

class Standard(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    def __str__(self):
        return self.name

class SectorCategory(MPTTModel):  # Changed to inherit from MPTTModel
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')  # Use TreeForeignKey
    
    def __str__(self):
        return self.name
    
    class MPTTMeta:
        order_insertion_by = ['name']  # Optional: orders nodes alphabetically
    
    class Meta:
        verbose_name_plural = "Sector Categories"

class Sector(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(SectorCategory, on_delete=models.CASCADE, related_name='sectors', null=True, blank=True)
    
    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField(max_length=200, default='Default Customer Name')
    sectors = models.ManyToManyField('Sector', blank=True)
    
    def __str__(self):
        return self.name

# New Question model
class Question(models.Model):
    text = models.TextField()  # The question content
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)  # Optional link to a sector
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for creation
    
    def __str__(self):
        return self.text[:50]  # Show first 50 characters of the question




class Answer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    response = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'question')  # Ensures one answer per user per question

    def __str__(self):
        return f"{self.user.username} - {self.question.text[:20]}"

class Report(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='report')
    completed_at = models.DateTimeField(auto_now_add=True)  # When report was generated
    decision_support = models.TextField(blank=True, null=True)
    regulatory_requirements = models.TextField(blank=True, null=True)
    stakeholder_expectations = models.TextField(blank=True, null=True)
    competitor_analysis = models.TextField(blank=True, null=True)
    risk_surface = models.TextField(blank=True, null=True)
    primary_risks = models.TextField(blank=True, null=True)
    governance_focus = models.TextField(blank=True, null=True)
    governance_topics = models.TextField(blank=True, null=True)
    minimum_policy_set = models.TextField(blank=True, null=True)
    minimum_solution_set = models.TextField(blank=True, null=True)
    solution_roadmap = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Report"  # Show submission ID
        