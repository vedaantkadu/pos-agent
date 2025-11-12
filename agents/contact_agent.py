"""
Contact Agent - PRODUCTION READY
Extracts names properly + displays in UI
"""

from datetime import datetime
from typing import Dict, List, Optional
import json
import os
import logging
import re

logger = logging.getLogger(__name__)


class ContactAgent:
    """Production contact management"""
    
    def __init__(self):
        self.data_file = "contacts_data.json"
        self.contacts = {}
        self.interactions = []
        self._load_data()
        
    async def initialize(self):
        """Initialize"""
        logger.info(f"✅ Contact Agent ready ({len(self.contacts)} contacts)")
        return True
    
    def _load_data(self):
        """Load contacts"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.contacts = data.get('contacts', {})
                    self.interactions = data.get('interactions', [])
                    logger.info(f"📂 Loaded {len(self.contacts)} contacts")
        except Exception as e:
            logger.error(f"❌ Load error: {e}")
    
    def _save_data(self):
        """Save contacts"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump({
                    'contacts': self.contacts,
                    'interactions': self.interactions
                }, f, indent=2)
            logger.info(f"💾 Saved {len(self.contacts)} contacts")
        except Exception as e:
            logger.error(f"❌ Save error: {e}")
    
    def extract_contact_info(self, text: str) -> Dict:
        """
        PRODUCTION contact extraction
        """
        
        text_lower = text.lower()
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        email = emails[0] if emails else None
        
        # Phone
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\d{10}',
            r'\+\d{11,15}',
        ]
        phone = None
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                phone = phones[0]
                break
        
        # Name extraction - ENHANCED
        name = None
        
        # Strategy 1: Explicit patterns
        name_patterns = [
            r'(?:add|new|create|save)\s+contact\s+(?:named\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'contact\s+(?:named|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:name|person)(?:\s+is)?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:add|save)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:\s+to contacts|\s+as contact)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                potential = match.group(1).strip()
                stop_words = {'Contact', 'Person', 'Add', 'New', 'Create', 'Save', 'Named', 'Called'}
                if potential not in stop_words:
                    name = potential
                    logger.info(f"✅ Name (pattern): {name}")
                    break
        
        # Strategy 2: Find capitalized sequences
        if not name:
            cap_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b'
            matches = re.findall(cap_pattern, text)
            
            if matches:
                stop_words = {
                    'Add', 'New', 'Create', 'Save', 'Contact', 'Person', 'Email',
                    'Phone', 'Company', 'Work', 'Home', 'The', 'This', 'That'
                }
                
                for match in matches:
                    words = match.split()
                    if not any(word in stop_words for word in words):
                        name = match
                        logger.info(f"✅ Name (caps): {name}")
                        break
        
        # Strategy 3: Extract from email
        if not name and email:
            username = email.split('@')[0]
            name = username.replace('.', ' ').replace('_', ' ').title()
            logger.info(f"✅ Name (email): {name}")
        
        # Company
        company = None
        company_patterns = [
            r'(?:works?\s+at|from|at|company)\s+([A-Z][A-Za-z\s&.,Inc]+?)(?:\s+as|\s+and|\.|$)',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                company = match.group(1).strip().rstrip('.')
                logger.info(f"✅ Company: {company}")
                break
        
        # Role
        role = None
        role_patterns = [
            r'(?:works?\s+as|role\s+is|position\s+is|title\s+is)\s+(?:a\s+|an\s+)?([A-Za-z\s]+?)(?:\s+at|\s+from|$)',
        ]
        for pattern in role_patterns:
            match = re.search(pattern, text_lower)
            if match:
                role = match.group(1).strip().title()
                logger.info(f"✅ Role: {role}")
                break
        
        # Tags
        tags = []
        tag_keywords = {
            'client': 'client', 'customer': 'client',
            'vendor': 'vendor', 'supplier': 'vendor',
            'colleague': 'colleague', 'friend': 'friend',
            'family': 'family', 'important': 'important', 'vip': 'vip'
        }
        for keyword, tag in tag_keywords.items():
            if keyword in text_lower and tag not in tags:
                tags.append(tag)
        
        return {
            'name': name,
            'email': email,
            'phone': phone,
            'company': company,
            'role': role,
            'tags': tags if tags else None
        }
    
    async def add_contact(
        self,
        name: str = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        role: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        raw_text: Optional[str] = None
    ) -> Dict:
        """
        Add contact - PRODUCTION READY
        """
        
        # Extract from text
        if raw_text:
            extracted = self.extract_contact_info(raw_text)
            logger.info(f"📝 Extracted: {extracted}")
            
            name = name or extracted.get('name')
            email = email or extracted.get('email')
            phone = phone or extracted.get('phone')
            company = company or extracted.get('company')
            role = role or extracted.get('role')
            tags = tags or extracted.get('tags')
        
        # Validate name
        if not name:
            logger.error("❌ No name")
            return {
                "success": False,
                "error": "No name provided",
                "user_message": "⚠️ Please provide a name. Try: 'Add contact John Doe'"
            }
        
        # Create ID
        contact_id = name.lower().replace(" ", "_")
        is_update = contact_id in self.contacts
        
        # Build contact
        contact = {
            "id": contact_id,
            "name": name,
            "email": email,
            "phone": phone,
            "company": company,
            "role": role,
            "tags": tags or [],
            "notes": notes,
            "added_date": self.contacts.get(contact_id, {}).get('added_date', datetime.now().isoformat()),
            "last_updated": datetime.now().isoformat(),
        }
        
        # Save
        self.contacts[contact_id] = contact
        self._save_data()
        
        action = "updated" if is_update else "added"
        logger.info(f"✅ Contact {action}: {name}")
        
        # Log interaction
        self.interactions.append({
            "contact_id": contact_id,
            "contact_name": name,
            "type": "updated" if is_update else "created",
            "date": datetime.now().isoformat(),
        })
        self._save_data()
        
        return {
            "success": True,
            "contact_id": contact_id,
            "contact": contact,
            "is_update": is_update,
            "message": f"Contact '{name}' {action}!",
            "user_message": f"✅ {name} {action} to contacts",
            "display": {
                "name": name,
                "email": email or "No email",
                "phone": phone or "No phone",
                "company": company or "No company",
                "role": role or "No role",
                "tags": tags or []
            }
        }
    
    async def get_all_contacts(
        self,
        tags: Optional[List[str]] = None,
        importance: Optional[str] = None
    ) -> List[Dict]:
        """Get all contacts"""
        
        contacts = list(self.contacts.values())
        
        if tags:
            contacts = [
                c for c in contacts
                if any(tag in c.get("tags", []) for tag in tags)
            ]
        
        # Sort by last updated
        contacts.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        
        logger.info(f"📇 Retrieved {len(contacts)} contacts")
        return contacts
    
    async def search_contacts(self, query: str) -> List[Dict]:
        """Search contacts"""
        query = query.lower()
        results = []
        
        for contact in self.contacts.values():
            searchable = [
                contact.get("name", "").lower(),
                contact.get("email", "").lower(),
                contact.get("company", "").lower(),
                " ".join(contact.get("tags", [])).lower(),
            ]
            
            if any(query in field for field in searchable):
                results.append(contact)
        
        logger.info(f"🔍 Search '{query}': {len(results)} results")
        return results
    
    async def delete_contact(self, contact_id: str) -> Dict:
        """Delete contact"""
        if contact_id not in self.contacts:
            return {"success": False, "error": "Not found"}
        
        name = self.contacts[contact_id]["name"]
        del self.contacts[contact_id]
        
        self.interactions = [
            i for i in self.interactions
            if i["contact_id"] != contact_id
        ]
        
        self._save_data()
        logger.info(f"🗑️ Deleted: {name}")
        
        return {
            "success": True,
            "message": f"Deleted {name}",
            "user_message": f"✅ {name} removed"
        }