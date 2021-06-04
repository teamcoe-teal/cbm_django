import math
import pytest
from CBM_Functions_1 import BearingFrequencies


def test_BearingFrequencies():
   assert(BearingFrequencies(rpm=1772,max_rated_rpm=3000,N=9,Inner=25,Outer=52,Bd=7.94,angle=0)) == {'BPFO': 105.49153246753248, 'BPFI': 160.30846753246755, 'BSF': 137.11242003336713, 'FTF': 11.721281385281387}

def test_BearingFrequencirs_type_error():
   '''
   Check if none of the parameter is 0 except angle
   '''
   with pytest.raises(Exception):
      assert(BearingFrequencies(rpm=0,max_rated_rpm=3000,N=9,Inner=25,Outer=52,Bd=7.94,angle=0)) == \
      {'BPFO': 105.49153246753248, 'BPFI': 160.30846753246755, 'BSF': 137.11242003336713, 'FTF': 11.721281385281387}
   with pytest.raises(Exception):
      assert(BearingFrequencies(rpm=1772,max_rated_rpm=0,N=9,Inner=25,Outer=52,Bd=7.94,angle=0)) == \
      {'BPFO': 105.49153246753248, 'BPFI': 160.30846753246755, 'BSF': 137.11242003336713, 'FTF': 11.721281385281387}
   with pytest.raises(Exception):
      assert(BearingFrequencies(rpm=1772,max_rated_rpm=3000,N=0,Inner=25,Outer=52,Bd=7.94,angle=0)) == \
      {'BPFO': 105.49153246753248, 'BPFI': 160.30846753246755, 'BSF': 137.11242003336713, 'FTF': 11.721281385281387}
   with pytest.raises(Exception):
      assert(BearingFrequencies(rpm=1772,max_rated_rpm=3000,N=9,Inner=0,Outer=52,Bd=7.94,angle=0)) == \
      {'BPFO': 105.49153246753248, 'BPFI': 160.30846753246755, 'BSF': 137.11242003336713, 'FTF': 11.721281385281387}
   with pytest.raises(Exception):
      assert(BearingFrequencies(rpm=1772,max_rated_rpm=3000,N=9,Inner=25,Outer=0,Bd=7.94,angle=0)) == \
      {'BPFO': 105.49153246753248, 'BPFI': 160.30846753246755, 'BSF': 137.11242003336713, 'FTF': 11.721281385281387}
   with pytest.raises(Exception):
      assert(BearingFrequencies(rpm=1772,max_rated_rpm=3000,N=9,Inner=25,Outer=52,Bd=0,angle=0)) == \
      {'BPFO': 105.49153246753248, 'BPFI': 160.30846753246755, 'BSF': 137.11242003336713, 'FTF': 11.721281385281387}
      
      



   
      
