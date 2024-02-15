from django.shortcuts import render,redirect
from django.views.generic import View
from budget.models import Transaction
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.utils import timezone
from django.db.models import Sum
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views.decorators.cache import never_cache
class TransactionForm(forms.ModelForm):
    class Meta:
        model=Transaction
        exclude=("created_date","user_object")
        # fields=["title","user","category","type","amount","title"]
        # fields="__all__"
        widgets={
            "title":forms.TextInput(attrs={"class":"form-control"}),
            "amount":forms.NumberInput(attrs={"class":"form-control"}),
            "type":forms.Select(attrs={"class":"form-control form-select"}),
            "category":forms.Select(attrs={"class":"form-control form-select"})
        }
class RegistrationForm(forms.ModelForm):
    class Meta:
        model=User
        fields=["username","email","password"]
        widgets={
            "username":forms.TextInput(attrs={"class":"form-control"}),
            "email":forms.EmailInput(attrs={"class":"form-control"}),
            "password":forms.PasswordInput(attrs={"class":"form-control"})
        }
class LoginForm(forms.Form):#no create no update
    username=forms.CharField(widget=forms.TextInput(attrs={"class":"form-control"}))
    password=forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control"}))
def signin_required(fn):
    def wrapper(request,*args,**kwargs):
        if not request.user.is_authenticated:
            messages.error(request,"invalid session")
            return redirect("signin")
        else:
            return fn(request,*args,**kwargs)
    return wrapper
decor=[signin_required,never_cache]
# Create your views here.
#  transaction list view
# localhost:8000/transations/all/
# method:get
@method_decorator(decor,name="dispatch")
class TransactionListView(View):
    def get(self,request,*args,**kwargs):
        qs=Transaction.objects.filter(user_object=request.user)
        current_month=timezone.now().month
        current_year=timezone.now().year
        data=Transaction.objects.filter(
            created_date__month=current_month,
            created_date__year=current_year,
            user_object=request.user
        ).values("type").annotate(type_total=Sum("amount"))
        cata_qs=Transaction.objects.filter(
            created_date__month=current_month,
            created_date__year=current_year,
            user_object=request.user
        ).values("category").annotate(cat_sum=Sum("amount"))
        # expence_total=Transaction.objects.filter(
        #     user_object=request.user,
        #     type="expense",
        #     created_date__month=current_month,
        #     created_date__year=current_year
        # ).aggregate(Sum("amount"))
        # income_total=Transaction.objects.filter(
        #     user_object=request.user,
        #     type="income",
        #     created_date__month=current_month,
        #     created_date__year=current_year
        # ).aggregate(Sum("amount"))
        # print(expence_total)
        # print(income_total)
        return render(request,"transaction.html",{"data":qs,"type_total":data,"cat_data":cata_qs})
# view for creating transaction
# localhost:8000/transations/add/
# method:get,post
@method_decorator(decor,name="dispatch")
class TransactionCreateView(View):
    def get(self,request,*args,**kwargs):
        form=TransactionForm
        return render(request,"transation_add.html",{"form":form})
    def post(self,request,*args,**kwargs):
        form=TransactionForm(request.POST)
        if form.is_valid():
            # for modelform
            form.instance.user_object=request.user
            form.save()
            # for normal form
            # data=form.cleaned_data
            # Transaction.objects.create(**data,user_object=request.user)
            messages.success(request,"transaction has been added successfully")
            return redirect("transation-list")
        else:
            messages.error(request,"failed to add transaction")
            return render(request,"transation_add.html",{"form":form})
# view for creating transaction detail
# localhost:8000/transations/{id}/
# method:get
@method_decorator(decor,name="dispatch")
class TransactionDetailView(View):
    def get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        qs=Transaction.objects.get(id=id)
        return render(request,"transation_detail.html",{"data":qs})
#view for deleting transaction
    # localhost:8000/transaction/{id}/remove/
    # method:get
@method_decorator(decor,name="dispatch")
class TransactionDeleteView(View):
    def get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        Transaction.objects.filter(id=id).delete()
        messages.success(request,"transaction has been removed")
        return redirect("transation-list")
# view for updateing transaction
    # localhost:8000/transaction/{id}/change/
    # method:get,post
@method_decorator(decor,name="dispatch")
class TransactionUpdateView(View):
    def get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        transaction_object=Transaction.objects.get(id=id)
        form=TransactionForm(instance=transaction_object)
        return render(request,"transaction_edit.html",{"form":form})
    def post(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        transaction_object=Transaction.objects.get(id=id)
        data=request.POST
        form=TransactionForm(data,instance=transaction_object)
        if form.is_valid():
            form.save()
            messages.success(request,"transaction has been removed")
            return redirect("transation-list")
        else:
            messages.error(request,"failed to update transaction")
            return render(request,"transaction_edit.html",{"form":form})
# view for registration
    # localhost:8000/signup/
    # method:get,post
class SignupView(View):
    def get(self,request,*args,**kwargs):
        form=RegistrationForm()
        return render(request,"register.html",{"form":form})
    def post(self,request,*args,**kwargs):
        form=RegistrationForm(request.POST)
        if form.is_valid():
            User.objects.create_user(**form.cleaned_data)
            return redirect("signin")
        else:
            return render(request,"register.html",{"form":form})
# view for signin
        # localhost:8000/signin/
        # method:get,post
class SigninView(View):
    def get(self,request,*args,**kwargs):
        form=LoginForm()
        return render(request,"login.html",{"form":form})
    def post(self,request,*args,**kwargs):
        form=LoginForm(request.POST)
        if form.is_valid():
            usrname=form.cleaned_data.get("username")
            pwd=form.cleaned_data.get("password")
            user_object=authenticate(request,username=usrname,password=pwd)
            if user_object:
                login(request,user_object)
                return redirect("transation-list")
        return render(request,"login.html",{"form":form})
# view for signout
    # localhost:8000/signout/
    # method:get
@method_decorator(decor,name="dispatch")
class SignOutView(View):
    def get(self,request,*args,**kwargs):
        logout(request)
        return redirect("signin")



    
        
        




        


    

    
