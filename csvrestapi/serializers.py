from rest_framework.serializers import ModelSerializer
from .models import Contact,Fileupload

from rest_framework import serializers


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fileupload
        fields = ("file", "sampfreq")


