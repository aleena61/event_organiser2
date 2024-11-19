from django.shortcuts import render

# Create your views here.
# views.py

# views.py
import google.generativeai as genai
from django.shortcuts import render, redirect,get_object_or_404
from .models import Event, EventPhoto, OldPhoto, Competition
from .forms import EventForm, CompetitionForm, EventPhotoForm, OldPhotoForm
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime
#genai.configure(api_key="AIzaSyBx731nHQN7dUUT4sAodinK09LmWu5RGRY")



def calendar_view(request):
    # Query all events from the database
    events = Event.objects.all()
    
    # Convert events into a dictionary with the date as the key
    events_data = {
        event.date.strftime('%Y-%m-%d'): event.name for event in events
    }
    # Get the current month and year for the dropdown menus
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    # Pass events and the current month/year to the template
    return render(request, 'events/calendar.html', {
        'events_dict': events_data,
        'current_month': current_month,
        'current_year': current_year
    })
    # Pass the dictionary to the template
    

def add_event(request):
    if request.method == 'POST':
        event_form = EventForm(request.POST)
        competition_form = CompetitionForm(request.POST)
        
        # Handle multiple photo uploads
        event_photos = request.FILES.getlist('event_photos')
        old_photos = request.FILES.getlist('old_photos')

        if event_form.is_valid() and competition_form.is_valid():
            # Save Event
            event = event_form.save()

            # Save Competition
            competition = competition_form.save(commit=False)
            competition.event = event
            competition.save()

            # Save Event Photos
            for photo in event_photos:
                EventPhoto.objects.create(event=event, image=photo)

            # Save Old Photos
            for old_photo in old_photos:
                OldPhoto.objects.create(event=event, image=old_photo)

            return redirect('event_detail', event_id=event.id)

    else:
        event_form = EventForm()
        competition_form = CompetitionForm()

    return render(request, 'events/add_event.html', {
        'event_form': event_form,
        'competition_form': competition_form,
    })
def home(request):
    events = Event.objects.all()  # Get all events from the database
    return render(request, 'events/home.html', {'events': events})
def event_detail(request, event_id):
    # Fetch the event by ID
    event = get_object_or_404(Event, id=event_id)

    # Get related event photos, old photos, and competitions
    event_photos = event.photos.all()
    old_photos = event.old_photos.all()
    competitions = event.competitions.all()

    # Pass all the data to the template
    return render(request, 'events/event_detail.html', {
        'event': event,
        'event_photos': event_photos,
        'old_photos': old_photos,
        'competitions': competitions,
    })
def create_newsletter(request, event_id):
    # Get the event by ID
    event = Event.objects.get(id=event_id)

    # Handle POST request to generate newsletter
    if request.method == 'POST':
        # Generate the content for the newsletter using AI
        newsletter_content = generate_newsletter(event)

        return render(request, 'events/newsletter_detail.html', {
            'newsletter_content': newsletter_content,
            'event': event
        })

    return render(request, 'events/create_newsletter.html', {'event': event})

# Generate the newsletter content using Gemini API
def generate_newsletter(event):
    content = f"""
    <h2>{event.name}</h2>
    <p><strong>Location:</strong> {event.place}</p>
    <p><strong>Date:</strong> {event.date}</p>
    <p><strong>Description:</strong> {event.description}</p>
    <p><strong>Don't miss out on this amazing event!</strong></p>
    """
    
    # Example of generating content through Gemini API
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(content)
    
    # Return the response text as the generated newsletter
    return response.text

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Log the user in
            login(request, user)
            print("User authenticated and logged in")
            messages.success(request, "Logged in successfully.")
            return redirect('home')  # Redirect to the home page
        else:
            # Invalid credentials
            print("Invalid credentials")
            messages.error(request, "Invalid username or password.")

        # Render the login page
    return render(request, 'events/login.html')    

# Signup View


def signup_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')  # Full Name
        email = request.POST.get('email')  # Email
        password = request.POST.get('password')  # Password

        # Validate inputs
        if not name or not email or not password:
            messages.error(request, "All fields are required.")
            return redirect('signup')

        # Check if the username or email is already taken
        if User.objects.filter(username=name).exists():
            messages.error(request, "Username already exists. Please choose another.")
            return redirect('signup')
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered. Try logging in.")
            return redirect('signup')

        # Create the user
        try:
            user = User.objects.create_user(
                username=name,  # Using `name` as `username`
                email=email,
                password=password
            )
            user.save()
            messages.success(request, "Account created successfully. You can now log in.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")
            return redirect('signup')

    # Render signup page for GET requests
    return render(request, 'events/signup.html')

# Logout View
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')

