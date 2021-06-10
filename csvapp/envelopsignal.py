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
from csvapp.forms import csvwithouttime

# api_url = "http://127.0.0.1:8000/csvrestapi/"

api_url ="https://cbmapiteal.azurewebsites.net/csvrestapi/"

def envelop_index(request):
	if request.method == "POST":	
        	print("do ntng")

	return render(request, "csvapp/envelop.html")


 
def envelop_upload_csv(request):
    
	data = {}
   
	if "GET" == request.method:
       
		return render(request, "csvapp/envelop.html", data)
	if "POST" == request.method:
		
		csv_file = request.FILES['file1']
		
		print("inside")

		if csv_file.name.endswith(".csv") != True:
			messages.error(request,'File is not CSV type')
			
			return render(request, "csvapp/envelop.html", data)
       
		## 	Read the csv file using pandas data frame and check for the columns accordingly
		csv=pd.read_csv(csv_file,error_bad_lines=False)
		col=csv.columns.tolist()
		col1=csv.columns.tolist()
		n=len(col)
		noofcol=2
		for i in range(len(col)):
			col1[i] = col1[i].lower()
			if col1[i] == "amplitude":
				ampindex= col[i]
			if col1[i] == "time":
				timeindex=col[i]
		iucolnames=['From','To']
		colnames=['amplitude','time']
		if n < 2:
			messages.error(request,'No columns to parse')			
			return render(request, "csvapp/envelop.html", data)
		##  If the column contains From and To the uploaded file is IU generated file,set the nofocol as 3
		if n !=2: 
			for word in iucolnames:
				if not word in col:
					print("no columns")
					messages.error(request,'Upload correct IU generated csv file')
					return render(request, "csvapp/envelop.html", data)	
			noofcol=3
			if col[2] == 'From' and col[3]=='To':
			
				noofcol = 3		
			else:
				messages.error(request,'Upload correct IU generated csv file ...[From],[To]')
				return render(request, "csvapp/envelop.html", data)
		##  If the column contains Amplitude and time ,set the noofcol as 2
		if n>0 and noofcol==2:
			for word in colnames:
				
				if not word in col1:
					print("no columns")
					messages.error(request,'Upload correct csv file......[amplitude],[time]')
					return render(request, "csvapp/envelop.html", data)
			
			# if col[0] != "time" and col[1] != "amplitude" or col[1] != "time" and col[0] != "amplitude":
			# 	messages.error(request,'File column names mismatch')			
			# 	return render(request, "csvapp/envelop.html", data)
		
		#try:
		
		## 	Convert csv file json object to string and 
		## store the rawdata to plot the graph
		input_file1 = request.FILES.get(u'file1')
		if input_file1:
			#input_file_df1 = pd.read_csv(input_file1)
			df_json1 = json.dumps(csv.to_json(orient='records'))
		input_file_json = json.loads(df_json1)
		df_in_first_api = pd.read_json(input_file_json)
		##  Store raw data to plot the graph
		if noofcol==3:
			
			
			amplitude=df_in_first_api['Total Acceleration avg']
			time=df_in_first_api['From']
			rawdata={"amplitude":amplitude.tolist(),"time":time.tolist()}
			
			#print(df_in_first_api)
		else:
			
			amplitude = df_in_first_api[ampindex]
			time=df_in_first_api[timeindex]
			rawdata={"amplitude":amplitude.tolist(),"time":time.tolist()}
		
			#print(df_in_first_api)

		## get the remaining parameters
		algo=request.POST.get("algo")
		modelnoval=request.POST.get("modelno")
		rpmval=request.POST.get("rpm")
		nval=request.POST.get("n")
		innerval=request.POST.get("inner")
		outerval=request.POST.get("outer")
		bdval=request.POST.get("bd")
		angleval=request.POST.get("angle")
		f1=0.5
		f2=0.75
		numtaps=51
		rpm = float(rpmval)
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

		url = api_url + "envelop_upload_csv/"
		payload = {"noofcol":noofcol,"input_file":df_json1,"algo":algo,"f1":json.dumps(f1),
		"f2":json.dumps(f2),"numtaps":json.dumps(numtaps),"modelno":modelno,"rpm":rpm,
		"nb":"null","inner":"null","outer":"null","bd":"null","angle":"null"}
		
		if inner!="":
		
			payload = {"noofcol":noofcol,"input_file":df_json1,"algo":algo,"f1":json.dumps(f1),
			"f2":json.dumps(f2),"numtaps":json.dumps(numtaps),"modelno":modelno,"rpm":rpm,"nb":nb,
			"inner":inner,"outer":outer,"bd":bd,"angle":angle}
	
		
		url_response = requests.post(url, data = payload)

		## store the json result
		envelopdata1=url_response.json()
		envelopdata3 = {"Frequency":envelopdata1['Frequency'],"Amplitude":envelopdata1['Amplitude']}
		envelopingdata = {"Frequency":envelopdata1['EnvHilbertFreq'],"Amplitude":envelopdata1['EnvHilbertAmp']}
		
		request.session['BPFO'] = envelopdata1['BPFO']
		request.session['BPFI']= envelopdata1['BPFI']
		request.session['BSF']= envelopdata1['BSF']
		request.session['FTF']= envelopdata1['FTF']
		request.session['fbpfo'] = envelopdata1['FBPFO']
		request.session['fbpfi'] = envelopdata1['FBPFI']
		request.session['fbsf'] = envelopdata1['FBSF']
		request.session['fftf'] = envelopdata1['FFTF']
		
		request.session['faultsmsg']= envelopdata1['faults_msg']
		if envelopdata1['faults_msg'] == "nofaults":
			request.session['faultsmsg'] = 0
	
		if envelopdata1['faults_msg'] == "faults cannot be detected":
			request.session['faultsmsg'] = 1
		if envelopdata1['faults_msg'] == "faults":
			request.session['faultsmsg'] = 2
		## Return the data to envelopdata template
		if envelopdata1['FBPFO'] != "null":
			freqlist=envelopdata1['fault_status']
	
			freqlist1=list(freqlist.keys())
	
			for i in range(len(freqlist1)):
				if freqlist1[i] == "BPFI":
					freqlist1[i] = "Inner fault detected"
				if freqlist1[i] == "BPFO":
					freqlist1[i] = "Outer fault detected"
				if freqlist1[i] == "BSF":
					freqlist1[i] = "Ball fault detected"
				if freqlist1[i] == "FTF":
					freqlist1[i] = "Cage fault detected"
			return render(request, "csvapp/enveloppeakdetection.html", {"envelopdata":envelopdata3,"enveloping":envelopingdata,'rawdata':rawdata,'fault_list':freqlist1})			
	
		else:
			return render(request, "csvapp/envelopdata.html", {"envelopdata":envelopdata3,"enveloping":envelopingdata,'rawdata':rawdata})			
		# except Exception as e:
		# 	logging.getLogger("error_logger").error("Unable to upload file. "+repr(e))
		# 	messages.error(request,"Unable to upload file. "+repr(e))


		
		#return HttpResponseRedirect(reverse("csvapp:upload")) 
		#return render(request, "csvapp/upload.html", data)

