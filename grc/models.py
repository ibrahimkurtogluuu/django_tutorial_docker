from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

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
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    session_id = models.CharField(max_length=100, blank=True, null=True)  # Optional Unique ID for session 
#   user = models.CharField(max_length=100, blank=True, null=True)  # Optional user
    response = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):

       # return f"Answer to '{self.question}' by {self.user or 'Anonymous'}" # Show user or 'Anonymous' if no user
        return f"Answer to '{self.question}' in {self.session_id} session" # Show user or 'Anonymous' if no user


class Report(models.Model):
    session_id = models.CharField(max_length=100, unique=True)  # Unique session
    completed_at = models.DateTimeField(auto_now_add=True)  # When report was generated
    summary = models.TextField(blank=True)  # Processed report data
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
        return f"Report for session {self.session_id}"  # Show session ID
        