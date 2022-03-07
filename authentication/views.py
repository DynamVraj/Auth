from django.http import HttpResponse
from django.shortcuts import render,redirect # for 3
# for 1
from django.contrib.auth.models import User
# for 2
from django.contrib import messages
# for 4
from django.contrib.auth import authenticate,login,logout
from auth import settings
# for 9
from django.core.mail import EmailMessage,send_mail
# for 10(current_sites)
from django.contrib.sites.shortcuts import get_current_site
# for 10(render to string)
from django.template.loader import render_to_string
# for 10(urlsafe base 64 encode)
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
# for 10(force bytes)
from django.utils.encoding import force_bytes, force_text
# for 10(generate_token)
from . tokens import generate_token

# Create your views here.
def home(request):
    return render(request,"authentification/index.html")

def signup(request):

    if request.method == "POST":
        #1.creating users in database
        #username = request.POST.get('username')
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        #5.To check user already signup or not
        if User.objects.filter(username=username):
            messages.error(request,"Username already taken! Please try another username")
            return redirect('home')
        if User.objects.filter(email=email):
            messages.error(request,"email already registerd!")
            return redirect('home')
        #6.To check lenght of user is larger
        if len(username)>15:
            messages.error(request,"Username must be under 15 characters")
            return redirect('home')
        #7.confirm password doesnt matches
        if pass1!=pass2:
            messages.error(request,"Password didn't match")
            return redirect('home')
        #8.username must be aphanumeric
        if not username.isalnum():
            messages.error(request,"Username must be Alpha-Numeric")
            return redirect('home')

        #1
        myuser = User.objects.create_user(username,email,pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = False #this is for user will be login after he/she confirms into mail
        myuser.save()

        #2.to pop up message
        messages.success(request, "Your Account has been sucessfully created.We have sent you confirmation email.Please Confirm!!")

        #9.To send Welcome Emails
        subject = "Welcome to Charusat"
        message = "Hello" + myuser.first_name + "!! \n" + "Welcome to CSE!! \n Thanks for visiting website \n we have sent you confirmation email to activate your account.\n\nThanking you"
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject,message,from_email,to_list,fail_silently=True)

        #10.Confimation email (tokens.py)

        current_site = get_current_site(request)
        email_subject = "Confirm you email @charusat login!!"
        msg = render_to_string('email_confirmation.html',{
            'name' : myuser.first_name,
            'domain' : current_site.domain,
            'uid' : urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token' : generate_token.make_token(myuser),
        })
        email = EmailMessage(
            email_subject,
            msg,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )
        email.fail_silently = True
        email.send()

        #3.to redirect to another page after creating use into DB
        return redirect('signin')

    return render(request,"authentification/signup.html")

def signin(request):

    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']

        #4.to check whether username and password is correct or not (already stored in DB or not
        user = authenticate(username=username,password=pass1)

        if user is not None:
            login(request,user)
            fname = user.first_name
            return render(request,"authentification/index.html",{'fname':fname})
        else:
            messages.error(request,"Bad Credentials")
            return redirect('home')

    return render(request,"authentification/signin.html")

def signout(request):
    logout(request)
    messages.success(request,"Loged Out Successfully")
    return redirect('home')

#11. to active user after confirmation mail
def activate(request,uidb64,token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        myuser=None

    if myuser is not None and generate_token.check_token(myuser,token):
        myuser.is_active = True
        myuser.save()
        login(request,myuser)
        return redirect('home')
    else:
        return render(request,'activation_failed.html')