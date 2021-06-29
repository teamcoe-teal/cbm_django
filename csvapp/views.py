from datetime import datetime, time
from django.shortcuts import render
from django.http import HttpResponse
from django.template import Context, loader
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from rest_framework.reverse import reverse
import logging
from django.contrib import messages
import requests
import pandas as pd
import numpy as np
import json
import csv
from django.contrib.sessions.models import Session
from datetime import datetime
from django.conf import settings
from csvapp.forms import csvwithouttime

# Create your views here.
# api_url = "http://127.0.0.1:8000/csvrestapi/"
api_url ="https://cbmapiteal.azurewebsites.net/csvrestapi/"

class Home(TemplateView):
	template_name = "csvapp/home.html"


def iiotportal(request):
	if request.method == "GET":
	#return HttpResponse()
		print("1")
		return render(request, "csvapp/iiotportal.html")

def index(request):
	if request.method == "POST":
	#return HttpResponse()
		print("1")

	
	return render(request, "csvapp/index.html")
    #return render('template:index.html', {})
 
def upload_csv(request):
    
	data = {}
   
	if "GET" == request.method:
		return render(request, "csvapp/upload.html", data)
	if "POST" == request.method:
		
		csv_file = request.FILES['file1']
		
		
		##	check for file extension
		if csv_file.name.endswith(".csv") != True:
			messages.error(request,'File is not CSV type')
			
			return render(request, "csvapp/upload.html", data)
       
		##	Read the csv file using pandas dataframe
		csv=pd.read_csv(csv_file,error_bad_lines=False)
	
		df = csv.loc[:, ~csv.columns.str.contains('^Unnamed')]
		df1 = csv.loc[:, ~csv.columns.str.contains(' ')]
		print(df1)
		#filtered_data = df.dropna(axis='columns', how='all')
		#rint(filtered_data)
		col=df1.columns.tolist()
		col1=df1.columns.tolist()
		## Get the column length
		n=len(col)
		noofcol=2
		print(n)
		for i in range(len(col)):
			col1[i] = col1[i].lower()
			if col1[i] == "amplitude":
				ampindex= col[i]
			if col1[i] == "time":
				timeindex=col[i]
		iucolnames=['From','To']
		colnames=['amplitude','time']
		
		if n < 2:
			messages.error(request,'please upload proper csv file')			
			return render(request, "csvapp/upload.html", data)
		##  If the column contains From and To the uploaded file is IU generated file,set the nofocol as 3
		if n !=2:
			for word in iucolnames:
				if not word in col:
					
					messages.error(request,'Upload correct IU generated csv file.....[From],[To]')
					return render(request, "csvapp/upload.html", data)
			
			noofcol=3 
			if col[2] == 'From' and col[3]=='To':
				noofcol = 3	
			else:
				messages.error(request,'Upload correct IU generated csv file')
				return render(request, "csvapp/upload.html", data)
		##  If the column contains Amplitude and time ,set the noofcol as 2
		if n>0 and noofcol==2:
			for word in colnames:
				if not word in col1:
					print("no columns")
					messages.error(request,'Upload correct csv file....[amplitude],[time]')
					return render(request, "csvapp/upload.html", data)
			
			
		

		
		
		## Convert csv file json object to string
		input_file1 = request.FILES.get(u'file1')
		if input_file1:
			
			df_json1 = json.dumps(csv.to_json(orient='records'))
			
		input_file_json = json.loads(df_json1)
		df_in_first_api = pd.read_json(input_file_json)

		##  Store raw data to plot the graph
		if noofcol==3:
			
			
			amplitude=df_in_first_api['Total Acceleration avg']
			time=df_in_first_api['From']
			rawdata={"amplitude":amplitude.tolist(),"time":time.tolist()}
			print(rawdata)
			#print(df_in_first_api)
		else:
			
			amplitude = df_in_first_api[ampindex]
			
			time=df_in_first_api[timeindex]
			rawdata={"amplitude":amplitude.tolist(),"time":time.tolist()}
			
		
				
		## get the remaining parameters

		modelnoval=request.POST.get("modelno")
		rpmval=request.POST.get("rpm")
		
		
		nval=request.POST.get("n")
		innerval=request.POST.get("inner")
		outerval=request.POST.get("outer")
		bdval=request.POST.get("bd")
		angleval=request.POST.get("angle")
		rpm = float(rpmval)
		print(modelnoval)
		if modelnoval is not None:
			modelno = modelnoval
		else:
			modelno = ""
		if innerval is "" or innerval is None:
			
			inner=""
		else:	
			rpm = float(rpmval)
		
			nb = int(nval)
			inner = float(innerval)
			outer = float(outerval)
			bd = float(bdval)
			angle = float(angleval)
		
		## API Call with url and payload

		url = api_url + "upload_csv/"
		payload = {"noofcol":noofcol,"input_file":df_json1,"modelno":modelno,"rpm":rpm,
		"nb":"null","inner":"null","outer":"null","bd":"null","angle":"null"}
		if inner!="":
		
			payload = {"noofcol":noofcol,"input_file":df_json1,"modelno":modelno,"rpm":rpm,
			"nb":nb,"inner":inner,"outer":outer,"bd":bd,"angle":angle}
	
		
		url_response = requests.post(url, data = payload)

		## store the json result
		fftdata1=url_response.json()
		
		fftdata3={"Frequencies":fftdata1['Frequencies'],"Amplitude":fftdata1['Amplitude']}

		##store bearing frequencies in sessions
		request.session['BPFO'] = fftdata1['BPFO']
		request.session['BPFI']= fftdata1['BPFI']
		request.session['BSF']= fftdata1['BSF']
		request.session['FTF']= fftdata1['FTF']
		FFTZip = dict(zip(fftdata1['Frequencies'],fftdata1['Amplitude']))
		
		request.session['FFTZip'] = FFTZip
		## Return the data to fftdata template
		return render(request, "csvapp/fftdata.html", {"fftdata":fftdata3,"rawdata":rawdata})			
		# except Exception as e:
		# 	logging.getLogger("error_logger").error("Unable to upload file. "+repr(e))
		# 	messages.error(request,"Unable to upload file. "+repr(e))


		
		#return HttpResponseRedirect(reverse("csvapp:upload")) 
		#return render(request, "csvapp/upload.html", data)


