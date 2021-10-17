from django import forms
from django.db.models import fields
from django.forms import widgets
from django.forms.models import model_to_dict
from .models import Customer, Order, Product
from django.contrib.auth.models import User


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields =['ordered_by', 'ship_address', 'phone', 'email', 'payment_method']

        widgets = {
            'ordered_by': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'ship_address': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'email': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'payment_method': forms.Select(attrs={
                'class':'form-control'
            })
        }

class CustomerRegistrationForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
                'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
                'class': 'form-control'}))
    email = forms.CharField(widget=forms.EmailInput(attrs={
                'class': 'form-control'}))
    class Meta:
        model = Customer
        fields = ['username','password','email','full_name','address',]
        
        widgets = {
            
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'address': forms.TextInput(attrs={
                'class':'form-control'
            })
        }
        
    def clean_username(self):
        uname = self.cleaned_data.get('username')
        if User.objects.filter(username = uname).exists():
            raise forms.ValidationError('Customer was allready existed !')

        return uname
    
        
    
    
    
class CustomerLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput())
    password = forms.CharField(widget=forms.PasswordInput())
    
    
    
    
class ForgotPasswordForm(forms.Form):
    email = forms.CharField(widget=forms.EmailInput(attrs={
        'class':'form-control',
        'placeholder':'Enter the email used in customer account.'
    }))
    
    def clean_email(self):
        e = self.cleaned_data.get('email')
        if Customer.objects.filter(user__email = e).exists():
            pass
        else:
            raise forms.ValidationError('Customer with this account dose not exists !')
        return e
    
    
class ProductForm(forms.ModelForm):
    more_images = forms.FileField(required=False, widget=forms.FileInput(attrs={'class':'form-control','multiple':True}))
    
    class Meta:
        model = Product
        fields = ['title','slug', 'category', 'image', 'marked_price',
                  'selling_price', 'description', 'warranty', 'return_policy']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the product title here...'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the unique slug here...'
            }),
            'category': forms.Select(attrs={
                'class':'form-control'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class':'form-control'
            }),
            'marked_price': forms.NumberInput(attrs={
                'class':'form-control'
            }),
            'selling_price': forms.NumberInput(attrs={
                'class':'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class':'form-control'
            }),
            'warranty': forms.Textarea(attrs={
                'class':'form-control'
            }),
            'return_policy': forms.TextInput(attrs={
                'class':'form-control'
            }),
            
        }
        
    

