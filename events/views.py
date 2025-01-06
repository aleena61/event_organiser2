from django.shortcuts import render

# Create your views here.
# views.py

# views.py
import google.generativeai as genai 
from django.shortcuts import render, redirect,get_object_or_404
from .models import Event, EventPhoto, OldPhoto, Competition
from .forms import EventForm, CompetitionForm, EventPhotoForm, OldPhotoForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import Http404, JsonResponse
from datetime import datetime,timedelta
from django.core.mail import send_mail
from django.db.models import Sum
genai.configure(api_key="AIzaSyBx731nHQN7dUUT4sAodinK09LmWu5RGRY")


from django.shortcuts import render
from django.db.models import Sum

def event_dashboard(request):
    # Retrieve all events created by the logged-in user
    user_events = Event.objects.filter(user=request.user)

    # Retrieve data for the bar graph (event names and total visits)
    event_visits = (
        user_events.values('name')  # Group by event name
        .annotate(total_visits=Sum('visits'))  # Sum visits for each event
        .order_by('name')  # Order by event name
    )

    context = {
        'events': user_events,
        'event_visits': list(event_visits),  # Convert QuerySet to list for JSON serialization
    }

    return render(request, 'events/event_dashboard.html', context)


def delete_event(request, event_id):
    # Delete an event by ID
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    event.delete()
    return redirect('event_dashboard')

def calendar_view(request):
  
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    # Calculate the previous and next years
    prev_year = current_year - 1
    next_year = current_year + 1

    # Handle month and year query parameters to select any month/year
    month = request.GET.get('month', current_month)
    year = request.GET.get('year', current_year)

    # Ensure month and year are integers
    month = int(month)
    year = int(year)

    # Calculate the first and last day of the selected month
    first_day_of_month = datetime(year, month, 1)

    if month == 12:
        last_day_of_month = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day_of_month = datetime(year, month + 1, 1) - timedelta(days=1)

    # Get all events in the current month
    events_in_month = Event.objects.filter(date__range=[first_day_of_month, last_day_of_month])

    # Structure the calendar days with events
    days_in_month = []
    for day in range(1, last_day_of_month.day + 1):
        date = datetime(year, month, day)
        day_events = events_in_month.filter(date=date)
        days_in_month.append({
            'day': day,
            'events': day_events,
            'date': date,
        })

    return render(request, 'events/calendar.html', {
        'days_in_month': days_in_month,
        'current_month': month,
        'current_year': year,
        'prev_year': prev_year,
        'next_year': next_year,  # Pass previous and next years
    })

@login_required(login_url='login_view')
def add_event(request):
    if request.method == 'POST':
      
        event_form = EventForm(request.POST)
        competition_form = CompetitionForm(request.POST)
        
        # Handle multiple photo uploads
        event_photos = request.FILES.getlist('event_photos')
        old_photos = request.FILES.getlist('old_photos')

        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if event_form.is_valid():
            # Save Event
            event = event_form.save(commit=False)
            
            event.user = request.user

            event.status = 'pending'  # Default to pending status

            if latitude and longitude:
                event.latitude = latitude
                event.longitude = longitude

            event = event_form.save()

            # Save Competition
            competitions_data = request.POST.getlist('competitions[][name]')
            if competitions_data:
                for i in range(len(competitions_data)):
                    competition = Competition(
                        event=event,
                        name=competitions_data[i],
                        date=request.POST.getlist('competitions[][date]')[i],
                        place=request.POST.getlist('competitions[][place]')[i],
                        description=request.POST.getlist('competitions[][description]')[i]
                    )
                    competition.save()


            # Save Event Photos
            for photo in event_photos:
                EventPhoto.objects.create(event=event, image=photo)

            # Save Old Photos
            for old_photo in old_photos:
                OldPhoto.objects.create(event=event, image=old_photo)
                notify_user(event)
            
            return redirect('event_detail', event_id=event.id)

    else:

        event_form = EventForm()
        competition_form = CompetitionForm()

    return render(request, 'events/add_event.html', {
        'event_form': event_form,
        'competition_form': competition_form,
    })
def home(request):
    # Fetch approved events
    events = Event.objects.filter(status='approved')

    # Get trending events (top 5 by number of visits)
    trending_events = events.order_by('-visits')[:4]

    # Get recently added events (top 5 by date added)
    recently_added_events = events.order_by('-created_at')[:4]

    # Pass both lists to the template
    return render(request, 'events/home.html', {
        'events': events,
        'trending_events': trending_events,
        'recently_added_events': recently_added_events,
    })

def event_detail(request, event_id):
    # Fetch the event by ID
    event = get_object_or_404(Event, id=event_id)
    event.visits += 1
    event.save()
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

    # Handle POST request to approve, reject, or save edited newsletter
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            # Get the edited newsletter content from the form
            edited_content = request.POST.get('edited_newsletter', '')

            # Save the edited content as the newsletter
            event.newsletter = edited_content
            event.save()

            messages.success(request, 'Newsletter has been approved and saved.')
            return redirect('event_detail', event_id=event.id)  # Redirect to event detail page

        elif action == 'reject':
            messages.warning(request, 'Newsletter generation was rejected.')
            return redirect('create_newsletter', event_id=event.id)  # Redirect back to newsletter creation

    # Generate the content for the newsletter when the page is first loaded (GET request)
    newsletter_content = generate_newsletter(event)

    return render(request, 'events/newsletter_detail.html', {
        'newsletter_content': newsletter_content,
        'event': event
    })


