from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
import requests
from .forms import *
from .models import *
from django.urls import reverse_lazy, reverse
from django.http import request,HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, DetailView, View, CreateView, FormView, ListView
from django.db.models import Q
from django.core.paginator import Paginator
from .utils import password_reset_token
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.parsers import JSONParser
from .serializers import *
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import generics, mixins
# Create your views here.


class CoreMixin(object):
    def dispatch(self, request, *args, **kwargs):
        cart_id = request.session.get('cart_id', None)
        if cart_id:
            cart_obj = Cart.objects.get(id = cart_id)
            # cart_obj = get_object_or_404(Cart, pk= cart_id)
            if request.user.is_authenticated and request.user.customer:
                cart_obj.customer = request.user.customer
                cart_obj.save()
        return super().dispatch(request, *args, **kwargs)


class HomeView(CoreMixin, TemplateView):
    template_name = "home.html" 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_products = Product.objects.all().order_by("-id")
        paginator = Paginator(all_products, 4)   
        page_number = self.request.GET.get('page')
        product_list = paginator.get_page(page_number)
        
        context['product_list'] = product_list
        return context
        
 
class AllProductsView(CoreMixin,TemplateView):
    template_name = "allproducts.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['allcategories'] = Category.objects.all()
        return context
    
    
class ProductDetailView(CoreMixin,TemplateView):
    template_name = 'productdetail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_slug = self.kwargs['slug']
        product = Product.objects.get(slug = url_slug)
        product.view_count +=1
        product.save()
        context['product'] = product
        return context
    
    

    
class AddToCart(CoreMixin,TemplateView):
    template_name = 'addtocart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #get product id from required url
        product_id = self.kwargs['pro_id']
        #get product
        product_obj = Product.objects.get(id = product_id)
        #check id cart exists
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart_obj = Cart.objects.get(id = cart_id)
            this_product_in_cart = cart_obj.cartproduct_set.filter(product = product_obj)
            
            if this_product_in_cart.exists():
                cartproduct = this_product_in_cart.last()
                cartproduct.quantity +=1
                cartproduct.subtotal += product_obj.selling_price
                cartproduct.save()
                cart_obj.total += product_obj.selling_price
                cart_obj.save()
                # messages.info("This item quantity was update")
            else:
                cartproduct = CartProduct.objects.create(
                    cart = cart_obj, product = product_obj, 
                    rate = product_obj.selling_price, 
                    quantity = 1, 
                    subtotal = product_obj.selling_price)
                # messages.info("This product was added to your cart")
                cart_obj.total += product_obj.selling_price
                cart_obj.save()
        else:
            cart_obj = Cart.objects.create(total=0)
            self.request.session['cart_id'] = cart_obj.id
            cartproduct = CartProduct.objects.create(
                    cart = cart_obj, product = product_obj, 
                    rate = product_obj.selling_price, 
                    quantity = 1, 
                    subtotal = product_obj.selling_price)
            cart_obj.total += product_obj.selling_price
            cart_obj.save()
            # messages.info("This product was added to your cart")
        #check if product already exists in cart
        
        return context
    

class ManageCartView(CoreMixin,View):
    def get(self, request, *args, **kwargs):
        cp_id = self.kwargs['cp_id']
        action = request.GET.get('action')
        cp_obj = CartProduct.objects.get(id = cp_id)
        cart_obj = cp_obj.cart
        if action == 'inc':
            cp_obj.quantity +=1
            cp_obj.subtotal += cp_obj.rate
            cp_obj.save()
            cart_obj.total += cp_obj.rate
            cart_obj.save()
        elif action == 'dcr':
            cp_obj.quantity -=1
            cp_obj.subtotal -= cp_obj.rate
            cp_obj.save()
            cart_obj.total -= cp_obj.rate
            cart_obj.save()
            if cp_obj.quantity <=0:
                cp_obj.delete()
        elif action == 'rmv':
            cart_obj.total -= cp_obj.subtotal
            cart_obj.save()
            cp_obj.delete()
        else:
            pass
        return redirect('core:mycart')


    
class MyCartView(CoreMixin,TemplateView):
    template_name = 'mycart.html'    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get('cart_id', None)
        if cart_id:
            cart = Cart.objects.get(id = cart_id)
        else: 
            cart = None
        context['cart'] = cart
        return context    
        
        

