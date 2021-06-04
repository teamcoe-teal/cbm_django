from django.contrib import admin
from .models import csvwithouttime,Fileupload

# Register your models here.
admin.site.register(csvwithouttime)

admin.site.register(Fileupload)