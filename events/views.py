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
from django.db.models import Sum
from .models import Notification
from datetime import timedelta
from django.utils import timezone

genai.configure(api_key="AIzaSyBx731nHQN7dUUT4sAodinK09LmWu5RGRY")


from django.shortcuts import render
from django.db.models import Sum

@login_required
def notifications_list(request):
    notifications = request.user.notifications.all().order_by('-created_at')
    return render(request, 'events/notifications.html', {'notifications': notifications})

@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications_list')


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
            
            Notification.objects.create(
                message=f"New event request: {event.name} by {request.user}"
            )
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
    events = Event.objects.filter(status='Approved')

    # Get trending events (top 5 by number of visits)
    trending_events = events.order_by('-visits')[:6]

    # Get recently added events (top 5 by date added)
    recently_added_events = events.order_by('-created_at')[:6]

     # Upcoming events (within the next month)
    today = timezone.now().date()

    # Upcoming events within the next month (combined)
    upcoming_events = events.filter(date__gt=today, date__lte=today + timedelta(weeks=4))[:10]  # Limit to 10 events

    # Ongoing events (happening today or between start and end date)
    ongoing_events = events.filter(date__lte=today, end_date__gte=today)

    # Pass both lists to the template
    return render(request, 'events/home.html', {
        'events': events,
        'trending_events': trending_events,
        'recently_added_events': recently_added_events,
        'upcoming_events': upcoming_events,  # Pass the merged upcoming events
        'ongoing_events': ongoing_events,
    })

def event_detail(request, event_id):
    # Fetch the event by ID
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    # Increment visits for the event
    event.visits += 1
    event.save()

    # Update or create an EventUser record to mark it as visited
    event_user, created = EventUser.objects.get_or_create(user=user, event=event)
    event_user.visited = True
    event_user.save()



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


