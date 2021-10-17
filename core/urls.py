from django.urls import path
from .views import *

app_name = 'core'
urlpatterns = [
    path('', HomeView.as_view(), name="home"),
    path('all-products/', AllProductsView.as_view(), name="allproducts"),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name = "productdetail"),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('search/', SearchView.as_view(), name = 'search'),
    
    #cart
    path('add-to-cart-<int:pro_id>/', AddToCart.as_view(), name = 'add-to-cart'),
    path('my-cart/', MyCartView.as_view(), name = 'mycart'),
    path('manage-cart/<int:cp_id>/', ManageCartView.as_view(), name = 'managecart'),
    path('empty-cart/', EmptyCartView.as_view(),name='emptycart'),
    
    #customer
    path('register/', CustomerRegistrationView.as_view(), name = 'customerregistration'),
    path('logout/', CustomerLogoutView.as_view(), name='logout'),
    path('login/', CustomerLoginView.as_view(), name='login'),
    path('profile/', CustomerProfileView.as_view(), name = "customerprofile"),
    path('profile/order-<int:pk>/', CustomerOrderDetail.as_view(), name = "customerorderdetail"),
    path('forgot-password/', PasswordForgotView.as_view(), name='forgotpassword'),
    
    #Admin
    path('admin-login/', AdminLoginView.as_view(), name="adminlogin"),
     path('admin-home/', AdminHomeView.as_view(), name='adminhome'),
    path('admin-order/<int:pk>/', AdminOrderDetailView.as_view(), name = 'adminorderdetail'),
    path('admin-all-orders/', AdminOrderListView.as_view(), name = 'adminorderlist'),
    path('admin-order-<int:pk>-change/', AminOrderStatusChangeView.as_view(), name = 'adminorderstatuschange'),
    path('admin-product/list/', AdminProductListView.as_view(), name = 'adminproductlist'),
    path('admin-product/add/', AdminProductCreateView.as_view(), name = 'adminproductcreate'),
    
    #payment
    path('esewa-request/', EsewaRequestView.as_view(), name = 'esewarequest'),
    path('esewa-verify/', EsewaVerifyView.as_view(), name = 'esewaverify'),
]