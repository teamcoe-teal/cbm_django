from django.db import models

# Create your models here.
class csvwithouttime(models.Model):
    file=models.FileField()
    sampfreq = models.CharField(max_length=45)


class Contact(models.Model):
    
    file=models.FileField()
    sampfreq = models.CharField(max_length=45)


    def __str__(self):
        return f"{self.file} {self.sampfreq}"


class Fileupload(models.Model):
    
    file=models.FileField()
    sampfreq = models.CharField(max_length=45)


    def __str__(self):
        return f"{self.file} {self.sampfreq}"