def envelop_upload_csv_nobfc(request):
    
	data = {}
   
	if "GET" == request.method:
       
		return render(request, "csvapp/envelop.html", data)
	if "POST" == request.method:
		
		csv_file = request.FILES['file1']
		
		

		if csv_file.name.endswith(".csv") != True:
			messages.error(request,'File is not CSV type')
			
			return render(request, "csvapp/envelop.html", data)
       

		csv=pd.read_csv(csv_file,error_bad_lines=False)
		col=csv.columns.tolist()
		n=len(col)
		noofcol=2
		
		if n == 0:
			messages.error(request,'No columns to parse')			
			return render(request, "csvapp/upload.html", data)
		if n != 2: 
			if col[2] == 'From' and col[3]=='To':
				noofcol = 3
				print("inside 3")
				csv.drop('Machine',inplace=True, axis=1)
				csv.drop('Monitor',inplace=True, axis=1)
				
			else:
				messages.error(request,'Upload correct IU generated csv file')
				return render(request, "csvapp/upload.html", data)
		if n==2:
			if col[0] != 'time' or col[1] != 'amplitude':
				messages.error(request,'File column names mismatch')			
				return render(request, "csvapp/upload.html", data)

		#try:
		
		input_file1 = request.FILES.get(u'file1')
		if input_file1:
			#input_file_df1 = pd.read_csv(input_file1)
			df_json1 = json.dumps(csv.to_json(orient='records'))
		
		
		algo=request.POST.get("algo")
		modelnoval=request.POST.get("modelno")
		modelno=modelnoval
		f1=0.5
		f2=0.75
		numtaps=51
		
		

		url = api_url + "envelop_upload_csv_nobfc/"
		payload = {"noofcol":noofcol,"input_file":df_json1,"algo":algo,"f1":json.dumps(f1),"f2":json.dumps(f2),"numtaps":json.dumps(numtaps),"modelno":modelno}
		
		
		
		url_response = requests.post(url, data = payload)
		envelopdata1=url_response.json()
		envelopdata3 = {"Frequency":envelopdata1['Frequency'],"Amplitude":envelopdata1['Amplitude']}
		envelopingdata = {"Frequency":envelopdata1['EnvHilbertFreq'],"Amplitude":envelopdata1['EnvHilbertAmp']}
		
		#envelopdata3={"EnvSignalHilbert":envelopdata1['EnvSignalHilbert'],"EnvSignalHilbertFFT":envelopdata1['EnvSignalHilbertFFT']}
	
		request.session['BPFO'] = envelopdata1['BPFO']
		request.session['BPFI']= envelopdata1['BPFI']
		request.session['BSF']= envelopdata1['BSF']
		request.session['FTF']= envelopdata1['FTF']
		
		return render(request, "csvapp/envelopdata.html", {"envelopdata":envelopdata3,"enveloping":envelopingdata})			
		
		
		#return HttpResponseRedirect(reverse("csvapp:upload")) 
		#return render(request, "csvapp/upload.html", data)


