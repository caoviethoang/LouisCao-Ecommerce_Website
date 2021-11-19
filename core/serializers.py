from rest_framework import serializers
from .models import *

class ProductSerialiszer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['category','title','slug','image','marked_price','selling_price']