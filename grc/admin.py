
from django.contrib import admin
from mptt.admin import MPTTModelAdmin  # Import MPTTModelAdmin for tree display
from .models import Standard, Customer, Sector, SectorCategory, Question, Answer, Report  # Add Question
from django.http import HttpResponseRedirect  # Import HttpResponseRedirect

class CustomerAdmin(admin.ModelAdmin):
    filter_horizontal = ('sectors',)  # Makes sector selection more user-friendly
    list_display = ('name', 'get_sectors')
    
    def get_sectors(self, obj):
        return ", ".join([sector.name for sector in obj.sectors.all()])
    get_sectors.short_description = 'Sectors'

class SectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'get_customers')
    list_filter = ('category',)  # Add filter by category
    
    def get_customers(self, obj):
        return ", ".join([customer.name for customer in obj.customer_set.all()])
    get_customers.short_description = 'Customers'

class SectorCategoryAdmin(MPTTModelAdmin):  # Changed to MPTTModelAdmin
    list_display = ('name', 'parent', 'level', 'get_sectors')  # Added parent and level for hierarchy
    list_filter = ('level',)  # Optional: filter by depth
    mptt_level_indent = 20  # Indents child nodes visually in the admin
    
    def get_sectors(self, obj):
        return ", ".join([sector.name for sector in obj.sectors.all()])
    get_sectors.short_description = 'Sectors'

# New Question admin
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'sector', 'created_at')
    list_filter = ('sector', 'created_at')

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'session_id', 'response', 'submitted_at')
    list_filter = ('question', 'submitted_at')
    search_fields = ('response', 'session_id')


# Report Admin
class ReportAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'completed_at', 'summary')  # Updated to match simplified model
    list_filter = ('completed_at', 'session_id')  # Added filter by session_id
    search_fields = ('session_id', 'summary')  # Added search by summary


# Register models with admin
admin.site.register(Standard)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Sector, SectorAdmin)
admin.site.register(SectorCategory, SectorCategoryAdmin)
admin.site.register(Question, QuestionAdmin)  # Add Question
admin.site.register(Answer, AnswerAdmin)  # Add Answer
admin.site.register(Report, ReportAdmin)