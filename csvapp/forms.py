from django import forms



class csvwithouttime(forms.Form):
    file=forms.FileField()
    algo = forms.NumberInput()
    sampfreq = forms.NumberInput()
    
    rpm = forms.NumberInput()
    maxrrpm = forms.NumberInput()
    
    n = forms.NumberInput()
    inner = forms.FloatField()
    
    outer = forms.FloatField()
    
    bd = forms.FloatField()
    angle = forms.FloatField()
    modelno=forms.CharField()
    # def __str__(self):
    #     return self.name + ":"+ str(self.filepath)

    