from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Standard, Customer, Sector, SectorCategory, Question, Answer, Report, AnswerSelection

class CustomerAdmin(admin.ModelAdmin):
    filter_horizontal = ('sectors',)
    list_display = ('name', 'get_sectors')
    
    def get_sectors(self, obj):
        return ", ".join([sector.name for sector in obj.sectors.all()])
    get_sectors.short_description = 'Sectors'

class SectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'get_customers')
    list_filter = ('category',)
    
    def get_customers(self, obj):
        return ", ".join([customer.name for customer in obj.customer_set.all()])
    get_customers.short_description = 'Customers'

class SectorCategoryAdmin(MPTTModelAdmin):
    list_display = ('name', 'parent', 'level', 'get_sectors')
    list_filter = ('level',)
    mptt_level_indent = 20
    
    def get_sectors(self, obj):
        return ", ".join([sector.name for sector in obj.sectors.all()])
    get_sectors.short_description = 'Sectors'

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'sector', 'created_at')
    list_filter = ('sector', 'created_at')

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'response', 'user')
    list_filter = ('question', 'response', 'user')
    search_fields = ('response', 'question', 'user')  # Updated to search via submission

class ReportAdmin(admin.ModelAdmin):
    list_display = ( 'completed_at', 'user')  # Custom method for session_id
    list_filter = ('completed_at', 'user')  # Filter via submission

class AnswerSelectionAdmin(admin.ModelAdmin):
    list_display = ['question', 'answer_text']
    list_filter = ['question']

# Register models with admin
admin.site.register(Standard)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Sector, SectorAdmin)
admin.site.register(SectorCategory, SectorCategoryAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(AnswerSelection, AnswerSelectionAdmin)
