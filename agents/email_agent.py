"""
Email Agent - Manages email with Gmail API
"""

import os
import base64
from email.mime.text import MIMEText
from typing import Dict, List, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle


class EmailAgent:
    """Handles email management through Gmail API"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self):
        self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
        self.service = None
        self.creds = None
        
    async def initialize(self):
        """Initialize Gmail API connection"""
        try:
            if os.path.exists('gmail_token.pickle'):
                with open('gmail_token.pickle', 'rb') as token:
                    self.creds = pickle.load(token)
            
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    self.creds = flow.run_local_server(host='localhost', port=8000)

                with open('gmail_token.pickle', 'wb') as token:
                    pickle.dump(self.creds, token)
            
            self.service = build('gmail', 'v1', credentials=self.creds)
            print("✅ Gmail connected")
            return True
            
        except Exception as e:
            print(f"❌ Email Agent init error: {e}")
            return False
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None
    ) -> Dict:
        """Send an email"""
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            return {
                "success": True,
                "message_id": sent_message['id'],
                "to": to,
                "subject": subject
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_recent_emails(
        self,
        max_results: int = 10,
        query: str = "is:unread"
    ) -> List[Dict]:
        """Get recent emails"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = {h['name']: h['value'] 
                          for h in email_data['payload']['headers']}
                
                emails.append({
                    "id": msg['id'],
                    "from": headers.get('From', ''),
                    "subject": headers.get('Subject', ''),
                    "date": headers.get('Date', ''),
                    "snippet": email_data.get('snippet', '')
                })
            
            return emails
            
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []
    
    async def mark_as_read(self, message_id: str) -> Dict:
        """Mark email as read"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            return {"success": True, "message_id": message_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_unread_count(self) -> int:
        """Get count of unread emails"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread'
            ).execute()
            
            return results.get('resultSizeEstimate', 0)
        except:
            return 0