# Generate the newsletter content using Gemini API
def generate_newsletter(event):
    content = f"""
    <h2>{event.name}</h2>
    <p><strong>Location:</strong> {event.place}</p>
    <p><strong>Date:</strong> {event.date}</p>
    <p><strong>Description:</strong> {event.description}</p>
    <p><strong>Don't miss out on this amazing event!</strong></p>
    <p>With the following details generate a newsletter for the event,
   in structured HTML with proper paragraphs and line breaks
   ,it should be well structured with place and 
    date like newspaper,and not more than 250 words.
    """
    
    # Example of generating content through Gemini API
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(content)
    
    # Return the response text as the generated newsletter
    return response.text


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile')  # Replace 'home' with your desired redirect URL
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'events/login.html')



def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # Match input field name
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Validate inputs
        if not username or not email or not password:
            messages.error(request, "All fields are required.")
            return redirect('signup_view')

        # Check if the username or email is already taken
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another.")
            return render(request, 'events/login.html', {'show_signup': True})
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered. Try logging in.")
            return render(request, 'events/login.html', {'show_signup': True})

        # Create the user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.save()

            subject = 'Welcome to Festfeed'
            message = f'Hi {username},\n\nThank you for signing up our platform. We are excited to have you onboard!'
            from_email = 'festfeed00@gmail.com'  # Replace with your email
            recipient_list = [email]
            send_mail(subject, message, from_email, recipient_list)
            
            messages.success(request, "Account created successfully. You can now log in.")
            return redirect('login_view')
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")
            return redirect('signup_view')

    # Render signup page for GET requests
    return render(request, 'events/login.html',{'show_signup': False})



# Logout View
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')

from django.db.models import Q


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Event, EventUser
from math import radians, sin, cos, sqrt, atan2


# Helper to calculate distance
def calculate_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    R = 6371  # Radius of the Earth in km
    return R * c


@login_required
def profile_view(request):
    user = request.user
    events = Event.objects.filter(status='approved')

    # Get user location
    user_lat = user.profile.latitude
    user_lon = user.profile.longitude

    # User visited events
    visited_events = EventUser.objects.filter(user=user, visited=True).values_list('event', flat=True)
    categories = Event.objects.filter(id__in=visited_events).values_list('category', flat=True)
    places = Event.objects.filter(id__in=visited_events).values_list('place', flat=True)

    # Suggested events based on category, place, and location
    suggested_events = []
    for event in events:
        distance = calculate_distance(user_lat, user_lon, event.latitude, event.longitude) if user_lat and user_lon else None
        if (event.category in categories or event.place in places or (distance and distance <= 50)):
            suggested_events.append(event)

    trending_events = events.order_by('-visits')[:4]
    recent_events = events.order_by('-created_at')[:4]
    print(recent_events)

    return render(request, 'events/profile.html', {
        'user': user,
        'events':events,
        'suggested_events': suggested_events,
        'trending_events': trending_events,
        'recent_events': recent_events,
    })

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
@csrf_exempt
def update_location(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        user = request.user

        if latitude and longitude:
            user.profile.latitude = latitude
            user.profile.longitude = longitude
            user.profile.save()
            return JsonResponse({'status': 'success', 'message': 'Location updated successfully'})

        return JsonResponse({'status': 'error', 'message': 'Invalid data'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@login_required
def bookmark_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    if event in user.bookmarked_events.all():
        user.bookmarked_events.remove(event)  # Remove bookmark
        bookmarked = False
    else:
        user.bookmarked_events.add(event)  # Add bookmark
        bookmarked = True

    return JsonResponse({'bookmarked': bookmarked})
@login_required
def bookmarked_events(request):
    user = request.user
    events = user.bookmarked_events.all()  # Get all bookmarked events
    return render(request, 'events/bookmarked_events.html', {'events': events})
@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Check if the user is the event creator or an admin
    if event.user != request.user and not request.user.is_staff:
        raise Http404("You do not have permission to edit this event.")

    if request.method == 'POST':
        event_form = EventForm(request.POST, instance=event)

        if event_form.is_valid():
            event = event_form.save(commit=False)

            # Mark the event as requested for approval
            event.requested_approval = True
            event.status = 'pending'  # Set to pending until admin approves

            event.save()

            # Notify admin or perform necessary actions here
            notify_user(event)
            return redirect('event_detail', event_id=event.id)
    else:
        event_form = EventForm(instance=event)

    return render(request, 'events/edit_event.html', {
        'event_form': event_form,
        'event': event
    })
# views.py
@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Check if the user is the event creator or an admin
    if event.user != request.user and not request.user.is_staff:
        raise Http404("You do not have permission to delete this event.")

    if request.method == 'POST':
        # Mark event as pending deletion
        event.delete_requested = True
        event.status = 'pending_deletion'
        event.save()

        # Notify admin or perform any necessary action
        notify_user(event)
        return redirect('event_detail', event_id=event.id)  # Delete the event
    return redirect('profile')  # Redirect to the event list or wherever you prefer
@staff_member_required
def manage_events(request):
    events = Event.objects.all()  # Fetch all events
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        action = request.POST.get('action')  # 'approve', 'reject', or 'pending'
        event = Event.objects.get(id=event_id)
        if action == 'approve':
            event.status = 'Approved'
        elif action == 'reject':
            event.status = 'Rejected'
        elif action == 'pending':
            event.status = 'Pending'
        event.save()
    return render(request, 'events/manage_events.html', {'events': events})
from django.core.mail import send_mail

def notify_user(event):
    user_email = event.user.email  # Assuming the Event model is linked to a user
    send_mail(
        subject="Event Status Updated",
        message=f"Your event '{event.name}' status has been updated to {event.status}.",
        from_email="festfeed00@gmail.com",
        recipient_list=[user_email],
    )
from django.http import JsonResponse

def check_login_status(request):
    if request.user.is_authenticated:
        return JsonResponse({'redirect_url': '/profile/'})  # Redirect to profile page
    else:
        return JsonResponse({'redirect_url': '/'})  # Redirect to home page


