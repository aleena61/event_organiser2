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
from datetime import datetime,timedelta, timezone
from django.core.mail import send_mail
from django.db.models import Sum, Count
from .models import Notification, Event
from django.utils import timezone
import random
import string
from django.core.cache import cache
from django.contrib.auth.hashers import make_password
import json
from django.conf import settings



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

# def calendar_view(request):
  
#     current_date = datetime.now()
#     current_month = current_date.month
#     current_year = current_date.year

#     # Calculate the previous and next years
#     prev_year = current_year - 1
#     next_year = current_year + 1

#     # Handle month and year query parameters to select any month/year
#     month = request.GET.get('month', current_month)
#     year = request.GET.get('year', current_year)

#     # Ensure month and year are integers
#     month = int(month)
#     year = int(year)

#     # Calculate the first and last day of the selected month
#     first_day_of_month = datetime(year, month, 1)

#     if month == 12:
#         last_day_of_month = datetime(year + 1, 1, 1) - timedelta(days=1)
#     else:
#         last_day_of_month = datetime(year, month + 1, 1) - timedelta(days=1)

#     # Get all events in the current month
#     events_in_month = Event.objects.filter(date__range=[first_day_of_month, last_day_of_month])

#     # Structure the calendar days with events
#     days_in_month = []
#     for day in range(1, last_day_of_month.day + 1):
#         date = datetime(year, month, day)
#         day_events = events_in_month.filter(date=date)
#         days_in_month.append({
#             'day': day,
#             'events': day_events,
#             'date': date,
#         })

#     return render(request, 'events/calendar.html', {
#         'days_in_month': days_in_month,
#         'current_month': month,
#         'current_year': year,
#         'prev_year': prev_year,
#         'next_year': next_year,  # Pass previous and next years
#     })


from datetime import datetime, timedelta
from django.shortcuts import render
from .models import Event

