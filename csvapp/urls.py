from django.urls import path
from . import views,envelopsignal


urlpatterns =[
    path('', views.Home.as_view(), name = "Home"),
    path('index/', views.index, name = "Index"),
    path('upload/', views.upload_csv, name = "Upload"),
    
    path('fftdata/', views.fftdata, name = "FFTdata"),
    path('upload_withouttime/', views.upload_withouttime, name = "Upload_withouttime"),
    path('upload_csv/', views.upload_csv, name = "Upload_csv"),
    path('downloadcsv/', views.downloadcsv, name = "downloadcsv"),
    path('envelop/', envelopsignal.envelop_index, name = "Envelop"),
    path('envelop_upload_csv/', envelopsignal.envelop_upload_csv, name = "envelop_upload_csv"),
    path('envelop_upload_csv_nobfc/', envelopsignal.envelop_upload_csv_nobfc, name = "envelop_upload_csv_nobfc"),
  
    path('envelop_upload_withouttime/', envelopsignal.envelop_upload_withouttime, name = "envelop_upload_withouttime"),
    path('envelop_upload_withouttimenobfc/', envelopsignal.envelop_upload_withouttimenobfc, name = "envelop_upload_withouttimenobfc"),
   
    path('getmodelno/', envelopsignal.getmodelno, name = "getmodelno"),
    path('iiotportal/', views.iiotportal, name = "iiotportal"),
    
]