def envelop_upload_withouttime(request):
	data1 ={}
	if "GET" == request.method :
		
        
		return render(request, "csvapp/envelop.html", data1)

    # if not GET, then proceed
	#try:	
	data1={}
	CSVData = csvwithouttime(request.POST,request.FILES)
		
	## Access the input file from the payload	
	csv_file = request.FILES['file1']
		
	sampfreq1 = request.POST.get("sampfreq")
	algo=request.POST.get("algo")

	## Store the other parameters
	modelnoval=request.POST.get("modelno")
	rpmval=request.POST.get("rpm")
	nval=request.POST.get("n")
	innerval=request.POST.get("inner")
	outerval=request.POST.get("outer")
	bdval=request.POST.get("bd")
	angleval=request.POST.get("angle")
	f1=0.5
	f2=0.75
	numtaps=51
	rpm = float(rpmval)
	print(innerval)
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
		
	
	
	#check if csv file or not
	if not csv_file.name.endswith('.csv'):
		print("not ending with .csv")
		messages.error(request,'File is not CSV type')
			
		return render(request, "csvapp/envelop.html", data1)

	## 	Read the csv file using pandas dataframe and check for the columns accordingly
	csv=pd.read_csv(csv_file,error_bad_lines=False) 
	col=csv.columns.tolist()
	
	col1=csv.columns.tolist()
	for i in range(len(col)):
		col1[i] = col1[i].lower()
		if col1[i] == "amplitude":
			ampindex= col[i]
	n = len(col)
	colnames=['amplitude']
	if n == 0:
		messages.error(request,'No columns to parse')			
		return render(request, "csvapp/envelop.html", data1)
		
	if n>0:
		for word in colnames:
			print(word)
			if not word in col1:
				print("no columns")
				messages.error(request,'Upload correct csv file...[amplitude]')
				return render(request, "csvapp/envelop.html", data1)
		

	
	## 	Convert csv file json object to string and 
	## store the rawdata to plot the graph

	input_file = request.FILES.get(u'file1')
	if input_file:
		#input_file_df = pd.read_csv(input_file)
		df_json = json.dumps(csv.to_json(orient='records'))
	sampfreq1 = float(request.POST.get("sampfreq"))
	input_file_json = json.loads(df_json)
	df_in_first_api = pd.read_json(input_file_json)
			
	amplitude = df_in_first_api[ampindex]
	
	rawdata={"amplitude":amplitude.tolist()}
			
		


	## API call URL with payload

	url = api_url + "envelop_upload_withouttime/"
	payload = {"input_file":df_json,"frequency":sampfreq1,"algo":algo,"f1":json.dumps(f1),
	"f2":json.dumps(f2),"numtaps":json.dumps(numtaps),"modelno":modelno,"rpm":rpm,"nb":"null",
	"inner":"null","outer":"null","bd":"null","angle":"null"}
	
	if inner!="":
		
		payload = {"input_file":df_json,"frequency":sampfreq1,"algo":algo,"f1":json.dumps(f1),
		"f2":json.dumps(f2),"numtaps":json.dumps(numtaps),"modelno":modelno,"rpm":rpm,"nb":nb,
		"inner":inner,"outer":outer,"bd":bd,"angle":angle}
	
	url_response = requests.post(url, data = payload)
	## Store the jsonresult
	envelopdata1=url_response.json()
	
	envelopdata3={"Frequencies":envelopdata1['Frequency'],"Amplitude":envelopdata1['Amplitude']}
	envelopingdata={"Frequencies":"null","Amplitude":envelopdata1['EnvHilbertAmp']}
	
	## Store the faults in sessions
	
	request.session['fbpfo'] = envelopdata1['FBPFO']
	request.session['fbpfi'] = envelopdata1['FBPFI']
	request.session['fbsf'] = envelopdata1['FBSF']
	request.session['fftf'] = envelopdata1['FFTF']
	request.session['BPFO'] = envelopdata1['BPFO']
	request.session['BPFI']= envelopdata1['BPFI']
	request.session['BSF']= envelopdata1['BSF']
	request.session['FTF']= envelopdata1['FTF']
	
	
	
	request.session['faultsmsg']= envelopdata1['faults_msg']
	if envelopdata1['faults_msg'] == "nofaults":
		request.session['faultsmsg'] = 0
	
	if envelopdata1['faults_msg'] == "faults cannot be detected":
		request.session['faultsmsg'] = 1
	if envelopdata1['faults_msg'] == "faults":
		request.session['faultsmsg'] = 2
	## Return data to envelopdata.html/enveloppeakdetection.html
	if envelopdata1['FBPFO'] != "null":
		freqlist=envelopdata1['fault_status']
	
		freqlist1=list(freqlist.keys())
	
		for i in range(len(freqlist1)):
			if freqlist1[i] == "BPFI":
				freqlist1[i] = "Inner fault detected"
			if freqlist1[i] == "BPFO":
				freqlist1[i] = "Outer fault detected"
			if freqlist1[i] == "BSF":
				freqlist1[i] = "Ball fault detected"
			if freqlist1[i] == "FTF":
				freqlist1[i] = "Cage fault detected"

		return render(request, "csvapp/enveloppeakdetection.html", {"envelopdata":envelopdata3,"enveloping":envelopingdata,"rawdata":rawdata,"fault_list":freqlist1})
	else:
		return render(request, "csvapp/envelopdata.html", {"envelopdata":envelopdata3,"enveloping":envelopingdata,"rawdata":rawdata})

        #return render (request, 'visual/index.html', {"something": True, "frequency": frequencies, "amplitude" : amplitude }, {'data':uri})
	# except Exception as e:
	# 	logging.getLogger("error_logger").error("Unable to upload file. "+repr(e))
	# 	messages.error(request,"Unable to upload file. "+repr(e))

	#return HttpResponseRedirect(reverse("csvapp:upload")) 
	#return render(request, "csvapp/upload.html", data1)