class EmptyCartView(CoreMixin,View):
    def get(self, request, *args, **kwargs):
        cart_id = request.session.get('cart_id', None)
        if cart_id:
            cart = Cart.objects.get(id = cart_id)
            cart.cartproduct_set.all().delete()
            cart.total = 0
            cart.save()
        return redirect('core:mycart')



class CheckoutView(CoreMixin,CreateView):
    template_name = 'checkout.html'
    form_class = CheckoutForm
    success_url = reverse_lazy('core:home')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.customer:
            pass
        else:
            return redirect('/login/?next=/checkout/')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get('cart_id', None)
        if cart_id:
            cart_obj = Cart.objects.get(id = cart_id)
        else:
            cart_obj = None
        context['cart'] = cart_obj
        return context
    
    def form_valid(self, form):
        cart_id = self.request.session.get('cart_id')
        if cart_id:
            cart_obj = Cart.objects.get(id = cart_id)
            form.instance.cart = cart_obj
            form.instance.subtotal = cart_obj.total
            form.instance.discount = 0
            form.instance.total = cart_obj.total
            form.instance.order_status = "Order Received"
            del self.request.session['cart_id']
            pm = form.cleaned_data.get('payment_method')
            order = form.save()
            if pm == 'Khalti':
                return redirect(reverse('core:khaltirequest') + '?o_id=' + str(order.id))
            elif pm == 'Esewa':
                return redirect(reverse('core:esewarequest') + '?o_id=' + str(order.id))
        else:
            return redirect('core:home')
        return super().form_valid(form)
    
    
#payment khalti
class KhaltiRequestView(View):
    def get(self, request, *args, **kwargs):
        o_id = self.request.GET.get('o_id')
        order = Order.objects.get(id = o_id)
        context = {
            'order' : order
        }
        return render(request, 'khaltirequest.html', context)
    

class KhaltiVerifyView(View):
    def get(self, request, *args, **kwargs):
        data={}
        return JsonResponse(data)

#payment esewa
class EsewaRequestView(View):
    def get(self, request, *args, **kwargs):
        o_id = self.request.GET.get('o_id')
        order  = Order.objects.get(id = o_id)
        context = {
            'order': order
        }
        return render(request, 'esewarequest.html', context)

class EsewaVerifyView(View):
    def get(self, request, *args, **kwargs):
        import xml.etree.ElementTree as ET
        oid = self.request.GET.get("oid")
        amt = request.GET.get('amt')
        refId = request.GET.get('refId')
        
        url ="https://uat.esewa.com.np/epay/transrec"
        d = {
            'amt': amt,
            'scd': 'EPAYTEST',
            'rid': refId,
            'pid': oid,
        }
        resp = requests.post(url, d)
        root = ET.fromstring(resp.content)
        status = root[0].text.strip()
        
        order_id = oid.split("_")[1]
        ord_obj = Order.objects.get(id = order_id)
        if status == "Success":
            ord_obj.payment_completed = True
            ord_obj.save()
            return redirect("/")
        else:
            
            return redirect("/esewa-request/?o_id="+order_id)

    
class CustomerRegistrationView(CreateView):
    template_name = 'customerregistration.html'
    form_class = CustomerRegistrationForm
    success_url = reverse_lazy('core:home')
    
    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        email = form.cleaned_data.get('email')
        user = User.objects.create_user(username, email, password)
        form.instance.user = user
        login(self.request, user)
        return super().form_valid(form)
    
    def get_success_url(self):
        if 'next' in self.request.GET:
            next_url = self.request.GET.get('next')
            return next_url
        else:
            return self.success_url

class CustomerLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('core:home')
    
    
class CustomerLoginView(FormView):
    template_name = 'customerlogin.html'
    form_class = CustomerLoginForm
    success_url = reverse_lazy('core:home')
    
    def form_valid(self, form):
        uname = form.cleaned_data.get('username')
        pword = form.cleaned_data["password"]
        usr = authenticate(username = uname, password = pword)
        if usr is not None and Customer.objects.filter(user = usr).exists():
            login(self.request, usr)
        else:
            return render(self.request, self.template_name, {'form': self.form_class, 'error':"Invalid credentials"})
        
        return super().form_valid(form)

    def get_success_url(self):
        if 'next' in self.request.GET:
            next_url = self.request.GET.get('next')
            return next_url
        else:
            return self.success_url
        

