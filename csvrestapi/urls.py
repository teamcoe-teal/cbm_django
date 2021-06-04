from django.urls import path
from django.contrib import admin
from . import views,envelopsignal
from csvrestapi.views import index,upload_csv,testapi
from csvrestapi.envelopsignal import envelop_upload_csv,envelop_upload_csv_nobfc,envelop_upload_withouttime,envelop_upload_withouttimenobfc,getmodelno

urlpatterns = [
    
    #path('', views.Home.as_view(), name = "Home"),
    path('test/', index,name = 'index'),
    path('upload_csv/', upload_csv,name = 'upload_csv'),
    path('envelop_upload_csv/', envelop_upload_csv,name = 'envelop_upload_csv'),
    path('envelop_upload_csv_nobfc/', envelop_upload_csv_nobfc,name = 'envelop_upload_csv_nobfc'),
    path('envelop_upload_withouttime/', envelop_upload_withouttime,name = 'envelop_upload_withouttime'),
    path('envelop_upload_withouttimenobfc/', envelop_upload_withouttimenobfc,name = 'envelop_upload_withouttimenobfc'),
    path('testapi/', testapi,name = 'testapi'),
   
    path('getmodelno/', getmodelno,name = 'getmodelno'),
   
    #path('test/<int:pk>/', getaccesstokenfftdata.as_view()),
   
]
