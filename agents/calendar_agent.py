import os
import pickle
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pytz
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class CalendarAgent:
    """Production-ready Google Calendar agent with smart time parsing"""

    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self):
        self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        self.service = None
        self.creds = None
        self.timezone = pytz.timezone('Asia/Kolkata')

    async def initialize(self):
        """Initialize Google Calendar service"""
        try:
            if os.path.exists('calendar_token.pickle'):
                with open('calendar_token.pickle', 'rb') as token:
                    self.creds = pickle.load(token)

            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    try:
                        self.creds.refresh(Request())
                    except Exception:
                        if os.path.exists('calendar_token.pickle'):
                            os.remove('calendar_token.pickle')
                        self.creds = None

                if not self.creds:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path,
                        self.SCOPES
                    )
                    self.creds = flow.run_local_server(host='localhost', port=8000)

                with open('calendar_token.pickle', 'wb') as token:
                    pickle.dump(self.creds, token)

            self.service = build('calendar', 'v3', credentials=self.creds)
            logger.info("✅ Google Calendar connected")
            return True

        except Exception as e:
            logger.error(f"❌ Calendar init error: {e}")
            return False

    def _smart_default_time(self, text: str, date: datetime.date) -> tuple:
        """
        Intelligently determine default time based on event context
        Returns (hour, minute) tuple
        """
        text_lower = text.lower()
        
        # Morning events (6 AM - 11:59 AM)
        morning_keywords = ['breakfast', 'morning', 'early', 'sunrise', 'gym', 'workout', 'jog', 'coffee']
        if any(kw in text_lower for kw in morning_keywords):
            return (9, 0)  # 9:00 AM
        
        # Afternoon events (12 PM - 5 PM)
        afternoon_keywords = ['lunch', 'afternoon', 'matinee', 'noon']
        if any(kw in text_lower for kw in afternoon_keywords):
            return (13, 0)  # 1:00 PM
        
        # Evening events (5 PM - 9 PM)
        evening_keywords = ['dinner', 'evening', 'night', 'drinks', 'party', 'movie', 'show']
        if any(kw in text_lower for kw in evening_keywords):
            return (19, 0)  # 7:00 PM
        
        # Late night events (9 PM - 11:59 PM)
        late_keywords = ['late', 'midnight', 'club', 'bar']
        if any(kw in text_lower for kw in late_keywords):
            return (21, 0)  # 9:00 PM
        
        # Business/work events default to 10 AM
        work_keywords = ['meeting', 'call', 'conference', 'presentation', 'review', 'sync', 'standup']
        if any(kw in text_lower for kw in work_keywords):
            return (10, 0)  # 10:00 AM
        
        # Default: 10:00 AM for general events
        return (10, 0)

    def parse_datetime_from_text(self, text: str) -> tuple:
        """
        Parse date, time, and duration from text with smart defaults
        Returns: (start_dt, end_dt, is_all_day)
        """

        text_lower = text.lower()
        now = datetime.now(self.timezone)

        # Defaults
        start_date = now.date()
        start_hour = None  # Will remain None if no time is found
        start_minute = 0
        duration_hours = 1
        date_found = False
        time_explicitly_mentioned = False
        is_all_day = False

        # Check for all-day event keywords FIRST
        allday_keywords = ['all day', 'full day', 'entire day', 'whole day', 
                          'trip', 'vacation', 'holiday', 'day off', 
                          'birthday', 'anniversary', 'visit']
        if any(kw in text_lower for kw in allday_keywords):
            is_all_day = True
            logger.info("🗓️ Detected all-day event keywords")

        # ===== DATE PARSING (PRIORITY ORDER) =====
        
        # 1. Specific dates: "25 Nov", "Nov 25", "25 November", "November 25", "25/11", "11/25"
        month_names = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
            'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
            'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
            'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
        }
        
        # Pattern: "25 Nov" or "Nov 25" or "25 November" or "November 25"
        for month_name, month_num in month_names.items():
            # Day Month format: "25 Nov"
            pattern = rf'\b(\d{{1,2}})\s+{month_name}\b'
            match = re.search(pattern, text_lower)
            if match:
                day = int(match.group(1))
                year = now.year
                try:
                    parsed_date = datetime(year, month_num, day).date()
                    if parsed_date < now.date():
                        year += 1
                        parsed_date = datetime(year, month_num, day).date()
                    start_date = parsed_date
                    date_found = True
                    logger.info(f"📅 Parsed specific date: {start_date}")
                    break
                except ValueError:
                    continue
            
            # Month Day format: "Nov 25"
            pattern = rf'\b{month_name}\s+(\d{{1,2}})\b'
            match = re.search(pattern, text_lower)
            if match:
                day = int(match.group(1))
                year = now.year
                try:
                    parsed_date = datetime(year, month_num, day).date()
                    if parsed_date < now.date():
                        year += 1
                        parsed_date = datetime(year, month_num, day).date()
                    start_date = parsed_date
                    date_found = True
                    logger.info(f"📅 Parsed specific date: {start_date}")
                    break
                except ValueError:
                    continue
        
        # Pattern: "25/11" or "11/25" or "25-11" or "11-25"
        if not date_found:
            date_patterns = [
                r'\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b',
            ]
            for pattern in date_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    num1 = int(match.group(1))
                    num2 = int(match.group(2))
                    year_match = match.group(3)
                    year = now.year if not year_match else (int(year_match) if len(year_match) == 4 else 2000 + int(year_match))
                    
                    # Try DD/MM first (more common internationally)
                    try:
                        parsed_date = datetime(year, num2, num1).date()
                        if parsed_date < now.date() and not year_match:
                            year += 1
                            parsed_date = datetime(year, num2, num1).date()
                        start_date = parsed_date
                        date_found = True
                        logger.info(f"📅 Parsed date (DD/MM): {start_date}")
                        break
                    except ValueError:
                        try:
                            parsed_date = datetime(year, num1, num2).date()
                            if parsed_date < now.date() and not year_match:
                                year += 1
                                parsed_date = datetime(year, num1, num2).date()
                            start_date = parsed_date
                            date_found = True
                            logger.info(f"📅 Parsed date (MM/DD): {start_date}")
                            break
                        except ValueError:
                            continue
        
        # 2. Relative dates (only if no specific date found)
        if not date_found:
            if "today" in text_lower:
                start_date = now.date()
                date_found = True
            elif "tomorrow" in text_lower:
                start_date = (now + timedelta(days=1)).date()
                date_found = True
            elif "next week" in text_lower:
                start_date = (now + timedelta(days=7)).date()
                date_found = True
            elif any(day in text_lower for day in ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']):
                days_map = {'monday':0,'tuesday':1,'wednesday':2,'thursday':3,'friday':4,'saturday':5,'sunday':6}
                for day_name, day_num in days_map.items():
                    if day_name in text_lower:
                        current_day = now.weekday()
                        days_ahead = (day_num - current_day + 7) % 7
                        days_ahead = days_ahead if days_ahead != 0 else 7
                        start_date = (now + timedelta(days=days_ahead)).date()
                        date_found = True
                        break

        # ===== TIME PARSING =====
        # Only parse time if not explicitly an all-day event
        if not is_all_day:
            time_patterns = [
                (r'\b(\d{1,2})\s*(am|pm)\b', 'simple'),
                (r'\b(\d{1,2}):(\d{2})\s*(am|pm)\b', 'detailed'),
                (r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b', 'at_prefix'),
                (r'\b([01]?[0-9]|2[0-3]):([0-5][0-9])\b', '24hour'),
            ]

            for pattern, ptype in time_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    time_explicitly_mentioned = True
                    try:
                        if ptype == 'simple':
                            hour = int(match.group(1))
                            minute = 0
                            period = match.group(2)
                            if period == 'pm' and hour != 12:
                                hour += 12
                            elif period == 'am' and hour == 12:
                                hour = 0
                            start_hour = hour
                            start_minute = minute
                            break
                        elif ptype in ['detailed', 'at_prefix']:
                            hour = int(match.group(1))
                            minute = int(match.group(2) or 0)
                            period = match.group(3)
                            if period == 'pm' and hour != 12:
                                hour += 12
                            elif period == 'am' and hour == 12:
                                hour = 0
                            start_hour = hour
                            start_minute = minute
                            break
                        elif ptype == '24hour':
                            start_hour = int(match.group(1))
                            start_minute = int(match.group(2))
                            break
                    except Exception as e:
                        logger.warning(f"⚠️ Time parse error: {e}")

        # ===== DETERMINE IF ALL-DAY EVENT =====
        # If no time was explicitly mentioned and no time-specific keywords, treat as all-day
        if start_hour is None and not time_explicitly_mentioned:
            # Check if there are time-specific keywords that suggest a timed event
            time_specific_keywords = ['meeting', 'call', 'conference', 'presentation', 
                                     'breakfast', 'lunch', 'dinner', 'coffee',
                                     'movie', 'show', 'party', 'gym', 'workout']
            
            has_time_context = any(kw in text_lower for kw in time_specific_keywords)
            
            if not has_time_context:
                is_all_day = True
                logger.info("🗓️ No time mentioned and no time-specific context - creating all-day event")
            else:
                # Use smart default time only if there's time-specific context
                start_hour, start_minute = self._smart_default_time(text, start_date)
                logger.info(f"⏰ Using smart default time: {start_hour}:{start_minute:02d} (context-based)")
        elif start_hour is not None:
            logger.info(f"⏰ Using explicitly mentioned time: {start_hour}:{start_minute:02d}")

        # ===== DURATION PARSING =====
        if not is_all_day:
            duration_patterns = [
                (r'(\d+)\s*hour', 'hours'), 
                (r'(\d+)\s*hr', 'hours'),
                (r'(\d+)\s*minute', 'minutes'), 
                (r'(\d+)\s*min', 'minutes')
            ]
            for pattern, unit in duration_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    value = int(match.group(1))
                    if unit == 'hours':
                        duration_hours = value
                    elif unit == 'minutes':
                        duration_hours = value / 60
                    break

        # ===== COMBINE DATE + TIME =====
        if is_all_day:
            # For all-day events, return just the date (no time component)
            logger.info(f"📆 Final: All-day event on {start_date}")
            return start_date, None, True
        else:
            start_dt = datetime.combine(start_date, datetime.min.time()).replace(hour=start_hour, minute=start_minute)
            start_dt = self.timezone.localize(start_dt)
            end_dt = start_dt + timedelta(hours=duration_hours)
            logger.info(f"📆 Final: {start_dt.strftime('%Y-%m-%d %I:%M %p')} → {end_dt.strftime('%I:%M %p')}")
            return start_dt, end_dt, False

    async def create_event(
        self,
        title: str,
        start_time: datetime = None,
        end_time: datetime = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        original_text: str = None,
        reminders: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict:
        """Create calendar event with smart time handling"""

        if not self.service:
            return {"success": False, "error": "Calendar not connected", "mock": True}

        is_all_day = False
        
        # Parse time if text provided
        if original_text:
            parsed_result = self.parse_datetime_from_text(original_text)
            start_time, end_time, is_all_day = parsed_result

        # Fallback times for timed events
        if not is_all_day and not start_time:
            start_time = datetime.now(self.timezone) + timedelta(hours=1)
            end_time = start_time + timedelta(hours=1)

        # Build event object based on whether it's all-day or timed
        if is_all_day:
            # All-day events use 'date' instead of 'dateTime'
            event = {
                'summary': title,
                'start': {'date': start_time.isoformat()},
                'end': {'date': (start_time + timedelta(days=1)).isoformat()},
            }
        else:
            # Timed events use 'dateTime'
            event = {
                'summary': title,
                'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
                'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
            }
        
        if description:
            event['description'] = description
        if location:
            event['location'] = location
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]

        # Only add reminders for timed events
        if not is_all_day:
            if reminders and isinstance(reminders, list):
                event['reminders'] = {'useDefault': False, 'overrides': reminders}
            else:
                event['reminders'] = {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 10}]}

        try:
            created = self.service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='none'
            ).execute()

            if is_all_day:
                logger.info(f"✅ All-day event created: {title} on {start_time}")
            else:
                logger.info(f"✅ Event created: {title} at {start_time.strftime('%d %b %Y, %I:%M %p')}")
            
            return {
                "success": True,
                "event_id": created['id'],
                "title": title,
                "start": start_time.isoformat() if is_all_day else start_time.isoformat(),
                "end": (start_time + timedelta(days=1)).isoformat() if is_all_day else end_time.isoformat(),
                "is_all_day": is_all_day,
                "link": created.get('htmlLink')
            }

        except Exception as e:
            logger.error(f"❌ Event creation failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_events(self, start_time: datetime, end_time: datetime, max_results: int = 100) -> List[Dict]:
        """Fetch events between start_time and end_time"""
        if not self.service:
            return []

        try:
            result = self.service.events().list(
                calendarId='primary',
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = []
            for event in result.get('items', []):
                events.append({
                    "id": event['id'],
                    "title": event.get('summary', 'No Title'),
                    "start": event['start'].get('dateTime', event['start'].get('date')),
                    "end": event['end'].get('dateTime', event['end'].get('date')),
                    "description": event.get('description', ''),
                    "location": event.get('location', ''),
                    "link": event.get('htmlLink')
                })
            return events
        except Exception as e:
            logger.error(f"❌ Get events error: {e}")
            return []

    async def get_today_events(self) -> List[Dict]:
        now = datetime.now(self.timezone)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return await self.get_events(start, end)

    async def get_calendar_summary(self) -> Dict:
        events = await self.get_today_events()
        return {
            "today_count": len(events),
            "today_events": events[:3],
            "next_event": events[0] if events else None
        }