class PasswordForgotView(FormView):
    template_name = 'forgotpassword.html'
    form_class = ForgotPasswordForm
    success_url = '/forgot-password/'

    def form_valid(self, form):
        #get email from user
        email = form.cleaned_data.get('email')    
        #get current host ip/domain  
        url = self.request.META['HTTP_HOST']
        #get customer  and then user
        customer = Customer.objects.get(user__email = email)
        user = customer.user
        #send mail to the user with email
        text_content = 'Please click the link below to reset your password'
        html_content = url + "/password-reset/" + email + "/" + password_reset_token.make_token(user) + "/" 
        send_mail(
            'Password Reset Link | Django Ecommerce', 
            text_content + html_content, 
            settings.EMAIL_HOST_USER, 
            [email],
            fail_silently=False,
        )
        return super().form_valid(form)
        
        
        
class CustomerProfileView(TemplateView):
    template_name = "customerprofile.html"
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            pass
        else:
            return redirect('/login/?next=/profile/')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.request.user.customer
        context['customer'] = customer
        orders = Order.objects.filter(cart__customer = customer).order_by('-id')
        context['orders'] = orders
        return context
    


class CustomerOrderDetail(DetailView):
    template_name = "customerorderdetail.html"
    model = Order
    context_object_name = "ord_obj"
    
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            order_id = self.kwargs['pk']
            order = Order.objects.get(id = order_id)
            if request.user.customer != order.cart.customer:
                return redirect("core:customerprofile" )
        else:
            return redirect('/login/?next=/profile/')
        return super().dispatch(request, *args, **kwargs)



class AdminLoginView(FormView):
    template_name = 'adminpages/adminlogin.html'
    form_class = CustomerLoginForm
    success_url = reverse_lazy("core:adminhome")

    def form_valid(self, form):
        uname = form.cleaned_data.get('username')
        pword = form.cleaned_data.get('password')
        usr = authenticate(username = uname, password = pword)
        if usr is not None and Admin.objects.filter(user = usr).exists():
            login(self.request, usr)
        else:
            return render(self.request, self.template_name, {'form': self.form_class, 'error':"Invalid credentials"})
        
        return super().form_valid(form)



#Mixin
class AdminRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Admin.objects.filter(user = request.user).exists():
            pass
        else:
            return redirect('/admin-login/')
        return super().dispatch(request, *args, **kwargs)



class AdminHomeView(AdminRequiredMixin, TemplateView):
    template_name = 'adminpages/adminhome.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pendingorders'] = Order.objects.filter( order_status = 'Order Received').order_by("-id")
        return context




class AdminOrderDetailView(AdminRequiredMixin, DetailView):
    template_name = ('adminpages/adminorderdetail.html')
    model = Order
    context_object_name = 'ord_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['allstatus'] = ORDER_STATUS
        return context


class AdminOrderListView(AdminRequiredMixin, ListView):
    template_name = ('adminpages/adminorderlist.html')
    queryset = Order.objects.all().order_by("-id")
    context_object_name = 'allorders'



class AminOrderStatusChangeView(AdminRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        order_id = self.kwargs['pk']
        order_obj = Order.objects.get(id = order_id)
        new_status = request.POST.get('status')
        order_obj.order_status = new_status
        order_obj.save()
        return redirect(reverse_lazy('core:adminorderdetail', kwargs={'pk': self.kwargs['pk']}))



class SearchView(TemplateView):
    template_name = 'search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kw = self.request.GET.get('keyword')
        results = Product.objects.filter(Q(title__icontains = kw) | Q(description__icontains = kw))
        context['results'] = results
        return context


class AdminProductListView(AdminRequiredMixin, ListView):
    template_name = 'adminpages/adminproductlist.html'
    queryset = Product.objects.all().order_by("-id")
    context_object_name = 'allproducts'
    

class AdminProductCreateView(AdminRequiredMixin, CreateView):
    template_name = 'adminpages/adminproductcreate.html'
    form_class = ProductForm
    success_url = reverse_lazy('core:adminproductlist')

    def form_valid(self, form):
        p = form.save()
        images = self.request.FILES.getlist("more_images")
        for i in images:
            ProductImage.objects.create(product=p, image=i)
        return super().form_valid(form)

class AboutView(CoreMixin,TemplateView):
    template_name = "about.html" 
    
    
class ContactView(CoreMixin,TemplateView):
    template_name = "contact.html"
    




#API

class ProductAPIView(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerialiszer(products, many = True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerialiszer(data = request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_201_CREATED)
        return Response(serializer.error, status=status.HTTP_400_BAD_REQUEST)
