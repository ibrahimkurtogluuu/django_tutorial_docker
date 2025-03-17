from django.db import models

# Create your models here.

class Standard(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField(max_length=200, default='Default Customer Name')
    sectors = models.ManyToManyField('Sector', blank=True)
    
    def __str__(self):
        return self.name

class Sector(models.Model):
    name = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name
