from django.contrib import admin
from .models import Standard, Customer, Sector

class CustomerAdmin(admin.ModelAdmin):
    filter_horizontal = ('sectors',)  # Makes sector selection more user-friendly
    list_display = ('name', 'get_sectors')
    
    def get_sectors(self, obj):
        return ", ".join([sector.name for sector in obj.sectors.all()])
    get_sectors.short_description = 'Sectors'

class SectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_customers')
    
    def get_customers(self, obj):
        return ", ".join([customer.name for customer in obj.customer_set.all()])
    get_customers.short_description = 'Customers'

admin.site.register(Standard)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Sector, SectorAdmin)
