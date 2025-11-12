"""
Task Agent - FIXED FOR YOUR NOTION DATABASE
Matches EXACTLY your database structure from the screenshot
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from notion_client import Client
import logging

logger = logging.getLogger(__name__)


class TaskAgent:
    """Task agent matching YOUR Notion database structure"""
    
    def __init__(self):
        self.notion_token = os.getenv("NOTION_TOKEN")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self.client = None
        
    async def initialize(self):
        """Initialize Notion"""
        try:
            if not self.notion_token:
                logger.error("❌ NOTION_TOKEN not found in .env")
                return False
            
            if not self.database_id:
                logger.error("❌ NOTION_DATABASE_ID not found in .env")
                return False
            
            self.client = Client(auth=self.notion_token)
            
            # Test connection
            response = self.client.databases.retrieve(database_id=self.database_id)
            db_title = response.get('title', [{}])[0].get('plain_text', 'POS Tasks')
            
            logger.info(f"✅ Notion connected: {db_title}")
            logger.info(f"📊 Database ID: {self.database_id[:8]}...")
            
            # Log properties
            props = response.get('properties', {})
            logger.info(f"🔍 Properties: {list(props.keys())}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Notion init failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def create_task(
        self,
        title: str,
        avatar: str = "Producer",
        priority: str = "P3",
        rpm_result: Optional[str] = None,
        rpm_purpose: Optional[str] = None,
        due_date: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: str = "Inbox"
    ) -> Dict:
        """Create task in YOUR Notion database"""
        
        if not self.client:
            logger.warning("⚠️ Notion not connected")
            return {
                "success": False,
                "error": "Notion not connected",
                "user_message": "❌ Task creation failed: Notion not connected"
            }
        
        try:
            logger.info(f"🔨 Creating task: {title}")
            
            # Build properties matching YOUR database
            properties = {
                # Title property (Name column)
                "Name": {
                    "title": [
                        {"text": {"content": title}}
                    ]
                },
                
                # Avatar select (Producer, Administrator, Entrepreneur, Integrator)
                "Avatar": {
                    "select": {"name": avatar}
                },
                
                # Priority select (P1, P2, P3, P4)
                "Priority": {
                    "select": {"name": priority}
                },
                
                # Status select (Inbox, Scheduled, In Progress, Done)
                "Status": {
                    "select": {"name": status}
                }
            }
            
            # XP Value (10-100 based on priority)
            xp_values = {"P1": 50, "P2": 30, "P3": 20, "P4": 10}
            properties["XP Value"] = {
                "number": xp_values.get(priority, 20)
            }
            
            # Due Date (if provided)
            if due_date:
                try:
                    # Handle different date formats
                    if 'T' in due_date:
                        date_part = due_date.split('T')[0]
                    else:
                        date_part = due_date
                    
                    properties["Due Date"] = {
                        "date": {"start": date_part}
                    }
                    logger.info(f"📅 Due date set: {date_part}")
                except Exception as e:
                    logger.warning(f"⚠️ Date parse error: {e}")
            
            # Create the page in Notion
            logger.info(f"🚀 Sending to Notion...")
            new_page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            logger.info(f"✅ Task created in Notion!")
            
            # Add content blocks if RPM provided
            if rpm_result or rpm_purpose:
                blocks = []
                
                if rpm_result:
                    blocks.append({
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [{"type": "text", "text": {"content": "Expected Result"}}]
                        }
                    })
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": rpm_result}}]
                        }
                    })
                
                if rpm_purpose:
                    blocks.append({
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [{"type": "text", "text": {"content": "Purpose"}}]
                        }
                    })
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": rpm_purpose}}]
                        }
                    })
                
                try:
                    self.client.blocks.children.append(
                        block_id=new_page["id"],
                        children=blocks
                    )
                    logger.info("📄 Added content blocks")
                except Exception as e:
                    logger.warning(f"⚠️ Could not add blocks: {e}")
            
            return {
                "success": True,
                "task_id": new_page["id"],
                "title": title,
                "avatar": avatar,
                "priority": priority,
                "status": status,
                "url": new_page["url"],
                "user_message": f"✅ Task '{title}' created in Notion!",
                "xp_value": xp_values.get(priority, 20)
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Task creation failed: {error_msg}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": error_msg,
                "title": title,
                "user_message": f"❌ Failed to create task: {error_msg[:100]}"
            }
    
    async def get_tasks(
        self,
        status: Optional[str] = None,
        avatar: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get tasks from Notion - FIXED API CALL"""
        
        if not self.client:
            return []
        
        try:
            # Build filters
            filters = []
            
            if status:
                filters.append({
                    "property": "Status",
                    "select": {"equals": status}
                })
            
            if avatar:
                filters.append({
                    "property": "Avatar",
                    "select": {"equals": avatar}
                })
            
            if priority:
                filters.append({
                    "property": "Priority",
                    "select": {"equals": priority}
                })
            
            # Build query
            query_params = {
                "page_size": limit,
                "sorts": [
                    {"property": "Priority", "direction": "ascending"},
                    {"property": "Created", "direction": "descending"}
                ]
            }
            
            if filters:
                if len(filters) > 1:
                    query_params["filter"] = {"and": filters}
                else:
                    query_params["filter"] = filters[0]
            
            # ✅ FIXED: Use .query() instead of .query_database()
            response = self.client.databases.query(
                database_id=self.database_id,
                **query_params
            )
            
            tasks = []
            for page in response.get("results", []):
                props = page["properties"]
                
                task = {
                    "id": page["id"],
                    "title": self._get_title(props.get("Name")),
                    "status": self._get_select(props.get("Status")),
                    "avatar": self._get_select(props.get("Avatar")),
                    "priority": self._get_select(props.get("Priority")),
                    "due_date": self._get_date(props.get("Due Date")),
                    "xp_value": self._get_number(props.get("XP Value")),
                    "created": page.get("created_time"),
                    "url": page.get("url")
                }
                tasks.append(task)
            
            logger.info(f"📊 Retrieved {len(tasks)} tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"❌ Get tasks error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_title(self, prop):
        """Extract title"""
        if prop and prop.get("title"):
            return prop["title"][0]["text"]["content"]
        return ""
    
    def _get_select(self, prop):
        """Extract select value"""
        if prop and prop.get("select"):
            return prop["select"]["name"]
        return None
    
    def _get_number(self, prop):
        """Extract number"""
        if prop and prop.get("number") is not None:
            return prop["number"]
        return 0
    
    def _get_date(self, prop):
        """Extract date"""
        if prop and prop.get("date") and prop["date"].get("start"):
            return prop["date"]["start"]
        return None
    
    async def get_today_tasks(self) -> List[Dict]:
        """Get inbox tasks"""
        return await self.get_tasks(status="Inbox")
    
    async def get_overdue_tasks(self) -> List[Dict]:
        """Get overdue tasks"""
        all_tasks = await self.get_tasks()
        today = datetime.now().date()
        
        overdue = []
        for task in all_tasks:
            if task.get("due_date") and task.get("status") != "Done":
                try:
                    due_date = datetime.fromisoformat(task["due_date"].replace('Z', '')).date()
                    if due_date < today:
                        overdue.append(task)
                except:
                    pass
        
        return overdue
    
    async def update_task(self, task_id: str, **updates) -> Dict:
        """Update task"""
        if not self.client:
            return {"success": False, "error": "Not initialized"}
        
        try:
            properties = {}
            
            if "status" in updates:
                properties["Status"] = {"select": {"name": updates["status"]}}
            if "priority" in updates:
                properties["Priority"] = {"select": {"name": updates["priority"]}}
            if "avatar" in updates:
                properties["Avatar"] = {"select": {"name": updates["avatar"]}}
            if "due_date" in updates:
                properties["Due Date"] = {"date": {"start": updates["due_date"]}}
            
            self.client.pages.update(
                page_id=task_id,
                properties=properties
            )
            
            logger.info(f"✅ Task updated")
            return {"success": True, "task_id": task_id}
            
        except Exception as e:
            logger.error(f"❌ Update error: {e}")
            return {"success": False, "error": str(e)}
    
    async def complete_task(self, task_id: str) -> Dict:
        """Mark as done"""
        return await self.update_task(task_id, status="Done")