from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render
from rest_framework import status
import requests
import json
import numpy as np
from rest_framework.views import APIView
from pymongo import MongoClient
from rest_framework.generics import CreateAPIView
from csvrestapi.serializers import ContactSerializer
import pandas as pd
from math import cos
from datetime import datetime, timedelta
from findpeaks import findpeaks
from django.conf import settings

dbname=settings.DATABASE

class ContactCreateAPI(CreateAPIView):
    serializer_class = ContactSerializer

class Home(TemplateView):
	template_name = "csvrestapi/apihome.html"


@api_view(['GET','POST'])
def index(request):
    if request.method == 'GET':
        csv_file=request.data
        return Response(data="hi",status=status.HTTP_200_OK)
    if request.method == 'POST':
        #serializer = SnippetSerializer(data=request.data)
        #csv_file = request.data.get("file")
        
        ## Access the inputfile from payload
        samplingfreq = float(request.data.get("frequency"))
        input_file_json = json.loads(request.data.get('input_file'))
        df_in_second_api = pd.read_json(input_file_json)
        col=list(df_in_second_api.columns)
        col1=list(df_in_second_api.columns)
       
        for i in range(len(col)):
	        col1[i] = col1[i].lower()
	        if col1[i] == "amplitude":
	        	ampindex= col[i]
        modelno = request.data.get('modelno')

        data1={"sampfreq":samplingfreq}

        # to calculate fft
        
        amplitude=df_in_second_api[ampindex]

        result = FFT(amplitude,samplingfreq)
        
        a=result['Frequencies'].tolist()
        b=result['Amplitude'].tolist()
        

        FFT_dict={"Frequencies":a,"Amplitude":b,"BPFO":"null","BPFI":"null","BSF":"null",
                "FTF":"null","FBPFO":"null","FBPFI":"null","FBSF":"null","FFTF":"null"}
        
        rpmval = request.data.get("rpm")
        inner = request.data.get("inner")
        ## If modelno is not null get the bearing frequencies from 
        ## database by passing modelno using mongoclient
        if modelno != "null":
            # print("insode modelno")
            mongo_client = MongoClient()
        
            mongo_client = MongoClient(dbname)
            db = mongo_client.test
            
            data=db.bearingfaults
            
            modellist=data.find({"ModelNo":modelno})
            #print("ModelNo:"+item["ModelNo"] +"BPFO:"+str(item["BPFO"]))
            print(modellist.count())
            for item in modellist:
                BPFOval = item["BPFO"]
                BPFIval = item["BPFI"]
                BSFval = item["BSF"]
                FTFval = item["FTF"]
            
                rpmval = request.data.get("rpm")
                rpm=float(rpmval)
                BPFO = BPFOval*rpm/60
                BPFI = BPFIval*rpm/60
                BSF = BSFval*rpm/60
                FTF = FTFval*rpm/60

        ## If modelno is null ,calculate faults by peakdetection algorithm
        ## by taking taking other dimensions 
        if modelno == "":
            if inner == "null":
            
                inner=""
            else:
            
                rpm=float(request.data.get("rpm"))           
                nb=int(request.data.get("nb"))
                inner=float(request.data.get("inner"))
                outer=float(request.data.get("outer"))
                bd=float(request.data.get("bd"))
                angle=float(request.data.get("angle"))
            if(inner!=""):
                print("inside inner")
                bearfreq=BearingFrequenies(rpm,nb,inner,outer,bd,angle)
                dffreq = pd.DataFrame(a ,columns=['Frequencies'])
                dfamp = pd.DataFrame(b,columns=['Amplitude'])
                dffreq.reset_index(drop=True, inplace=True)
                dfamp.reset_index(drop=True, inplace=True)
                df_freqamp = pd.concat([dffreq, dfamp],axis=1)
                freq_list = list()
                freq_list.append(bearfreq['BPFO'])
                freq_list.append(bearfreq['BPFI'])
                freq_list.append(bearfreq['BSF'])
                freq_list.append(bearfreq['FTF'])
                freq_dict={}
                names=['BPFO','BPFI','BSF','FTF']
                    
                for i in range(len(freq_list)):
                    all_freq=PEAKDETECTOR(df_freqamp,freq_list[i],4)
                    freq_dict[names[i]]=all_freq
                print(freq_dict)
                FFT_dict={"Frequencies":a,"Amplitude":b,"BPFO":bearfreq['BPFO'],"BPFI":bearfreq['BPFI'],"BSF":bearfreq['BSF'],"FTF":bearfreq['FTF'],"FBPFO":freq_dict['BPFO'],"FBPFI":freq_dict['BPFI'],"FBSF":freq_dict['BSF'],"FFTF":freq_dict['FTF']}
        else:
            dffreq = pd.DataFrame(a ,columns=['Frequencies'])
            dfamp = pd.DataFrame(b,columns=['Amplitude'])
            dffreq.reset_index(drop=True, inplace=True)
            dfamp.reset_index(drop=True, inplace=True)
            df_freqamp = pd.concat([dffreq, dfamp],axis=1)
            freq_list = list()
            freq_list.append(BPFO)
            freq_list.append(BPFI)
            freq_list.append(BSF)
            freq_list.append(FTF)
            freq_dict={}
            names=['BPFO','BPFI','BSF','FTF']
           
            for i in range(len(freq_list)):
                all_freq=PEAKDETECTOR(df_freqamp,freq_list[i],4)
                freq_dict[names[i]]=all_freq
            print(freq_dict)
            FFT_dict={"Frequencies":a,"Amplitude":b,"BPFO":BPFO,"BPFI":BPFI,"BSF":BSF,"FTF":FTF,"FBPFO":freq_dict['BPFO'],"FBPFI":freq_dict['BPFI'],"FBSF":freq_dict['BSF'],"FFTF":freq_dict['FTF']}
        
        ## JSONResult
        return JsonResponse(FFT_dict)
        #return HttpResponse(json.dumps(FFTZip))
        #return Response(data={responsedata},status=status.HTTP_200_OK)