def envelop_upload_withouttimenobfc(request):
	data1 ={}
	if "GET" == request.method :
		
        
		return render(request, "csvapp/envelop.html", data1)

    # if not GET, then proceed
	#try:	
	data1={}
	CSVData = csvwithouttime(request.POST,request.FILES)
		
		
	csv_file = request.FILES['file1']
		
	sampfreq1 = request.POST.get("sampfreq")
	algo=request.POST.get("algo")
	
	
	
	f1=0.5
	f2=0.75
	numtaps=51
	
	
	
	#check if csv file or not
	if not csv_file.name.endswith('.csv'):
		print("not ending with .csv")
		messages.error(request,'File is not CSV type')
			
		return render(request, "csvapp/envelop.html", data1)
	csv=pd.read_csv(csv_file,error_bad_lines=False) 
	col=csv.columns.tolist()
		
	n = len(col)

	if n == 0:
		messages.error(request,'No columns to parse')			
		return render(request, "csvapp/envelop.html", data1)
		
	if n != 1:
		messages.error(request,'File has more than 1 column')			
		return render(request, "csvapp/envelop.html", data1)

	if col[0] != 'amplitude':
		messages.error(request,'File column names mismatch')			
		return render(request, "csvapp/envelop.html", data1)


	input_file = request.FILES.get(u'file1')
	if input_file:
		#input_file_df = pd.read_csv(input_file)
		df_json = json.dumps(csv.to_json(orient='records'))
	sampfreq1 = float(request.POST.get("sampfreq"))

	
	url = api_url + "envelop_upload_withouttimenobfc/"
	payload = {"input_file":df_json,"frequency":sampfreq1,"algo":algo,"f1":json.dumps(f1),"f2":json.dumps(f2),"numtaps":json.dumps(numtaps)}
	
	
	url_response = requests.post(url, data = payload)
	envelopdata1=url_response.json()
	envelopdata2 = json.dumps(envelopdata1)
	envelopdata3={"Frequencies":envelopdata1['Frequency'],"Amplitude":envelopdata1['Amplitude']}
	envelopingdata={"Frequencies":"null","Amplitude":envelopdata1['EnvHilbertAmp']}
	#print(fftdata1['Frequencies'])
	#print(fftdata1)
	request.session['BPFO'] = envelopdata1['BPFO']
	request.session['BPFI']= envelopdata1['BPFI']
	request.session['BSF']= envelopdata1['BSF']
	request.session['FTF']= envelopdata1['FTF']
	
	#messages.error(request,"fft plotted")
	
	return render(request, "csvapp/envelopdata.html", {"envelopdata":envelopdata3,"enveloping":envelopingdata})

        #return render (request, 'visual/index.html', {"something": True, "frequency": frequencies, "amplitude" : amplitude }, {'data':uri})
	# except Exception as e:
	# 	logging.getLogger("error_logger").error("Unable to upload file. "+repr(e))
	# 	messages.error(request,"Unable to upload file. "+repr(e))

	#return HttpResponseRedirect(reverse("csvapp:upload")) 
	#return render(request, "csvapp/upload.html", data1)



def getmodelno(request):
	if request.method == 'POST':
		print("inside get csvapp model no")
		url = api_url + "getmodelno/"
		url_response = requests.post(url)
		envelopdata1=url_response.json()	
		print(envelopdata1)

	if request.method == 'GET':
		print("inside get csvapp model no")
		url = api_url + "getmodelno/"
		url_response = requests.post(url)
		envelopdata1=url_response.json()	
		print(envelopdata1)