@login_required
def profile_view(request):
    user = request.user
    events = Event.objects.filter(status='Approved')

    # Get user location
    user_lat = user.profile.latitude
    user_lon = user.profile.longitude

    # Fetch all events visited by the user
    visited_events = EventUser.objects.filter(user=user, visited=True).values_list('event', flat=True)

    # Fetch all events bookmarked by the user
    bookmarked_events = EventUser.objects.filter(user=user, bookmarked=True).values_list('event', flat=True)

    # Get the categories and places for visited events
    visited_categories = Event.objects.filter(id__in=visited_events).values_list('category', flat=True)
    visited_places = Event.objects.filter(id__in=visited_events).values_list('place', flat=True)

    # Get the categories and places for bookmarked events
    bookmarked_categories = Event.objects.filter(id__in=bookmarked_events).values_list('category', flat=True)
    bookmarked_places = Event.objects.filter(id__in=bookmarked_events).values_list('place', flat=True)

    # Combine all the categories and places from visited and bookmarked events
    categories = set(visited_categories) | set(bookmarked_categories)
    places = set(visited_places) | set(bookmarked_places)   

    # Separate lists for suggested and nearby events
    suggested_events = []
    nearby_events = []

    for event in events:
        # Calculate distance only if the user's location and event's location are available
        distance = calculate_distance(user_lat, user_lon, event.latitude, event.longitude) if user_lat and user_lon else None

        if distance and distance <= 50:
          nearby_events.append(event)

        # Exclude events already visited
        if event.id in visited_events:
            continue

        # Add to suggested_events based on category or place
        if event.category in categories or event.place in places:
            suggested_events.append(event)
        
    # Get trending and recent events
    trending_events = events.order_by('-visits')[:6]
    recent_events = events.order_by('-created_at')[:6]
    print(nearby_events)    

    # Upcoming events (within the next month)
    today = timezone.now().date()

    # Upcoming events within the next month (combined)
    upcoming_events = events.filter(date__gt=today, date__lte=today + timedelta(weeks=4))[:10]  # Limit to 10 events

    # Ongoing events (happening today or between start and end date)
    ongoing_events = events.filter(date__lte=today, end_date__gte=today)

    # Recently visited events (limit to most recent visits)
    recent_visited_events = Event.objects.filter(id__in=visited_events).order_by('-eventuser__created_at')[:6]

    return render(request, 'events/profile.html', {
        'user': user,
        'events':events,
        'nearby_events': nearby_events,
        'suggested_events': suggested_events,
        'trending_events': trending_events,
        'recent_events': recent_events,
        'upcoming_events': upcoming_events,  # Pass the merged upcoming events
        'ongoing_events': ongoing_events,
        'recent_visited_events': recent_visited_events,
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
from django.shortcuts import render
from .models import Event
from django.db.models import Count

def dashboard_view(request):
    CATEGORY_CHOICES = [
        ('cultural', 'Cultural'),
        ('Music', 'Music'),
        ('Sports', 'Sports'),
        ('Art', 'Art'),
        ('Tech', 'Tech'),
        ('Food', 'Food'),
    ]
    category_labels = []
    for category_key, category_label in CATEGORY_CHOICES:
        category_labels.append(category_label)
        
    # Example: count events by category
    categories_count = Event.objects.filter(status='Approved').values('category').annotate(count=Count('category'))
    

    events_data = list(
        Event.objects.filter(status='Approved').values('date', 'visits', 'category')
        .annotate(event_count=Count('name'))
        .order_by('date')
    )
    for event in events_data:
        event['date'] = event['date'].isoformat()
    # Example: total visits of events
    total_visits = Event.objects.filter(status='Approved').aggregate(total_visits=Sum('visits'))
    
    # Get all events and their view count for the pie chart
    events = Event.objects.filter(status='Approved').values('name', 'visits')  # Assuming 'visits' is the field tracking event views
    
    context = {
        'categories_count': categories_count,
        'total_visits': total_visits,
        'events': events,  # Adding events data for the pie chart
        'category_labels': category_labels,
        'events_data': json.dumps(list(events_data)),
    }
    
    return render(request, 'events/dashboard.html', context)



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Event
from django.http import HttpResponse

# View to approve selected events
def approve_events(request):
    if request.method == 'POST':
        event_ids = request.POST.getlist('event_ids')  # Get the list of event IDs from the form
        events = Event.objects.filter(id__in=event_ids)
        events.update(status='approved')  # Approve selected events
        
        messages.success(request, "Selected events have been approved.")
        return redirect('events_dashboard')  # Redirect to an appropriate page (e.g., events dashboard)

# View to reject selected events
def reject_events(request):
    if request.method == 'POST':
        event_ids = request.POST.getlist('event_ids')  # Get the list of event IDs from the form
        events = Event.objects.filter(id__in=event_ids)
        events.update(status='rejected')  # Reject selected events
        
        messages.success(request, "Selected events have been rejected.")
        return redirect('events_dashboard')

# View to approve event changes
def approve_changes(request):
    if request.method == 'POST':
        event_ids = request.POST.getlist('event_ids')  # Get the list of event IDs from the form
        events = Event.objects.filter(id__in=event_ids)
        events.update(requested_approval=False, status='approved')  # Approve changes for selected events
        
        messages.success(request, "Selected events' changes have been approved.")
        return redirect('events_dashboard')

# View to reject event changes
def reject_changes(request):
    if request.method == 'POST':
        event_ids = request.POST.getlist('event_ids')  # Get the list of event IDs from the form
        events = Event.objects.filter(id__in=event_ids)
        events.update(requested_approval=False, status='rejected')  # Reject changes for selected events
        
        messages.success(request, "Selected events' changes have been rejected.")
        return redirect('events_dashboard')

# View to approve event deletion
def approve_deletion(request):
    if request.method == 'POST':
        event_ids = request.POST.getlist('event_ids')  # Get the list of event IDs from the form
        events = Event.objects.filter(id__in=event_ids)
        events.update(delete_requested=False, status='deleted')  # Approve deletion for selected events
        
        for event in events:
            event.delete()  # Delete the events

        messages.success(request, "Selected events have been deleted.")
        return redirect('events_dashboard')

# View to reject event deletion
def reject_deletion(request):
    if request.method == 'POST':
        event_ids = request.POST.getlist('event_ids')  # Get the list of event IDs from the form
        events = Event.objects.filter(id__in=event_ids)
        events.update(delete_requested=False, status='active')  # Reject deletion for selected events
        
        messages.success(request, "Selected events' deletion has been rejected.")
        return redirect('events_dashboard')
    
from django.shortcuts import render, get_object_or_404
from .models import Event