def calendar_view(request):
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

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

    prev_year = current_year - 1
    next_year = current_year + 1

    return render(request, 'events/calendar.html', {
        'days_in_month': days_in_month,
        'current_month': month,
        'current_year': year,
        'prev_year': prev_year,
        'next_year': next_year,
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Event, Competition, Category, EventPhoto, OldPhoto, Notification
from .forms import EventForm, CompetitionForm

@login_required(login_url='login_view')
def add_event(request):
    categories = Category.objects.all()  # Ensure 'categories' is always defined

    if request.method == 'POST':
        print("Received Data:", request.POST)  # Debugging
        event_form = EventForm(request.POST, request.FILES)
        
        competition_form = CompetitionForm(request.POST)

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

            event.save()
            event_form.save_m2m()  # Save ManyToManyField (categories)

            # ✅ Use .set() for Many-to-Many fields
            event.category.set(request.POST.getlist('category'))

            # Create notification for admin
            admin_user = User.objects.filter(username='john').first()
            if admin_user:
                Notification.objects.create(
                    user=admin_user,
                    message=f"{request.user.username} has requested to add an event: {event.name}.",
                )

            # Save Competitions
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

                    # Set single category per competition
                    category_id = request.POST.getlist('competitions[][category]')[i]  
                    if category_id:
                        competition.category.set([get_object_or_404(Category, id=category_id)])
                        competition.save()

            # Save Event Photos
            for photo in event_photos:
                EventPhoto.objects.create(event=event, image=photo)

            # Save Old Photos
            for old_photo in old_photos:
                OldPhoto.objects.create(event=event, image=old_photo)

            # Notify the user (assuming notify_user is defined elsewhere)
            notify_user(event)

            messages.success(request, "Event added successfully!")
            return redirect('event_detail', event_id=event.id)
        
        else:
            print("Form errors:", event_form.errors)  # Debugging: This will print errors in the console
            messages.error(request, "Error: Please check your inputs.")

    else:
        event_form = EventForm()
        competition_form = CompetitionForm()

    return render(request, 'events/add_event.html', {
        'event_form': event_form,
        'competition_form': competition_form,
        'categories': categories,  # Always defined
    })

def home(request):
    # Get current and future approved events
    today = timezone.now().date()
    last_month = today - timezone.timedelta(days=30)
    events = Event.objects.filter(status='Approved', date__gte=today)
    
    # Get events from last month
    last_month_events = Event.objects.filter(
        status='Approved',
        date__gte=last_month,
        date__lt=today
    ).order_by('-date')

    # Get user location only if user is authenticated and has a profile
    user_lat = None
    user_lon = None
    if request.user.is_authenticated:
        try:
            user_lat = request.user.profile.latitude
            user_lon = request.user.profile.longitude
        except:
            pass

    # Get trending events (top 5 by number of visits)
    trending_events = events.order_by('-visits')[:6]

    # Get recently added events (top 5 by date added)
    recently_added_events = events.order_by('-created_at')[:6]

     # Upcoming events (within the next month)
    upcoming_events = events.filter(date__gt=today, date__lte=today + timedelta(weeks=4))[:10]

    # Ongoing events (happening today or between start and end date)
    ongoing_events = events.filter(date__lte=today, end_date__gte=today)

    # Pass both lists to the template
    return render(request, 'events/home.html', {
        'events': events,
        'trending_events': trending_events,
        'recently_added_events': recently_added_events,
        'upcoming_events': upcoming_events,
        'ongoing_events': ongoing_events,
        'user_lat': user_lat,
        'user_lon': user_lon,
    })

def event_detail(request, event_id):
    # Fetch the event by ID
    event = get_object_or_404(Event, id=event_id)

    # Increment visits for the event
    event.visits += 1
    event.save()
    if request.user.is_authenticated:
        user=request.user
        # Update or create an EventUser record to mark it as visited
        event_user, created = EventUser.objects.get_or_create(user=user, event=event)
        event_user.visited = True
        event_user.save()



    # Get related event photos, old photos, and competitions
    event_photos = event.photos.all()
    old_photos = event.old_photos.all()
    competitions = event.competitions.all()
    categories = Category.objects.all()  # Fetch categories from the database


    # Pass all the data to the template
    return render(request, 'events/event_detail.html', {
        'event': event,
        'event_photos': event_photos,
        'old_photos': old_photos,
        'competitions': competitions,
        'categories': categories,
    })




def create_newsletter(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    word_limit = int(request.GET.get('word_limit', 250))  # Get word limit from GET request

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            edited_content = request.POST.get('edited_newsletter', '')

            # Convert plain text back to structured HTML paragraphs
            event.newsletter = f"<p>{edited_content.replace('\n', '</p><p>')}</p>"
            event.save()

            messages.success(request, 'Newsletter has been approved and saved.')
            return redirect('event_detail', event_id=event.id)

        elif action == 'reject':
            messages.warning(request, 'Newsletter generation was rejected.')
            return redirect('create_newsletter', event_id=event.id)

    # Generate newsletter using the word limit
    generated_newsletter = generate_newsletter(event, word_limit)
 

    return render(request, 'events/newsletter_detail.html', {
        'event': event,
        'newsletter_content': generated_newsletter
    })

def generate_newsletter(event, word_limit=250):
    content = f"""
    <h2>{event.name}</h2>
    <p><strong>Location:</strong> {event.place}</p>
    <p><strong>Date:</strong> {event.date}</p>
    <p><strong>Description:</strong> {event.description}</p>
    <p><strong>Don't miss out on this amazing event!</strong></p>
    <p>Generate a newsletter for the event with structured paragraphs, formatted like a newspaper.
    The content should be **limited to {word_limit} words.**</p>
    """

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(content)

    generated_newsletter = response.text

    return generated_newsletter  # No need to strip HTML here, it's done in the model method



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if username=='john':
                return redirect('dashboard_view_admin')
            else:
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


@login_required(login_url='/')  # Redirect to home page if not logged in
def profile_view(request):
    today = timezone.now().date()
    last_month = today - timezone.timedelta(days=30)
    
    # Get current and future events
    current_future_events = Event.objects.filter(
        status='Approved',
        date__gte=today
    )
    
    # Get events from last month
    recent_past_events = Event.objects.filter(
        status='Approved',
        date__gte=last_month,
        date__lt=today
    )
    
    # Get user location if profile exists
    user_latitude = None
    user_longitude = None
    try:
        user_latitude = request.user.profile.latitude
        user_longitude = request.user.profile.longitude
    except:
        pass
    
    # Get suggested events based on visited and bookmarked events
    visited_events = EventUser.objects.filter(user=request.user, visited=True).values_list('event', flat=True)
    bookmarked_events = EventUser.objects.filter(user=request.user, bookmarked=True).values_list('event', flat=True)
    
    # Get categories from visited and bookmarked events
    visited_categories = Event.objects.filter(id__in=visited_events).values_list('category', flat=True)
    bookmarked_categories = Event.objects.filter(id__in=bookmarked_events).values_list('category', flat=True)
    
    # Combine categories and remove duplicates
    user_categories = set(visited_categories) | set(bookmarked_categories)
    
    # Get suggested events (same category but not visited)
    suggested_events = current_future_events.filter(
        category__in=user_categories
    ).exclude(
        id__in=visited_events
    ).distinct()[:6]
    
    # Get nearby events if user location is available
    nearby_events = current_future_events
    if user_latitude and user_longitude:
        nearby_events = []
        for event in current_future_events:
            if event.latitude and event.longitude:
                distance = calculate_distance(
                    user_latitude, user_longitude,
                    event.latitude, event.longitude
                )
            if distance <= 50:  # Events within 50km
             nearby_events.append(event)
        nearby_events = nearby_events[:6]  # Limit to 6 events
    
    # Get trending events (based on views)
    trending_events = current_future_events.order_by('-visits')[:6]
    
    # Get recent events
    recent_events = current_future_events.order_by('date')[:6]
    
    # Get upcoming events
    upcoming_events = current_future_events.filter(date__gt=today).order_by('date')[:6]
    
    # Get ongoing events
    ongoing_events = current_future_events.filter(date=today)
    
    # Get recently visited events
    try:
        recently_visited_events = Event.objects.filter(
            id__in=request.user.profile.recently_visited_events.all(),
            date__gte=last_month
        ).order_by('-date')[:6]
    except:
        recently_visited_events = None
    
    context = {
        'events': current_future_events,
        'last_month_events': recent_past_events,
        'suggested_events': suggested_events,
        'nearby_events': nearby_events,
        'trending_events': trending_events,
        'recent_events': recent_events,
        'upcoming_events': upcoming_events,
        'ongoing_events': ongoing_events,
        'recently_visited_events': recently_visited_events,
        'user_latitude': user_latitude,
        'user_longitude': user_longitude,
    }
    
    return render(request, 'events/profile.html', context)

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
    event_user, created = EventUser.objects.get_or_create(user=user, event=event)
    if event in user.bookmarked_events.all():
        user.bookmarked_events.remove(event) 
        event_user.bookmarked = False # Remove bookmark
        bookmarked = False
    else:
        user.bookmarked_events.add(event)
        event_user.bookmarked = True  # Add bookmark
        bookmarked = True

    return JsonResponse({'bookmarked': bookmarked})
@login_required
def bookmarked_events(request):
    user = request.user
    events = user.bookmarked_events.all()  # Get all bookmarked events
    return render(request, 'events/bookmarked_events.html', {'events': events})
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from .forms import EventForm, EventPhotoForm, OldPhotoForm, CompetitionForm
from .models import Event, EventPhoto, OldPhoto, Competition
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect
from .forms import EventForm, EventPhotoForm, OldPhotoForm, CompetitionForm
from .models import Event, EventPhoto, OldPhoto, Competition

@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, user=request.user)

    if request.method == 'POST':
        print("POST request received")
        event_form = EventForm(request.POST, request.FILES, instance=event)
        competition_form = CompetitionForm(request.POST)
        
        if event_form.is_valid():
            print("Event form is valid")
            # Save event with pending status
            event = event_form.save(commit=False)
            event.status = 'pending'  # Set status to pending for admin review
            event.save()
            event_form.save_m2m()
            
            # Create notification for admin
            admin_user = User.objects.filter(username='john').first()
            if admin_user:
                Notification.objects.create(
                    user=admin_user,
                    message=f"{request.user.username} has edited the event: {event.name}. Please review the changes.",
                )
            
            # Handle competitions
            competitions_data = request.POST.getlist('competitions[][name]')
            if competitions_data:
                # Delete competitions marked for deletion
                delete_competitions = request.POST.getlist('delete_competition')
                for comp_id in delete_competitions:
                    if comp_id:
                        Competition.objects.filter(id=comp_id).delete()
                
                # Update or create competitions
                for i in range(len(competitions_data)):
                    competition_id = request.POST.getlist('competitions[][id]')[i]
                    if competition_id:
                        # Update existing competition
                        competition = Competition.objects.get(id=competition_id)
                        competition.name = competitions_data[i]
                        competition.date = request.POST.getlist('competitions[][date]')[i]
                        competition.place = request.POST.getlist('competitions[][place]')[i]
                        competition.description = request.POST.getlist('competitions[][description]')[i]
                        competition.save()
                    else:
                        # Create new competition
                        competition = Competition.objects.create(
                            event=event,
                            name=competitions_data[i],
                            date=request.POST.getlist('competitions[][date]')[i],
                            place=request.POST.getlist('competitions[][place]')[i],
                            description=request.POST.getlist('competitions[][description]')[i]
                        )
            
            # Handle photos
            event_photos = request.FILES.getlist('event_photos')
            old_photos = request.FILES.getlist('old_photos')
            
            # Delete photos marked for deletion
            delete_photos = request.POST.getlist('delete_photo')
            for photo_id in delete_photos:
                if photo_id:
                    EventPhoto.objects.filter(id=photo_id).delete()
            
            # Add new photos
            for photo in event_photos:
                EventPhoto.objects.create(event=event, image=photo)
            
            for old_photo in old_photos:
                OldPhoto.objects.create(event=event, image=old_photo)
            
            messages.success(request, "Event updated successfully! Waiting for admin approval.")
            return redirect('event_detail', event_id=event.id)
        else:
            print("Event form is not valid")
            messages.error(request, "Error: Please check your inputs.")
    
    else:
        event_form = EventForm(instance=event)
        competition_form = CompetitionForm()
    
    return render(request, 'events/edit_event.html', {
        'event_form': event_form,
        'competition_form': competition_form,
        'event': event,
    })



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
#approve or reject or pending

def is_admin(user):
    return user.username == 'john'

@login_required
def manage_events(request):
    if not is_admin(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
        
    # Fetch all events
    events = Event.objects.all()
    
    # Fetch pending events (both new and edited)
    pending_events = Event.objects.filter(status='pending').order_by('-updated_at')
    
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        action = request.POST.get('action')
        
        try:
            event = Event.objects.get(id=event_id)
            
            if action == 'approve':
                event.status = 'Approved'
                # Create notification for approval
                Notification.objects.create(
                    user=event.user,
                    message=f"Your event '{event.name}' has been approved.",
                )
                
                # If this was an edit, notify bookmarked users
                if event.status == 'pending':
                    bookmarked_users = event.bookmarked_by.all()
                    reminded_users = event.reminded_by.all()
                    
                    for user in bookmarked_users:
                        Notification.objects.create(
                            user=user,
                            message=f"The event '{event.name}' that you bookmarked has been updated.",
                        )
                    
                    for user in reminded_users:
                        Notification.objects.create(
                            user=user,
                            message=f"The event '{event.name}' that you set a reminder for has been updated.",
                )
                
            elif action == 'reject':
                event.status = 'Rejected'
                # Create notification for rejection
                Notification.objects.create(
                    user=event.user,
                    message=f"Your event '{event.name}' has been rejected.",
                )
                
            elif action == 'pending':
                event.status = 'Pending'
                # Create notification for pending status
                Notification.objects.create(
                    user=event.user,
                    message=f"Your event '{event.name}' has been marked as pending.",
                )
            
            event.save()
            messages.success(request, f"Event has been {action}d successfully.")
            
        except Event.DoesNotExist:
            messages.error(request, "Event not found.")
        except Exception as e:
            messages.error(request, f"Error processing request: {str(e)}")
    
    return render(request, 'events/manage_events.html', {
        'events': events,
        'pending_events': pending_events,
    })

@login_required
def approve_event_edit(request, event_id):
    if not is_admin(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
        
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            # Update event status
            event.status = 'approved'
            event.save()
            
            # Create notification for event creator
            Notification.objects.create(
                user=event.user,
                message=f"Your edit request for event '{event.name}' has been approved.",
            )
            
            # Notify users who bookmarked or reminded the event
            bookmarked_users = event.bookmarked_by.all()
            reminded_users = event.reminded_by.all()
            
            for user in bookmarked_users:
                Notification.objects.create(
                    user=user,
                    message=f"The event '{event.name}' that you bookmarked has been updated.",
                )
            
            for user in reminded_users:
                Notification.objects.create(
                    user=user,
                    message=f"The event '{event.name}' that you set a reminder for has been updated.",
                )
            
            messages.success(request, "Event edit approved successfully!")
            
        elif action == 'reject':
            # Revert event to previous state
            event.status = 'rejected'
            event.save()
            
            # Create notification for event creator
            Notification.objects.create(
                user=event.user,
                message=f"Your edit request for event '{event.name}' has been rejected.",
            )
            
            messages.warning(request, "Event edit rejected.")
        
        return redirect('manage_events')
    
    return render(request, 'events/admin/approve_event_edit.html', {
        'event': event,
    })

@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
        
    # Get all events
    events = Event.objects.all()
    
    # Get pending events
    pending_events = Event.objects.filter(status='pending').order_by('-updated_at')
    
    # Get category counts
    categories_count = (
        Event.objects.values('category__name')
        .annotate(count=Count('id'))
        .order_by('category__name')
    )
    
    # Prepare events data for charts
    events_data = []
    for event in events:
        events_data.append({
            'name': event.name,
            'date': event.date.strftime('%Y-%m-%d'),
            'category': event.category.first().name if event.category.exists() else 'Uncategorized',
            'visits': event.visits
        })
    
    context = {
        'events': events,
        'pending_events': pending_events,
        'categories_count': categories_count,
        'events_data': json.dumps(events_data),
        'category_labels': [item['category__name'] for item in categories_count],
    }
    return render(request, 'events/dashboard.html', context)

@login_required
def notifications(request):
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        action = request.POST.get('action')
        
        if notification_id:
            notification = get_object_or_404(Notification, id=notification_id, user=request.user)
            
            if action == 'mark_read':
                notification.is_read = True
                notification.save()
                return JsonResponse({'status': 'success'})
            elif action == 'remove':
                notification.delete()
                return JsonResponse({'status': 'success'})
    
    # Get notifications for the current user
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Different categorization based on user type
    if is_admin(request.user):
        # For admin: Show new event requests and edit requests
        new_event_notifications = notifications.filter(message__icontains='has requested to add an event')
        edit_notifications = notifications.filter(message__icontains='has edited the event')
        status_notifications = None
    else:
        # For regular users: Show status changes of their events and bookmarked/reminded events
        new_event_notifications = None
        edit_notifications = None
        status_notifications = notifications.filter(
            Q(message__icontains='has been approved') |
            Q(message__icontains='has been rejected') |
            Q(message__icontains='has been updated')
        )
    
    context = {
        'new_event_notifications': new_event_notifications,
        'edit_notifications': edit_notifications,
        'status_notifications': status_notifications,
        'is_admin': is_admin(request.user)
    }
    
    return render(request, 'events/notifications.html', context)

def check_login_status(request):
    """Check if the user is logged in and return their status"""
    if request.user.is_authenticated:
        return JsonResponse({
            'is_logged_in': True,
            'username': request.user.username,
            'is_admin': is_admin(request.user)
        })
    return JsonResponse({
        'is_logged_in': False,
        'username': None,
        'is_admin': False
    })

@login_required
def mark_notification_as_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)

def search_events(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    date = request.GET.get('date', '')
    sort_by = request.GET.get('sort', 'newest')  # Default sort by newest

    events = Event.objects.filter(status='Approved')

    if query:
        events = events.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    if category:
        events = events.filter(category__id=category)

    if location:
        events = events.filter(place__icontains=location)

    if date:
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            events = events.filter(date=date_obj)
        except ValueError:
            pass

    # Apply sorting
    if sort_by == 'newest':
        events = events.order_by('-created_at')
    elif sort_by == 'oldest':
        events = events.order_by('created_at')
    elif sort_by == 'date':
        events = events.order_by('date')
    elif sort_by == 'name_asc':
        # Case-insensitive sorting for name ascending
        events = sorted(events, key=lambda x: x.name.lower())
    elif sort_by == 'name_desc':
        # Case-insensitive sorting for name descending
        events = sorted(events, key=lambda x: x.name.lower(), reverse=True)
    elif sort_by == 'visits':
        events = events.order_by('-visits')

    # Get all categories for the filter dropdown
    categories = Category.objects.all()
    
    context = {
        'events': events,
        'query': query,
        'category': category,
        'location': location,
        'date': date,
        'sort_by': sort_by,
        'categories': categories,
    }
    
    return render(request, 'events/search_results.html', context)

def notify_user(user, event, status):
    """Send email notification to user about event status changes"""
    subject = f'Event Status Update: {event.name}'
    
    if status == 'Approved':
        message = f'''
        Dear {user.username},

        Your event "{event.name}" has been approved and is now visible on our platform.

        Event Details:
        - Name: {event.name}
        - Date: {event.date}
        - Location: {event.place}
        - Description: {event.description}

        You can view your event here: http://127.0.0.1:8000/events/{event.id}/

        Best regards,
        Event Organizer Team
        '''
    elif status == 'Rejected':
        message = f'''
        Dear {user.username},

        We regret to inform you that your event "{event.name}" has been rejected.

        Event Details:
        - Name: {event.name}
        - Date: {event.date}
        - Location: {event.place}

        If you have any questions about this decision, please contact our support team.

        Best regards,
        Event Organizer Team
        '''
    else:  # Pending
        message = f'''
        Dear {user.username},

        Your event "{event.name}" is currently pending review.

        Event Details:
        - Name: {event.name}
        - Date: {event.date}
        - Location: {event.place}
        - Description: {event.description}

        We will review your event and notify you once a decision has been made.

        Best regards,
        Event Organizer Team
        '''

    try:
        send_mail(
            subject,
            message,
            'festfeed00@gmail.com',  # Using the same email as in signup_view
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    """Send OTP to user's email"""
    subject = 'Password Reset OTP'
    message = f'''
    Dear User,

    Your OTP for password reset is: {otp}

    This OTP will expire in 10 minutes.

    If you didn't request this password reset, please ignore this email.

    Best regards,
    Event Organizer Team
    '''
    
    try:
        send_mail(
            subject,
            message,
            'festfeed00@gmail.com',
            [email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def forgot_password(request):
    """Handle forgot password request"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generate OTP
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Store OTP in cache for 5 minutes
            cache_key = f'reset_otp_{email}'
            cache.set(cache_key, otp, 300)  # 300 seconds = 5 minutes
            
            # Send OTP via email
            subject = 'Password Reset OTP'
            message = f'Your OTP for password reset is: {otp}. This OTP will expire in 5 minutes.'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]
            
            send_mail(subject, message, from_email, recipient_list)
            
            messages.success(request, 'OTP has been sent to your email.')
            return redirect('verify_otp', email=email)
        except User.DoesNotExist:
            messages.error(request, 'No user found with this email address.')
    
    return render(request, 'events/forgot_password.html')

def verify_otp(request, email):
    """Verify OTP and show password reset form"""
    if not email:
        return redirect('forgot_password')
    
    if request.method == 'POST':
        otp = request.POST.get('otp')
        cache_key = f'reset_otp_{email}'
        stored_otp = cache.get(cache_key)
        
        if stored_otp and otp == stored_otp:
            # OTP is valid, redirect to reset password page with email
            return redirect('reset_password', email=email)
        else:
            messages.error(request, 'Invalid or expired OTP. Please try again.')
    
    return render(request, 'events/verify_otp.html', {'email': email})

def reset_password(request, email):
    """Handle password reset"""
    if not email:
        print("No email provided")
        return redirect('forgot_password')
    
    if request.method == 'POST':
        print("POST request received")  
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if not password or not confirm_password:
            messages.error(request, 'Both password fields are required.')
            return render(request, 'events/reset_password.html', {'email': email})
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match. Please try again.')
            return render(request, 'events/reset_password.html', {'email': email})
        
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'events/reset_password.html', {'email': email})
        
        try:
            print("Resetting password for user:", email)
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            
            # Clear the OTP from cache
            cache_key = f'reset_otp_{email}'
            cache.delete(cache_key)
            print("Password reset successfully")
            messages.success(request, 'Password has been reset successfully. Please login with your new password.')
            return redirect('login_view')
        except User.DoesNotExist:
            print("User not found")
            messages.error(request, 'User not found.')
            return redirect('forgot_password')
    
    return render(request, 'events/reset_password.html', {'email': email})