@api_view(['GET','POST'])
def upload_csv(request):
    if request.method == 'GET':
        csv_file=request.data
        return Response(data="hi",status=status.HTTP_200_OK)
    if request.method == 'POST':
        #serializer = SnippetSerializer(data=request.data)
        #csv_file = request.data.get("file")
        
        ## Access the input file from the payload
        input_file_json = json.loads(request.data.get('input_file'))
        
        
        df_in_second_api = pd.read_json(input_file_json)
        col=list(df_in_second_api.columns)
        col1=list(df_in_second_api.columns)
       
        modelno=request.data.get('modelno')
        noofcol = int(request.data.get('noofcol'))

        ## drop the null data from the each raw
        dropnullrowsdf = df_in_second_api.dropna()
       
       ## if noofcol is 3 calculate the time difference of From and To and store 
       ## in another column to get total time
        if noofcol == 3:
            timevalues = dropnullrowsdf['From']
       
            dropnullrowsdf['To Time'] = dropnullrowsdf['From'].shift(-1).where(dropnullrowsdf['From'].shift()!='')
        
            timevalues.index = range(len(timevalues))
            dropnullrowsdf.index = range(len(dropnullrowsdf))
            dropnullrowsdf['To Time'][-1] = 0
            for i in range(len(timevalues)-1):
                fromtime1 = dropnullrowsdf['From'][i]
                fromtime2 = dropnullrowsdf['To Time'][i]
                fromt1 = datetime.strptime(fromtime1, "%Y-%m-%d %H:%M:%S")
                fromt2=datetime.strptime(fromtime2, "%Y-%m-%d %H:%M:%S")
                
                ms1 = fromt1.timestamp() * 1000
                
                ms2=fromt2.timestamp() * 1000
                
                maindiff = ms2-ms1
                
                timevalues[i] = maindiff
                
                dropnullrowsdf['From'][i] = timevalues[i]
            timevalues.iloc[-1]=0
            
            time=dropnullrowsdf['From']
            amplitude=dropnullrowsdf['Total Acceleration avg']
            num1 = time.sum()

            ## If noofcol is 2 store the amplitude and time values
        if noofcol == 2:
            for i in range(len(col)):
	            col1[i] = col1[i].lower()
	            if col1[i] == "amplitude":
	                ampindex= col[i]
	            if col1[i] == "time":
		            timeindex=col[i]
		
            time=dropnullrowsdf[timeindex]
            amplitude=dropnullrowsdf[ampindex]
            num1=time.iloc[-1] - time.iloc[0]


        ## Calculate sampling frequency
        val = len(time)
        num = num1
        sf = (val/num)*1000
        samplingFrequency = sf
        
        

        
        ## Calculate FFT
        result = FFT(amplitude,samplingFrequency)
        
        ## Store Frequencies and amplitude
        a=result['Frequencies'].tolist()
        b=result['Amplitude'].tolist()
        FFT_dict={"Frequencies":a,"Amplitude":b,"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}

        rpmval = request.data.get("rpm")
        innerval = request.data.get("inner")
        ## If modelno is not null get fault frequencies 
        ## from database
        if modelno != "null":
            # print("insode modelno")
            mongo_client = MongoClient()
            mongo_client = MongoClient(dbname)
            db = mongo_client.test
            data=db.bearingfaults
            modellist=data.find({"ModelNo":modelno})
            
            for item in modellist:
                BPFOval = item["BPFO"]
                BPFIval = item["BPFI"]
                BSFval = item["BSF"]
                FTFval = item["FTF"]
        
                rpm=float(rpmval)
                BPFO = BPFOval*rpm/60
                BPFI = BPFIval*rpm/60
                BSF = BSFval*rpm/60
                FTF = FTFval*rpm/60
        ## if modelno is null take other dimentions and calculate bearing frequencies
        if modelno == "":
            if innerval == "null":
            
                inner=""
            else:
            
                rpm=float(request.data.get("rpm"))
        
            
                nb=int(request.data.get("nb"))
                inner=float(request.data.get("inner"))
                outer=float(request.data.get("outer"))
                bd=float(request.data.get("bd"))
                angle=float(request.data.get("angle"))
            if(inner!=""):
            
                bearfreq=BearingFrequenies(rpm,nb,inner,outer,bd,angle)
                FFT_dict={"Frequencies":a,"Amplitude":b,"BPFO":bearfreq['BPFO'],"BPFI":bearfreq['BPFI'],"BSF":bearfreq['BSF'],"FTF":bearfreq['FTF']}

            #FFT_dict={"Frequencies":a,"Amplitude":b,"BPFO":BPFO,"BPFI":BPFI,"BSF":BSF,"FTF":FTF}

        #FFT_dict={"Frequencies":frequencies,"Amplitude":abs(fourierTransform)}
        # FFTZip = dict(zip(frequencies,abs(fourierTransform)))
        # print(FFTZip)
        else:
                
            FFT_dict={"Frequencies":a,"Amplitude":b,"BPFO":BPFO,"BPFI":BPFI,"BSF":BSF,"FTF":FTF}


        ## return JSONResult
        return JsonResponse(FFT_dict)
        #return HttpResponse(json.dumps(FFTZip))
        #return Response(data={responsedata},status=status.HTTP_200_OK)


@api_view(['GET','POST'])
def testapi(request):
    if request.method == 'POST':
        textstring = request.data.get('sample')
        dict={"teststring":textstring}
        return JsonResponse(dict)

## FFT Function

def FFT(x ,Sfreq):
    
   # Calculate frequencies
    xCount = len(x)
    values = np.arange(int(xCount / 2))
    timePeriod = xCount / Sfreq
    frequencies = values / timePeriod
    # Frequency domain representation
    # Normalize amplitude
    fourierTransform = np.fft.fft(x) / xCount
    # Exclude sampling frequency
    fourierTransform = fourierTransform[range(int(len(x) / 2))]
    
    #return dict(zip(frequencies,abs(fourierTransform))) ----if needed in form {freq1:fft1,freq2:ff2.....}
    return {'Frequencies': frequencies ,'Amplitude': abs(fourierTransform)}


## TO calculate bearing frequencies

def BearingFrequenies(rpm,N,Inner,Outer,Bd,angle=0):
   # Convert RPM into Hz 
   fundamental = (rpm/60) 
   # Calculate Pitch Diameter
   Pd = (Inner + Outer) / 2
   # Calculate Cosine of contact angle
   cosine = cos(angle*np.pi/180)
   # Calculate BPFO , BPFI ,BSF ,FTF
   BPFO = (fundamental * N/2) *(1 -(Bd * cosine/Pd))
   BPFI = (fundamental * N/2) *(1 +(Bd * cosine/Pd))
   BSF = (fundamental * Pd/Bd) *(1 -(Bd * cosine/Pd)**2)
   FTF = (fundamental/2) *(1 -(Bd * cosine/Pd))
   
   return {'BPFO': BPFO ,'BPFI': BPFI ,'BSF': BSF ,'FTF': FTF}




def PEAKDETECTOR(array, freq, N):

    freq_list = [i * freq for i in range(1, N + 1)]

   
    
    detected_freq = list()
    
    
    for expected_freq in freq_list:
        
        x = array.query('Frequencies>@expected_freq-5 & Frequencies<@expected_freq+5')
        
        fp = findpeaks(method='topology', lookahead=1, verbose=0)
        
        results = fp.fit(x['Amplitude'])
        
        peak_amp = list(results['df'].query('peak==True')['y'])
        peak_amp = max(peak_amp)
        peak_freq = list(array.query('Amplitude=={}'.format(peak_amp))['Frequencies'])[0]
        detected_freq.append(peak_freq)

    return detected_freq
