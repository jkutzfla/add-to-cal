from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os.path
import pickle
import json
import re
import sys

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def parse_event_info(event_info_str):
    """Parse the event information string into a structured format."""
    lines = event_info_str.split('\n')
    event_data = {}
    
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if value and value != "Not specified":
                event_data[key] = value
    
    return event_data

def parse_datetime(date_str, time_str):
    """Parse date and time strings into datetime object."""
    if not date_str or not time_str:
        return None
    
    try:
        # Handle various date formats
        date_formats = [
            "%A, %B %d",  # Thursday, April 10
            "%B %d, %Y",  # April 10, 2024
            "%Y-%m-%d"    # 2024-04-10
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if not parsed_date:
            return None
            
        # Add current year if not present
        if parsed_date.year == 1900:
            current_year = datetime.now().year
            parsed_date = parsed_date.replace(year=current_year)
        
        # Parse time
        time_formats = [
            "%I:%M %p",  # 7:00 PM
            "%H:%M"      # 19:00
        ]
        
        parsed_time = None
        for fmt in time_formats:
            try:
                parsed_time = datetime.strptime(time_str, fmt)
                break
            except ValueError:
                continue
                
        if not parsed_time:
            return None
            
        return datetime.combine(parsed_date.date(), parsed_time.time())
        
    except Exception as e:
        print(f"Error parsing datetime: {e}")
        return None

def get_google_calendar_service():
    """Get or create Google Calendar API service."""
    creds = None
    
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

def create_calendar_event(event_data):
    """Create an event in Google Calendar."""
    try:
        service = get_google_calendar_service()
        
        # Parse start and end times
        start_datetime = parse_datetime(event_data.get('Event Date'), 
                                     event_data.get('Event Start Time'))
        end_datetime = parse_datetime(event_data.get('Event Date'), 
                                   event_data.get('Event End Time'))
        
        if not start_datetime:
            raise ValueError("Could not parse event start time")
            
        if not end_datetime:
            # If no end time, make it an hour-long event
            end_datetime = start_datetime.replace(hour=start_datetime.hour + 1)
        
        event = {
            'summary': event_data.get('Event Title', 'Untitled Event'),
            'location': event_data.get('Event Location', ''),
            'description': event_data.get('Event Description', ''),
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'America/New_York',  # Adjust timezone as needed
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/New_York',  # Adjust timezone as needed
            },
        }
        
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f'Event created: {event.get("htmlLink")}')
        return event
        
    except Exception as e:
        print(f"Error creating calendar event: {e}")
        return None

def main():
    # Load environment variables
    load_dotenv()
    # Import the event extraction functions
    from load_page import get_webpage_content, extract_event_info
    
    # Get URL from command line
    if len(sys.argv) != 2:
        print("Usage: python save_to_calendar.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Get webpage content and extract event info
    content = get_webpage_content(url)
    event_info_str = extract_event_info(content)
    
    # Parse the event information
    event_data = parse_event_info(event_info_str)
    
    # Create the calendar event
    create_calendar_event(event_data)

if __name__ == "__main__":
    main() 