def upload_withouttime(request):
	data1 ={}
	if "GET" == request.method :
		print("uutrfvb")
        
		return render(request, "csvapp/upload.html", data1)

    # if not GET, then proceed
	#try:	
	data1={}

	CSVData = csvwithouttime(request.POST,request.FILES)
		
	## Access the input file from the payload	
	csv_file = request.FILES['file']
		
	sampfreq1 = request.POST.get("sampfreq")

	## Store the other parameters
	modelnoval=request.POST.get("modelno")

	rpmval=request.POST.get("rpm")
	
	nval=request.POST.get("n")
	innerval=request.POST.get("inner")
	outerval=request.POST.get("outer")
	bdval=request.POST.get("bd")
	angleval=request.POST.get("angle")
	rpm = float(rpmval)

	if modelnoval is not None:
		modelno = modelnoval
	else:
		modelno = ""
	if innerval == "" or innerval is None:
		
		inner=""
		
	else:
		
		nb = int(nval)
		inner = float(innerval)
		outer = float(outerval)
		bd = float(bdval)
		angle = float(angleval)
		
	
	
	
	# check if csv file or not
	if not csv_file.name.endswith('.csv'):
		print("not ending with .csv")
		messages.error(request,'File is not CSV type')
			
		return render(request, "csvapp/upload.html", data1)


	## 	Read the csv file using pandas dataframe and check for the columns accordingly
	csv=pd.read_csv(csv_file,error_bad_lines=False) 
	df = csv.loc[:, ~csv.columns.str.contains('^Unnamed')]
	df1 = csv.loc[:, ~csv.columns.str.contains(' ')]
	col=df1.columns.tolist()
	col1=df1.columns.tolist()
	for i in range(len(col)):
		col1[i] = col1[i].lower()
		if col1[i] == "amplitude":
			ampindex= col[i]
		
	colnames=['amplitude']	
	n = len(col)

	if n == 0:
		messages.error(request,'No columns to parse')			
		return render(request, "csvapp/upload.html", data1)
		
	if n != 1:
		messages.error(request,'File has more than 1 column')			
		return render(request, "csvapp/upload.html", data1)
	if n>0:
		for word in colnames:
			if not word in col1:
				print("no columns")
				messages.error(request,'Upload correct csv file....[amplitude]')
				return render(request, "csvapp/envelop.html", data1)
	
	
	
	## 	Convert csv file json object to string and 
	## store the rawdata to plot the graph
	input_file = request.FILES.get(u'file')
	if input_file:
		#input_file_df = pd.read_csv(input_file)
		df_json = json.dumps(csv.to_json(orient='records'))
	sampfreq1 = float(request.POST.get("sampfreq"))
	input_file_json = json.loads(df_json)
	df_in_first_api = pd.read_json(input_file_json)
			
	amplitude = df_in_first_api[ampindex]
	
	rawdata={"amplitude":amplitude.tolist()}
			
		
	## API call with payload
	
	url = api_url + "test/"
	payload = {"input_file":df_json,"frequency":sampfreq1,"modelno":modelno,"rpm":rpm,"nb":"null","inner":"null",
															"outer":"null","bd":"null","angle":"null"}
	if inner!="":
		
		payload = {"input_file":df_json,"frequency":sampfreq1,"modelno":modelno,"rpm":rpm,"nb":nb,
							"inner":inner,"outer":outer,"bd":bd,"angle":angle}
	
	url_response = requests.post(url, data = payload)
	
	fftdata1=url_response.json()
	
	fftdata3={"Frequencies":fftdata1['Frequencies'],"Amplitude":fftdata1['Amplitude']}
	#print(fftdata1['Frequencies'])
	#print(fftdata1)
	request.session['BPFO'] = fftdata1['BPFO']
	request.session['BPFI']= fftdata1['BPFI']
	request.session['BSF']= fftdata1['BSF']
	request.session['FTF']= fftdata1['FTF']
	request.session['fbpfo'] = fftdata1['FBPFO']
	request.session['fbpfi'] = fftdata1['FBPFI']
	request.session['fbsf'] = fftdata1['FBSF']
	request.session['fftf'] = fftdata1['FFTF']
	#messages.error(request,"fft plotted")
	if fftdata1['FBPFO'] != "null":
		return render(request, "csvapp/fftpeakdetection.html", {"fftdata":fftdata3,"rawdata":rawdata})
	else:
		return render(request, "csvapp/fftdata.html", {"fftdata":fftdata3,"rawdata":rawdata})

	
        #return render (request, 'visual/index.html', {"something": True, "frequency": frequencies, "amplitude" : amplitude }, {'data':uri})
	# except Exception as e:
	# 	logging.getLogger("error_logger").error("Unable to upload file. "+repr(e))
	# 	messages.error(request,"Unable to upload file. "+repr(e))

	#return HttpResponseRedirect(reverse("csvapp:upload")) 
	#return render(request, "csvapp/upload.html", data1)


def fftdata(request):
	if request.method == "GET":
	#return HttpResponse()
		print("get fftdata")

		return render(request, "csvapp/fftdata.html")
    #return render('template:index.html', {})
 
	if request.method == "POST":
	#return HttpResponse()
		
		return render(request, "csvapp/fftdata.html")
    #return render('template:index.html', {})
 

def downloadcsv(request):
	if request.method == "GET":
		return render(request, "csvapp/upload.html")
	if request.method == "POST":
		fftdata=request.session.get('fftdata')
		
		# df = pd.DataFrame(fftdata)
		# df.to_csv("F:\\ddrive\\Pranitha\\ConditionMonitoring\\fft.csv")
		
		# df = pd.DataFrame(fftdata,index=None)
		# df.to_csv('./data/Download.csv', index=False)
		
 		
		response = HttpResponse(
      	content_type='text/csv',
       	headers={'Content-Disposition': 'attachment; filename="FFT.csv"'},
   )
   
		df = pd.DataFrame(fftdata,index=None)
		df.to_csv(response)
	
		
		
		

		return render(request, 'csvapp/upload.html', {'question': response})
		#return response
   		
		# return render(request, "csvapp/upload.html")


