from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .models import GoogleCredentials
from django.conf import settings
from datetime import datetime
import os
import pytz



def format_datetime(date_str, time_str, timezone='US/Central'):
    datetime_str = f"{date_str}T{time_str}:00"
    naive_datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
    central_tz = pytz.timezone(timezone)
    aware_datetime = central_tz.localize(naive_datetime)
    iso_datetime_str = aware_datetime.isoformat()
    return iso_datetime_str


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Disable OAuthlib's HTTPS verification for local testing



def calendar_home_view(request):
    context = {}
    return render(request, 'calendar_home.html', context)



@login_required
def authorize(request):
    flow = Flow.from_client_config(
        settings.CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events'],
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    request.session['state'] = state
    return redirect(authorization_url)



@login_required
def oauth2callback(request):
    flow = Flow.from_client_config(
        settings.CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events'],
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials

    google_credentials, created = GoogleCredentials.objects.get_or_create(user=request.user)
    google_credentials.token = credentials.token
    google_credentials.refresh_token = credentials.refresh_token
    google_credentials.token_uri = credentials.token_uri
    google_credentials.client_id = credentials.client_id
    google_credentials.client_secret = credentials.client_secret
    google_credentials.scopes = ','.join(credentials.scopes)
    google_credentials.save()
    return redirect('list-calendars')



def add_event(event_data, user):

    google_credentials = GoogleCredentials.objects.get(user=user)

    credentials = Credentials(
        token=google_credentials.token,
        refresh_token=google_credentials.refresh_token,
        token_uri=google_credentials.token_uri,
        client_id=google_credentials.client_id,
        client_secret=google_credentials.client_secret,
        scopes=google_credentials.scopes.split(',')
    )

    try:
        service = build('calendar', 'v3', credentials=credentials)
        event = {
            'summary': event_data["summary"],
            'location': event_data["location"],
            'description': event_data["description"],
            'start': {'dateTime': event_data["formatted_start_time"], 'timeZone': 'America/Chicago'},
            'end': {'dateTime': event_data["formatted_end_time"], 'timeZone': 'America/Chicago'},
            'attendees': event_data["attendees"],
            # 'reminders': {'useDefault': False, 'overrides': [{'method': 'email', 'minutes': 24 * 60}, {'method': 'popup', 'minutes': 10}]},
        }
        event = service.events().insert(calendarId='c_6ebd154264cad716ba35a00bd0a9d64c378b091814b371d3a6d0c704ac5e3097@group.calendar.google.com', body=event).execute()

        google_credentials.token = credentials.token
        google_credentials.refresh_token = credentials.refresh_token
        google_credentials.token_uri = credentials.token_uri
        google_credentials.client_id = credentials.client_id
        google_credentials.client_secret = credentials.client_secret
        google_credentials.scopes = ','.join(credentials.scopes)
        google_credentials.save()
        return
    except HttpError as error:
        print("Error adding event:", error)
        return



def list_calendars(request):
    google_credentials = GoogleCredentials.objects.get(user=request.user)

    credentials = Credentials(
        token=google_credentials.token,
        refresh_token=google_credentials.refresh_token,
        token_uri=google_credentials.token_uri,
        client_id=google_credentials.client_id,
        client_secret=google_credentials.client_secret,
        scopes=google_credentials.scopes.split(',')
    )
    service = build('calendar', 'v3', credentials=credentials)
    calendar_list = service.calendarList().list().execute()
    calendars = calendar_list.get('items', [])
    return render(request, 'list_calendars.html', {'calendars': calendars})



def add_event_page(request):

    if request.method == 'POST':
        summary = request.POST.get('summary')
        location = request.POST.get('location')
        description = request.POST.get('description')
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        attendees = request.POST.getlist('attendees')

        attendee_list = []
        for attendee in attendees:
            email = {"email":attendee}
            attendee_list.append(email)
    
        event_data = {
                "summary":summary,
                "location":location,
                "description":description,
                "date":date,
                "start_time":start_time,
                "end_time":end_time,
                "attendees":attendee_list,
                "formatted_start_time": format_datetime(date, start_time),
                "formatted_end_time": format_datetime(date, end_time)
        }

        user = request.user

        add_event(event_data, user)

        print("event_data", event_data)
  
        return redirect('add-event')

    context= {}
    return render(request, 'add_event.html', context)