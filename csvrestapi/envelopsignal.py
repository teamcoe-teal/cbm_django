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
#from snippets.models import Snippet
#from snippets.serializers import SnippetSerializer
# Create your views here.
from rest_framework.generics import CreateAPIView
from csvrestapi.serializers import ContactSerializer
import pandas as pd
from math import cos,pi,e
from datetime import datetime
import numpy
from scipy.signal import hilbert
from scipy.signal import firwin
from scipy.signal import convolve2d
import warnings
warnings.filterwarnings("ignore")
#from pymongo import MongoClient
from findpeaks import findpeaks
from django.conf import settings
from sklearn.ensemble import IsolationForest

mongo_url="mongodb://127.0.0.1:27017"
dbname=settings.DATABASE


@api_view(['GET','POST'])
def envelop_upload_csv(request):
    if request.method == 'GET':
        csv_file=request.data
        return Response(data="hi",status=status.HTTP_200_OK)
    if request.method == 'POST':
        #serializer = SnippetSerializer(data=request.data)
        #csv_file = request.data.get("file")
        
        ##  Access the input file from the payload
        input_file_json = json.loads(request.data.get('input_file'))
        df_in_second_api = pd.read_json(input_file_json)
        
        col=list(df_in_second_api.columns)
        col1=list(df_in_second_api.columns)
       
        algo=request.data.get('algo')
        f1=request.data.get('f1')
        f2=request.data.get('f2')
        numtaps=request.data.get('numtaps')
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
                
                ms1 = fromt1.timestamp() *1
                
                ms2=fromt2.timestamp() * 1
                
                maindiff = ms2-ms1
                
                timevalues[i] = maindiff
                
                dropnullrowsdf['From'][i] = timevalues[i]
            timevalues.iloc[-1]=0
            
            time=dropnullrowsdf['From']
            amplitude=dropnullrowsdf['Total Acceleration avg']
           
            num1=time.sum()

        ## If noofcol is 2 store the amplitude and time values   
        if noofcol == 2:
            for i in range(len(col)):
	            col1[i] = col1[i].lower()
	            if col1[i] == "amplitude":
	                ampindex= col[i]
	            if col1[i] == "time":
		            timeindex=col[i]
		
            time=df_in_second_api[timeindex]
            amplitude=df_in_second_api[ampindex]
            num1 = time.iloc[-1] - time.iloc[0]
        # to calculate fft
        
        ## Calculate sampling frequency
        val = len(time)
        
        num = num1
        
        sf = (val/num)*1
        Sfreq = sf
        
       
        x=amplitude
        y=time
        Freq = abs(y)

        ## If modelno is not null get fault frequencies 
        ## from database
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

            

        #filterresult = FILTER(x,Sfreq,f1,f2,numtaps)
        
        ## if algorithm selected is hilbert Transform,calculate the envelope signal and FFT of the envelope
        if algo == "hilbtrans":
            
            # For enveloping using hilbert transform          
            Env_x = abs(hilbert(FILTER(x,Sfreq,f1,f2,numtaps)))
            Env_x_rounded = np.round(Env_x,4)
            Env_dc = (Env_x_rounded  - np.mean(Env_x_rounded)).squeeze()
            
            FFT_dc = FFT(Env_dc,Sfreq)
            

            Envelope_dict={"EnvHilbertFreq":Freq.tolist(),"EnvHilbertAmp":abs(Env_dc).tolist(),
            "Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),
            "BPFO":"null","BPFI":"null","BSF":"null","FTF":"null","FBPFO":"null","FBPFI":"null",
            "FBSF":"null","FFTF":"null"}
            
            #Envelope_dict={"EnvSignalHilbert":Env_dc,"EnvSignalHilbertFFT":FFT(Env_dc,Sfreq),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
            rpmval = request.data.get("rpm")
            innerval = request.data.get("inner")
            ## if modelno is null take other dimentions and calculate bearing
            #  faults using peakdetection algorithm
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
                    dffreq = pd.DataFrame(FFT_dc['Frequencies'] ,columns=['Frequencies'])
                    dfamp = pd.DataFrame(FFT_dc['Amplitude'],columns=['Amplitude'])
                    dffreq.reset_index(drop=True, inplace=True)
                    dfamp.reset_index(drop=True, inplace=True)
                    df_freqamp = pd.concat([dffreq, dfamp],axis=1)
                    print(df_freqamp)
                    freq_list = list()
                    freq_list.append(bearfreq['BPFO'])
                    freq_list.append(bearfreq['BPFI'])
                    freq_list.append(bearfreq['BSF'])
                    freq_list.append(bearfreq['FTF'])
                    freq_dict={}
                    names=['BPFO','BPFI','BSF','FTF'] 
                    freq_dict1=FaultDectector(df_freqamp,freq_list)
                    Envelope_dict={"EnvHilbertFreq":Freq.tolist(),"EnvHilbertAmp":abs(Env_dc).tolist(),
                    "Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),
                    "BPFO":"null","BPFI":"null","BSF":"null","FTF":"null","FBPFO":freq_dict1['BPFO'],
                    "FBPFI":freq_dict1['BPFI'],"FBSF":freq_dict1['BSF'],"FFTF":freq_dict1['FTF']}
                    
                    #Envelope_dict={"EnvHilbertFreq":Freq.tolist(),"EnvHilbertAmp":abs(Env_dc).tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":bearfreq['BPFO'],"BPFI":bearfreq['BPFI'],"BSF":bearfreq['BSF'],"FTF":bearfreq['FTF']}
                
                #Envelope_dict={"EnvSignalHilbert":Env_dc,"EnvSignalHilbertFFT":FFT(Env_dc,Sfreq),"BPFO":BPFO,"BPFI":BPFI,"BSF":BSF,"FTF":FTF}
                #Envelope_dict={"EnvSignalHilbertFFT":FFT(Env_dc,Sfreq),"BPFO":BPFO,"BPFI":BPFI,"BSF":BSF,"FTF":FTF}
            else:
                dffreq = pd.DataFrame(FFT_dc['Frequencies'] ,columns=['Frequencies'])
                dfamp = pd.DataFrame(FFT_dc['Amplitude'],columns=['Amplitude'])
                dffreq.reset_index(drop=True, inplace=True)
                dfamp.reset_index(drop=True, inplace=True)
                df_freqamp = pd.concat([dffreq, dfamp],axis=1)
                print(df_freqamp)
                freq_list = list()
                freq_list.append(BPFO)
                freq_list.append(BPFI)
                freq_list.append(BSF)
                freq_list.append(FTF)
                freq_dict={}
                names=['BPFO','BPFI','BSF','FTF']
                
                freq_dict1=FaultDectector(df_freqamp,freq_list)
                print(freq_dict1)
                Envelope_dict={"EnvHilbertFreq":Freq.tolist(),"EnvHilbertAmp":abs(Env_dc).tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null","FBPFO":freq_dict1['BPFO'],"FBPFI":freq_dict1['BPFI'],"FBSF":freq_dict1['BSF'],"FFTF":freq_dict1['FTF']}
                
                #Envelope_dict={"EnvHilbertFreq":Freq.tolist(),"EnvHilbertAmp":abs(Env_dc).tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":BPFO,"BPFI":BPFI,"BSF":BSF,"FTF":FTF}
                
        ## if algorithm is demodulation,calculate envelope signal 
        # using demodulation algorithm and FFT of it      
        else:
            Ba1 = Sfreq/4
            Ba2 = (3/8)*Sfreq
            f0 = (Ba2 + Ba1)/2
            t = 1 /Sfreq
            raw_x = x * e**(-2j*pi*f0*t)
            Demod_x = 2 * FILTER(raw_x,Sfreq,f1,f2,numtaps = 51)
            Demod_x_rounded = np.round(Demod_x,4)
            Demod_dc = (Demod_x_rounded  - np.mean( Demod_x_rounded)).squeeze()
            
            FFT_dc = FFT(Demod_dc,Sfreq)
            Freq = abs(y)
            Envelope_dict={"EnvHilbertFreq":Freq.tolist(),"EnvHilbertAmp":abs(Demod_dc).tolist(),
            "Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),
            "BPFO":"null","BPFI":"null","BSF":"null","FTF":"null","FBPFO":"null","FBPFI":"null",
            "FBSF":"null","FFTF":"null"}
                
            #Envelope_dict={"EnvSignalDemodulation":Demod_dc,"EnvSignalDemoduationFFT":FFT(Demod_dc,Sfreq),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
      
            rpmval = request.data.get("rpm")
            innerval = request.data.get("inner")
            
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
                    
                    Envelope_dict={"EnvHilbertFreq":Freq.tolist(),"EnvHilbertAmp":abs(Demod_dc).tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":bearfreq['BPFO'],"BPFI":bearfreq['BPFI'],"BSF":bearfreq['BSF'],"FTF":bearfreq['FTF'],"FBPFO":"null","FBPFI":"null","FBSF":"null","FFTF":"null"}
                
             
                    #Envelope_dict={"EnvSignalDemodulation":Demod_dc,"EnvSignalDemoduationFFT":FFT(Demod_dc,Sfreq),"BPFO":BPFO,"BPFI":BPFI,"BSF":BSF,"FTF":FTF}
            else:

                Envelope_dict={"EnvHilbertFreq":Freq.tolist(),"EnvHilbertAmp":abs(Demod_dc).tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":BPFO,"BPFI":BPFI,"BSF":BSF,"FTF":FTF,"FBPFO":"null","FBPFI":"null","FBSF":"null","FFTF":"null"}
                

        #FFT_dict={"Frequencies":frequencies,"Amplitude":abs(fourierTransform)}
        # FFTZip = dict(zip(frequencies,abs(fourierTransform)))
        # print(FFTZip)


        ## Return result as json
        return JsonResponse(Envelope_dict)
        #return HttpResponse(json.dumps(FFTZip))
        #return Response(data={responsedata},status=status.HTTP_200_OK)


@api_view(['GET','POST'])
def envelop_upload_csv_nobfc(request):
    if request.method == 'GET':
        csv_file=request.data
        return Response(data="hi",status=status.HTTP_200_OK)
    if request.method == 'POST':
        #serializer = SnippetSerializer(data=request.data)
        #csv_file = request.data.get("file")
        
        
      
        
        input_file_json = json.loads(request.data.get('input_file'))
        df_in_second_api = pd.read_json(input_file_json)
        
        algo=request.data.get('algo')
        f1=request.data.get('f1')
        f2=request.data.get('f2')
        numtaps=request.data.get('numtaps')
        modelno=request.data.get('modelno')
        noofcol = int(request.data.get('noofcol'))
        dropnullrowsdf = df_in_second_api.dropna()
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
            num1=time.sum()
        if noofcol == 2:
            time=df_in_second_api['time']
            amplitude=df_in_second_api['amplitude']
            num1 = time.iloc[-1] - time.iloc[0]
        # to calculate fft
        
        val = len(time)
        num = num1
        sf = (val/num)*1000
        Sfreq = sf
        
        
        x=amplitude
        y=time
        
        if algo == "hilbtrans":
            
            # For enveloping using hilbert transform          
            Env_x = abs(hilbert(FILTER(x,Sfreq,f1,f2,numtaps)))
            Env_x_rounded = np.round(Env_x,4)
            Env_dc = (Env_x_rounded  - np.mean(Env_x_rounded)).squeeze()
            FFT_dc = FFT(Env_dc,Sfreq)
            Freq = abs(y)
            #Envelope_dict={"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
            Envelope_dict={"EnvHilbertFreq":Freq.tolist(),"EnvHilbertAmp":Env_dc.tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
            #print(Envelope_dict)
            #Envelope_dict={"EnvSignalHilbert":Env_dc,"EnvSignalHilbertFFT":FFT(Env_dc,Sfreq),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
                
        else:
            Ba1 = Sfreq/4
            Ba2 = (3/8)*Sfreq
            f0 = (Ba2 + Ba1)/2
            t = 1 /Sfreq
            raw_x = x * e**(-2j*pi*f0*t)
            Demod_x = 2 * FILTER(raw_x,Sfreq,f1,f2,numtaps = 51)
            Demod_x_rounded = np.round(Demod_x,4)
            Demod_dc = (Demod_x_rounded  - np.mean( Demod_x_rounded)).squeeze()
            
            FFT_dc = FFT(Demod_dc,Sfreq)
            Freq = abs(y)
            Envelope_dict={"EnvHilbertFreq":Freq.tolist(),"EnvHilbertAmp":abs(Demod_dc).tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
            #print(Envelope_dict)"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
                
            #Envelope_dict={"EnvSignalDemodulation":Demod_dc,"EnvSignalDemoduationFFT":FFT(Demod_dc,Sfreq),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
      
            
       
        return JsonResponse(Envelope_dict)
        #return HttpResponse(json.dumps(FFTZip))
        #return Response(data={responsedata},status=status.HTTP_200_OK)



@api_view(['GET','POST'])
def envelop_upload_withouttime(request):
    if request.method == 'GET':
        csv_file=request.data
        return Response(data="hi",status=status.HTTP_200_OK)
    if request.method == 'POST':
        #serializer = SnippetSerializer(data=request.data)
        #csv_file = request.data.get("file")

        ## Access the inputfile from payload
        input_file_json = json.loads(request.data.get('input_file'))
        df_in_second_api = pd.read_json(input_file_json)
        col=list(df_in_second_api.columns)
        col1=list(df_in_second_api.columns)
       
        for i in range(len(col)):
	        col1[i] = col1[i].lower()
	        if col1[i] == "amplitude":
	        	ampindex= col[i]
        Sfreq = float(request.data.get("frequency"))
        algo=request.data.get('algo')
        f1=request.data.get('f1')
        f2=request.data.get('f2')
        numtaps=request.data.get('numtaps')
        modelno = request.data.get('modelno')


        ## If modelno is not null get the freaquencies from 
        # database based on the modelno
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

            
        # to calculate fft
        

        
        x=df_in_second_api[ampindex]

        #filterresult = FILTER(x,Sfreq,f1,f2,numtaps)
        ## if algorithm selected is hilbert Transform,calculate the envelope signal and FFT of the envelope
        if algo == "hilbtrans":
            # For enveloping using hilbert transform          
            Env_x = abs(hilbert(FILTER(x,Sfreq,f1,f2,numtaps)))
            Env_x_rounded = np.round(Env_x,4)
            Env_dc = (Env_x_rounded  - np.mean(Env_x_rounded)).squeeze()
            FFT_dc = FFT(Env_dc,Sfreq)
            Envelope_dict={"EnvHilbertFreq":"null","EnvHilbertAmp":Env_dc.tolist(),
            "Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),
            "BPFO":"null","BPFI":"null","BSF":"null","FTF":"null","FBPFO":"null","FBPFI":"null","FBSF":"null",
            "FFTF":"null"}
            
            #Envelope_dict={"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
           
            #Envelope_dict={"EnvSignalHilbert":Env_dc,"EnvSignalHilbertFFT":FFT(Env_dc,Sfreq),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
            
            inner = request.data.get("inner")
            ## if modelno is null take other dimentions and calculate bearing
            #  faults using peakdetection algorithm
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
                    bearfreq=BearingFrequenies(rpm,nb,inner,outer,bd,angle)
                    dffreq = pd.DataFrame(FFT_dc['Frequencies'] ,columns=['Frequencies'])
                    dfamp = pd.DataFrame(FFT_dc['Amplitude'],columns=['Amplitude'])
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
                    freq_dict1=FaultDectector(df_freqamp,freq_list)
                   
                    for i in range(len(freq_list)):

                        all_freq=PEAKDETECTOR(df_freqamp,freq_list[i],4)
                        freq_dict[names[i]]=all_freq
                    
                    Envelope_dict={"EnvHilbertFreq":"null","EnvHilbertAmp":Env_dc.tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null","FBPFO":freq_dict1['BPFO'],"FBPFI":freq_dict1['BPFI'],"FBSF":freq_dict1['BSF'],"FFTF":freq_dict1['FTF']}
                    #Envelope_dict={"EnvHilbertFreq":"null","EnvHilbertAmp":Env_dc.tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":bearfreq['BPFO'],"BPFI":bearfreq['BPFI'],"BSF":bearfreq['BSF'],"FTF":bearfreq['FTF'],"FBPFO":freq_dict['BPFO'],"FBPFI":freq_dict['BPFI'],"FBSF":freq_dict['BSF'],"FFTF":freq_dict['FTF']}
                
                    #Envelope_dict={"EnvSignalHilbert":Env_dc,"EnvSignalHilbertFFT":FFT(Env_dc,Sfreq),"BPFO":BPFO,"BPFI":BPFI,"BSF":BSF,"FTF":FTF}
                    #Envelope_dict={"EnvSignalHilbertFFT":FFT(Env_dc,Sfreq),"BPFO":BPFO,"BPFI":BPFI,"BSF":BSF,"FTF":FTF}
            else:
               
                dffreq = pd.DataFrame(FFT_dc['Frequencies'] ,columns=['Frequencies'])
                dfamp = pd.DataFrame(FFT_dc['Amplitude'],columns=['Amplitude'])
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
                freq_dict1=FaultDectector(df_freqamp,freq_list)
                Envelope_dict={"EnvHilbertFreq":"null","EnvHilbertAmp":Env_dc.tolist(),
                "Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),
                "BPFO":"null","BPFI":"null","BSF":"null","FTF":"null","FBPFO":freq_dict1['BPFO'],
                "FBPFI":freq_dict1['BPFI'],"FBSF":freq_dict1['BSF'],"FFTF":freq_dict1['FTF']}
                
                #Envelope_dict={"EnvHilbertFreq":"null","EnvHilbertAmp":Env_dc.tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null","FBPFO":freq_dict['BPFO'],"FBPFI":freq_dict['BPFI'],"FBSF":freq_dict['BSF'],"FFTF":freq_dict['FTF']}
                #Envelope_dict={"EnvHilbertFreq":"null","EnvHilbertAmp":Env_dc.tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":BPFO,"BPFI":BPFI,"BSF":BSF,"FTF":FTF,"FBPFO":freq_dict['BPFO'],"FBPFI":freq_dict['BPFI'],"FBSF":freq_dict['BSF'],"FFTF":freq_dict['FTF']}
            
                #Envelope_dict={"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":BPFO,"BPFI":BPFI,"BSF":BSF,"FTF":FTF}

        ## if algorithm is demodulation,calculate envelope signal 
        # using demodulation algorithm and FFT of it       
        else:
            Ba1 = Sfreq/4
            Ba2 = (3/8)*Sfreq
            f0 = (Ba2 + Ba1)/2
            t = 1 /Sfreq
            raw_x = x * e**(-2j*pi*f0*t)
            Demod_x = 2 * FILTER(raw_x,Sfreq,f1,f2,numtaps = 51)
            Demod_x_rounded = np.round(Demod_x,4)
            Demod_dc = (Demod_x_rounded  - np.mean( Demod_x_rounded)).squeeze()
            
            FFT_dc = FFT(Demod_dc,Sfreq)
            
            Envelope_dict={"EnvHilbertFreq":"null","EnvHilbertAmp":Demod_dc.tolist(),
            "Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),
            "BPFO":"null","BPFI":"null","BSF":"null","FTF":"null","FBPFO":"null","FBPFI":"null",
            "FBSF":"null","FFTF":"null"}
                
            #Envelope_dict={"EnvSignalDemodulation":Demod_dc,"EnvSignalDemoduationFFT":FFT(Demod_dc,Sfreq),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
            
            rpmval = request.data.get("rpm")
            innerval = request.data.get("inner")
            if modelno=="":
                if innerval == "null":
                    inner=""
                else:
            
                    rpm=float(request.data.get("rpm"))
        
                    
                    nb=int(request.data.get("nb"))
                    inner=float(request.data.get("inner"))
                    outer=float(request.data.get("outer"))
                    bd=float(request.data.get("bd"))
                    angle=float(request.data.get("angle"))
                if(innerval!=""):
                    bearfreq=BearingFrequenies(rpm,nb,inner,outer,bd,angle)

                    Envelope_dict={"EnvHilbertFreq":"null","EnvHilbertAmp":abs(Demod_dc).tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":bearfreq['BPFO'],"BPFI":bearfreq['BPFI'],"BSF":bearfreq['BSF'],"FTF":bearfreq['FTF'],"FBPFO":"null","FBPFI":"null","FBSF":"null","FFTF":"null"}
                
                    #Envelope_dict={"EnvSignalDemodulation":Demod_dc,"EnvSignalDemoduationFFT":FFT(Demod_dc,Sfreq),"BPFO":BPFO,"BPFI":BPFI,"BSF":BSF,"FTF":FTF}
            else:
                Envelope_dict={"EnvHilbertFreq":"null","EnvHilbertAmp":abs(Demod_dc).tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":BPFO,"BPFI":BPFI,"BSF":BSF,"FTF":FTF,"FBPFO":"null","FBPFI":"null","FBSF":"null","FFTF":"null"}
                  
        #FFT_dict={"Frequencies":frequencies,"Amplitude":abs(fourierTransform)}
        # FFTZip = dict(zip(frequencies,abs(fourierTransform)))
        # print(FFTZip)
        ## Return as jsonresult
        return JsonResponse(Envelope_dict)
        #return HttpResponse(json.dumps(FFTZip))
        #return Response(data={responsedata},status=status.HTTP_200_OK)



@api_view(['GET','POST'])
def envelop_upload_withouttimenobfc(request):
    if request.method == 'GET':
        csv_file=request.data
        return Response(data="hi",status=status.HTTP_200_OK)
    if request.method == 'POST':
        #serializer = SnippetSerializer(data=request.data)
        #csv_file = request.data.get("file")
        
        input_file_json = json.loads(request.data.get('input_file'))
        df_in_second_api = pd.read_json(input_file_json)
        Sfreq = int(request.data.get("frequency"))
        algo=request.data.get('algo')
        f1=request.data.get('f1')
        f2=request.data.get('f2')
        numtaps=request.data.get('numtaps')
        

        
            

        # to calculate fft
        

        
        x=df_in_second_api['amplitude']
        
        #filterresult = FILTER(x,Sfreq,f1,f2,numtaps)
        
        if algo == "hilbtrans":
          
            # For enveloping using hilbert transform          
            Env_x = abs(hilbert(FILTER(x,Sfreq,f1,f2,numtaps)))
            Env_x_rounded = np.round(Env_x,4)
            Env_dc = (Env_x_rounded  - np.mean(Env_x_rounded)).squeeze()
            FFT_dc = FFT(Env_dc,Sfreq)
           
            Envelope_dict={"EnvHilbertFreq":"null","EnvHilbertAmp":Env_dc.tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
            
            #Envelope_dict={"EnvSignalHilbert":Env_dc,"EnvSignalHilbertFFT":FFT(Env_dc,Sfreq),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
        else:
            Ba1 = Sfreq/4
            Ba2 = (3/8)*Sfreq
            f0 = (Ba2 + Ba1)/2
            t = 1 /Sfreq
            raw_x = x * e**(-2j*pi*f0*t)
            Demod_x = 2 * FILTER(raw_x,Sfreq,f1,f2,numtaps = 51)
            Demod_x_rounded = np.round(Demod_x,4)
            Demod_dc = (Demod_x_rounded  - np.mean( Demod_x_rounded)).squeeze()
            
            FFT_dc = FFT(Demod_dc,Sfreq)

            Envelope_dict={"EnvHilbertFreq":"null","EnvHilbertAmp":abs(Demod_dc).tolist(),"Frequency":FFT_dc['Frequencies'].tolist(),"Amplitude":FFT_dc['Amplitude'].tolist(),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
                
            #Envelope_dict={"EnvSignalDemodulation":Demod_dc,"EnvSignalDemoduationFFT":FFT(Demod_dc,Sfreq),"BPFO":"null","BPFI":"null","BSF":"null","FTF":"null"}
            
                  
       
        return JsonResponse(Envelope_dict)
        #return HttpResponse(json.dumps(FFTZip))
        #return Response(data={responsedata},status=status.HTTP_200_OK)





def FILTER(x,Sfreq,f1,f2,numtaps):
    
    # removing dc bias
    dc_x = x - np.mean(x)
    # Convert the array to 2-d for convolution
    dc_x_2d=dc_x[:, np.newaxis]
    # Compute the coefficients of FIR filter     
    b_filter = firwin(int(numtaps), [float(f1), float(f2)], pass_zero = False)
    
    b_filter_round = np.round(b_filter,4)
    # Convert the filter coefficients array to 2-d for convolution
    b_filter_2d = b_filter_round[:, np.newaxis]
    # Convolution of the array of filter coefficients and the signal
    bandpass_x = convolve2d(dc_x_2d, b_filter_2d, 'same')
    bandpass_x = np.round(bandpass_x,4)
    # Flattening the array to 1-d
    bandpass_x = np.asarray(bandpass_x).squeeze()
    
    return bandpass_x
    
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

def FaultDectector(array, fault_freq):
    def findpeaklibrary(array, freq, N=4):

        freq_list = [i * freq for i in range(1, N + 1)]

        detected_freq = list()
        detected_amp = list()
        

        for expected_freq in freq_list:
            
            x = array.query('Frequencies>@expected_freq-5 & Frequencies<@expected_freq+5')
            
            fp = findpeaks(method='topology', lookahead=1, verbose=0)
            results = fp.fit(x['Amplitude'])
            peak_amp = list(results['df'].query('peak==True')['y'])
            peak_amp = max(peak_amp)
            peak_freq = list(array.query('Amplitude=={}'.format(peak_amp))['Frequencies'])[0]
            detected_freq.append(peak_freq)
            detected_amp.append(peak_amp)
        return {'Frequencies': detected_freq, 'Amplitude': detected_amp}

    df = array.copy()

    model = IsolationForest(n_estimators=100, max_samples='auto', contamination=float(0.01), max_features=1.0)
    model.fit(df[['Amplitude']])
    df['anomaly'] = model.predict(df[['Amplitude']])
    Anomaly_df = df[df['anomaly'] == -1]
    Anomaly_rms = np.sqrt(np.mean([i ** 2 for i in Anomaly_df['Amplitude']]))
    Anomaly_param = 2.5 * Anomaly_rms

    detected_peaks = list()
    for i in fault_freq:
        x = findpeaklibrary(df, i, 4)
        detected_peaks.append(x)

    detected_freq_dict = {'BPFO': detected_peaks[0], 'BPFI': detected_peaks[1], 'BSF': detected_peaks[2],
                          'FTF': detected_peaks[3]}

    true_cond = list()
    for i in detected_freq_dict.items():

        key = i[0]
        amps = i[1]['Amplitude']
        freq = i[1]['Frequencies']
        count = sum(n > Anomaly_param for n in amps)

        if count >= 3:
            cond = True
        else:
            cond = False

        if cond:
            true_cond.append(key)

    if not true_cond:
        return []

    else:
        fault_dict={'BPFO':[],'BPFI':[],'BSF':[],'FTF':[]}
        for fault in true_cond:
            fault_dict[fault] = detected_freq_dict[fault]['Frequencies']

        return fault_dict


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

@api_view(['GET','POST'])
def getmodelno(request):
    if request.method == 'POST':
        print("insode get modelno")
    #     mongo_client = MongoClient()
        
    #     mongo_client = MongoClient('mongodb://127.0.0.1:27017')
    #     db = mongo_client.iudb
    #     print(db)
    #     data=db.bearingfaults
    #     print(data)
    #     modellist=data.find({"ModelNo":"61804-2RZ SKF"})
    # #print("ModelNo:"+item["ModelNo"] +"BPFO:"+str(item["BPFO"]))
    #     print(modellist.count())
    #     for item in modellist:
    #         ModelNo = item["ModelNo"]
    #         print(ModelNo)


