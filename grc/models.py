from django.db import models

# Create your models here.

class Standard(models.Model):
    standard_name = models.CharField(max_length=200)
    standard_description = models.TextField()
    
    def __str__(self):
        return self.standard_name

class Customer(models.Model):
    name = models.CharField(max_length=200, default='Default Customer Name')
    
    def __str__(self):
        return self.name
