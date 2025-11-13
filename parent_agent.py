"""
Present Operating System (POS) - Parent Agent - FIXED EMAIL EXTRACTION
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import google.generativeai as genai
import json
import logging
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ParentAgent:
    """Central orchestrator that ACTUALLY executes agent actions"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        self.context = {}
        self.agents = {}
        
    async def initialize(self):
        """Initialize all child agents"""
        from agents.task_agent import TaskAgent
        from agents.calendar_agent import CalendarAgent
        from agents.email_agent import EmailAgent
        from agents.weather_agent import WeatherAgent
        from agents.xp_agent import XPAgent
        from agents.groq_api import GroqAgent
        from agents.report_agent import ReportAgent
        from agents.contact_agent import ContactAgent
        from agents.interrupt_agent import InterruptAgent
        
        self.agents = {
            "task": TaskAgent(),
            "calendar": CalendarAgent(),
            "email": EmailAgent(),
            "weather": WeatherAgent(),
            "xp": XPAgent(),
            "groq": GroqAgent(),
            "report": ReportAgent(),
            "contact": ContactAgent(),
            "interrupt": InterruptAgent()
        }
        
        logger.info("Initializing agent swarm...")
        for name, agent in self.agents.items():
            try:
                await agent.initialize()
                logger.info(f"✅ {name.capitalize()} Agent initialized")
            except Exception as e:
                logger.error(f"❌ {name.capitalize()} Agent failed: {e}")
    
    def analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """Extract structured information from user input"""
        
        if not self.model:
            return self._fallback_intent_analysis(user_input)
        
        prompt = f"""Analyze this user input and extract information.

User input: "{user_input}"

Provide JSON with:
1. intent_type: Main action (schedule, task, email, search, chat, contact, contact_list, report, weather, focus, etc.)
2. entities: {{
   "dates": ["extracted dates"],
   "times": ["extracted times"],
   "emails": ["email addresses found in the text"],
   "names": ["person names"],
   "topics": ["main topics"]
}}
3. priority: P1/P2/P3/P4
4. avatar: Producer/Administrator/Entrepreneur/Integrator
5. params: {{
   "title": "task/event title",
   "description": "details",
   "due_date": "YYYY-MM-DD",
   "query": "search/chat query",
   "to_email": "recipient email address",
   "subject": "email subject",
   "body": "email body text",
   "contact_name": "person name for contacts",
   "action": "list/add/search for contacts"
}}

CRITICAL: For emails:
- Extract the email address and put it in BOTH entities.emails AND params.to_email
- Extract the message content and put it in params.body
- Generate an appropriate subject line

Examples:
- "send email to john@example.com asking about the project" → 
  intent_type: "email", 
  entities: {{"emails": ["john@example.com"]}},
  params: {{"to_email": "john@example.com", "subject": "Project inquiry", "body": "asking about the project"}}

- "email vedant@gmail.com tell him to give my money back" →
  intent_type: "email",
  entities: {{"emails": ["vedant@gmail.com"]}},
  params: {{"to_email": "vedant@gmail.com", "subject": "Payment Request", "body": "tell him to give my money back"}}

Respond ONLY with valid JSON."""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            elif result_text.startswith("```"):
                result_text = result_text.replace("```", "").strip()
            
            parsed = json.loads(result_text)
            parsed["original_input"] = user_input
            
            # FORCE email extraction with regex as backup
            if parsed.get("intent_type") == "email":
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
                emails = re.findall(email_pattern, user_input)
                if emails and not parsed.get("params", {}).get("to_email"):
                    parsed.setdefault("params", {})["to_email"] = emails[0]
                    parsed.setdefault("entities", {})["emails"] = emails
                    logger.info(f"🔧 Backup regex extracted email: {emails[0]}")
            
            return parsed
            
        except Exception as e:
            logger.warning(f"Intent analysis error: {e}")
            return self._fallback_intent_analysis(user_input)
    
    def _fallback_intent_analysis(self, user_input: str) -> Dict:
        """Enhanced fallback with better email parsing"""
        lower_input = user_input.lower()
        
        intent_type = "chat"
        avatar = "Producer"
        priority = "P3"
        params = {}
        entities = {}
        
        # STEP 1: Extract emails FIRST - this is critical
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        emails = re.findall(email_pattern, user_input)
        
        if emails:
            params["to_email"] = emails[0]
            entities["emails"] = emails
            logger.info(f"📧 Extracted email: {emails[0]}")
        
        # STEP 2: Detect intent
        if any(word in lower_input for word in ["search for", "find information about", "look up", "google"]):
            intent_type = "search"
            query = lower_input
            for trigger in ["search for", "find information about", "look up", "google", "search"]:
                if trigger in query:
                    query = query.split(trigger, 1)[-1].strip()
            params["query"] = query
        
        elif any(word in lower_input for word in ["show all contacts", "view all contacts", "list contacts", "all my contacts", "show contacts"]):
            intent_type = "contact_list"
            params["action"] = "list"
        
        elif any(word in lower_input for word in ["add contact", "new contact", "save contact", "create contact"]):
            intent_type = "contact"
            params["action"] = "add"
            name_match = re.search(r'contact\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', user_input)
            if name_match:
                params["contact_name"] = name_match.group(1)
        
        elif any(word in lower_input for word in ["email", "mail", "send", "write to", "message"]) or emails:
            # If we detected an email address OR email keywords, it's an email intent
            intent_type = "email"
            
            # Extract body content
            body_triggers = ["tell him", "tell her", "tell them", "asking", "ask", "about", "regarding"]
            body = user_input
            
            # Try to extract the message part
            for trigger in ["tell him", "tell her", "tell them", "asking", "ask him", "ask her"]:
                if trigger in lower_input:
                    body = lower_input.split(trigger, 1)[-1].strip()
                    break
            
            # If no trigger found, use everything after the email
            if emails and emails[0] in user_input:
                parts = user_input.split(emails[0], 1)
                if len(parts) > 1:
                    body = parts[1].strip()
            
            params["body"] = body if body != user_input else user_input
            params["subject"] = "Message from Present OS"
            
            logger.info(f"📧 Email intent - To: {params.get('to_email')}, Body: {params.get('body')[:50]}...")
        
        elif any(word in lower_input for word in ["task", "todo", "remind", "create task"]):
            intent_type = "task"
            title_match = re.search(r'(?:task|todo|create)\s+(?:to\s+)?(.+)', lower_input)
            if title_match:
                params["title"] = title_match.group(1).strip()
        
        elif any(word in lower_input for word in ["schedule", "calendar", "meeting", "event", "book"]):
            intent_type = "schedule"
            event_match = re.search(r'(?:schedule|meeting|event)\s+(?:a\s+)?(.+?)(?:\s+(?:at|on|for|tomorrow|today)\s+|$)', lower_input)
            if event_match:
                params["title"] = event_match.group(1).strip()
            else:
                params["title"] = "Meeting"
        
        elif any(word in lower_input for word in ["weather", "temperature", "forecast"]):
            intent_type = "weather"
        
        elif any(word in lower_input for word in ["report", "summary", "stats", "performance"]):
            intent_type = "report"
        
        else:
            intent_type = "chat"
            params["query"] = user_input
        
        # Priority detection
        if any(word in lower_input for word in ["urgent", "asap", "immediately", "critical"]):
            priority = "P1"
        elif any(word in lower_input for word in ["important", "high priority"]):
            priority = "P2"
        
        return {
            "intent_type": intent_type,
            "entities": entities,
            "priority": priority,
            "avatar": avatar,
            "params": params,
            "original_input": user_input
        }
    
    def route_to_agents(self, intent: Dict[str, Any]) -> List[str]:
        """Better routing logic with Groq integration"""
        
        agents_to_activate = []
        intent_type = intent.get("intent_type", "").lower()
        params = intent.get("params", {})
        
        # Direct mapping
        agent_map = {
            "task": ["task", "xp"],
            "schedule": ["calendar", "xp"],
            "email": ["email"],
            "weather": ["weather"],
            "search": ["groq"],
            "chat": ["groq"],
            "contact": ["contact"],
            "contact_list": ["contact"],
            "report": ["report", "task", "xp"],
            "focus": ["interrupt"],
            "xp": ["xp"]
        }
        
        if intent_type in agent_map:
            agents_to_activate.extend(agent_map[intent_type])
        else:
            agents_to_activate.append("groq")
        
        # Remove duplicates
        seen = set()
        unique_agents = []
        for agent in agents_to_activate:
            if agent not in seen and agent in self.agents:
                seen.add(agent)
                unique_agents.append(agent)
        
        if not unique_agents:
            unique_agents = ["groq"]
        
        logger.info(f"Routing to agents: {unique_agents}")
        return unique_agents
    
    async def process(self, user_input: str) -> Dict[str, Any]:
        """Main processing pipeline"""
        
        try:
            logger.info(f"🎯 Processing: {user_input}")
            intent = self.analyze_intent(user_input)
            logger.info(f"🧠 Intent: {intent.get('intent_type')}")
            logger.info(f"📋 Params: {intent.get('params')}")
            
            agents_to_activate = self.route_to_agents(intent)
            logger.info(f"🤖 Activating: {', '.join(agents_to_activate)}")
            
            agent_results = []
            for agent_name in agents_to_activate:
                if agent_name in self.agents:
                    result = await self._execute_agent(agent_name, intent, agents_to_activate)
                    agent_results.append(result)
                    logger.info(f"✅ {agent_name} executed")
            
            response_text = self._generate_response(intent, agent_results)
            
            return {
                "response": response_text,
                "intent": intent,
                "agents": agents_to_activate,
                "actions": agent_results,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "response": f"Error: {str(e)}",
                "error": str(e),
                "success": False
            }
    
    async def _execute_agent(self, agent_name: str, intent: Dict, agents_to_activate: List[str]) -> Dict:
        """ACTUALLY EXECUTE AGENTS - FIXED EMAIL HANDLING"""
        
        try:
            agent = self.agents[agent_name]
            params = intent.get("params", {})
            intent_type = intent.get("intent_type", "")
            original_text = intent.get("original_input", "")
            
            # ========== TASK AGENT ==========
            if agent_name == "task":
                title = params.get("title") or intent.get("original_input", "New task")
                
                logger.info(f"📝 Creating task: {title}")
                result = await agent.create_task(
                    title=title,
                    avatar=intent.get("avatar", "Producer"),
                    priority=intent.get("priority", "P3"),
                    due_date=params.get("due_date")
                )
                return {"agent": "task", "action": "create", "result": result}
            
            # ========== CALENDAR AGENT ==========
            elif agent_name == "calendar":
                title = params.get("title", "Meeting")
                
                logger.info(f"📅 Creating calendar event: {title}")
                result = await agent.create_event(
                    title=title,
                    original_text=original_text,
                    description=params.get("description")
                )
                
                return {"agent": "calendar", "action": "create", "result": result}
            
            # ========== EMAIL AGENT - FIXED ==========
            elif agent_name == "email":
                to_email = params.get("to_email")
                
                # DEBUGGING
                logger.info(f"📧 Email Agent - Params: {params}")
                logger.info(f"📧 Email Agent - to_email: {to_email}")
                
                if not to_email:
                    logger.error("⚠️ No recipient email found in params")
                    logger.error(f"⚠️ Full intent: {intent}")
                    return {
                        "agent": "email",
                        "action": "error",
                        "result": {"error": "No recipient email specified", "success": False}
                    }
                
                subject = params.get("subject", "Message from Present OS")
                body = params.get("body", original_text)
                
                logger.info(f"📧 Sending email:")
                logger.info(f"   To: {to_email}")
                logger.info(f"   Subject: {subject}")
                logger.info(f"   Body: {body[:100]}...")
                
                result = await agent.send_email(
                    to=to_email,
                    subject=subject,
                    body=body
                )
                
                return {"agent": "email", "action": "send", "result": result}
            
            # ========== GROQ AGENT - SEARCH & CHAT ==========
            elif agent_name == "groq":
                system_context = await self.fetch_context()
                
                if intent_type == "search":
                    query = params.get("query") or original_text
                    search_prompt = f"Search and provide detailed information about: {query}"
                    
                    logger.info(f"🔍 Groq search query: {query}")
                    result = await agent.chat(search_prompt, system_context)
                    
                    return {
                        "agent": "groq",
                        "action": "search",
                        "result": result
                    }
                else:
                    logger.info(f"💬 Groq chat: {original_text[:50]}...")
                    result = await agent.chat(original_text, system_context)
                    
                    return {
                        "agent": "groq",
                        "action": "chat",
                        "result": result
                    }
            
            # ========== WEATHER AGENT ==========
            elif agent_name == "weather":
                result = await agent.get_current_weather()
                return {"agent": "weather", "action": "current", "result": result}
            
            # ========== XP AGENT ==========
            elif agent_name == "xp":
                avatars = await agent.get_all_avatars()
                
                if "task" in agents_to_activate or "calendar" in agents_to_activate:
                    xp_reward = agent.calculate_task_xp(intent.get("priority", "P3"))
                    agent.award_xp(intent.get("avatar", "Producer"), xp_reward, "Action completed")
                
                return {"agent": "xp", "action": "status", "result": {"avatars": avatars}}
            
            # ========== CONTACT AGENT ==========
            elif agent_name == "contact":
                action = params.get("action", "add")
                
                if action == "list" or intent_type == "contact_list":
                    logger.info(f"👥 Retrieving all contacts")
                    contacts = await agent.get_all_contacts()
                    return {
                        "agent": "contact",
                        "action": "list",
                        "result": {
                            "contacts": contacts,
                            "count": len(contacts),
                            "displayable": True
                        }
                    }
                
                elif action == "add" or "add" in intent_type or "contact" in intent_type:
                    logger.info(f"👤 Adding contact from text: {original_text}")
                    
                    result = await agent.add_contact(
                        name=params.get("contact_name"),
                        email=params.get("email"),
                        phone=params.get("phone"),
                        company=params.get("company"),
                        role=params.get("role"),
                        tags=params.get("tags"),
                        raw_text=original_text
                    )
                    return {"agent": "contact", "action": "add", "result": result}
                
                else:
                    contacts = await agent.get_all_contacts()
                    return {"agent": "contact", "action": "list", "result": {"contacts": contacts, "count": len(contacts)}}
            
            # ========== REPORT AGENT ==========
            elif agent_name == "report":
                if "task" in self.agents:
                    tasks = await self.agents["task"].get_tasks()
                    logger.info(f"📊 Generating report with {len(tasks)} tasks")
                    return {
                        "agent": "report",
                        "action": "generate",
                        "result": {
                            "status": "Report ready",
                            "total_tasks": len(tasks),
                            "message": f"Analyzed {len(tasks)} tasks"
                        }
                    }
                return {"agent": "report", "action": "generate", "result": {"status": "Report ready"}}
            
            # ========== INTERRUPT AGENT ==========
            elif agent_name == "interrupt":
                if "start" in intent_type or "focus" in intent_type:
                    result = await agent.start_focus_mode(duration_minutes=25)
                    return {"agent": "interrupt", "action": "start_focus", "result": result}
                else:
                    status = await agent.get_focus_status()
                    return {"agent": "interrupt", "action": "status", "result": status}
            
            else:
                return {"agent": agent_name, "action": "unknown", "result": {"status": "executed"}}
            
        except Exception as e:
            logger.error(f"❌ Agent execution error ({agent_name}): {e}")
            import traceback
            traceback.print_exc()
            return {
                "agent": agent_name,
                "action": "error",
                "result": {"error": str(e)}
            }
    
    def _generate_response(self, intent: Dict, results: List[Dict]) -> str:
        """Generate human-friendly response"""
        
        intent_type = intent.get("intent_type", "")
        
        # Check for errors
        errors = [r for r in results if "error" in r.get("result", {})]
        if errors:
            error_msg = errors[0]['result']['error']
            return f"⚠️ I encountered an issue: {error_msg}"
        
        # Success messages by intent type
        if intent_type == "task":
            return "✅ Task created successfully! Added to your Notion database."
        
        elif intent_type == "schedule":
            event_result = next((r["result"] for r in results if r["agent"] == "calendar"), {})
            if event_result.get("success"):
                title = event_result.get("title", "Event")
                start = event_result.get("start", "")
                try:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    time_str = start_dt.strftime("%B %d at %I:%M %p")
                    return f"📅 Event '{title}' scheduled for {time_str}! Check your Google Calendar."
                except:
                    return f"📅 Event '{title}' scheduled successfully! Check your Google Calendar."
            return "📅 Event created (check your calendar for details)"
        
        elif intent_type == "email":
            email_result = next((r["result"] for r in results if r["agent"] == "email"), {})
            if email_result.get("success"):
                to = email_result.get("to", "recipient")
                return f"✅ Email sent successfully to {to}!"
            return "⚠️ Email sending failed - check logs for details"
        
        elif intent_type in ["search", "chat"]:
            groq_result = next((r["result"] for r in results if r["agent"] == "groq"), {})
            if groq_result.get("success"):
                return groq_result.get("response", "✅ Query processed!")
            return "⚠️ AI service unavailable - check your Groq API key"
        
        elif intent_type == "weather":
            weather_data = next((r["result"] for r in results if r["agent"] == "weather"), {})
            temp = weather_data.get("temp", "?")
            condition = weather_data.get("condition", "Unknown")
            return f"🌤️ Current weather: {temp}°C, {condition}"
        
        elif intent_type == "contact_list":
            contact_result = next((r["result"] for r in results if r["agent"] == "contact"), {})
            if "contacts" in contact_result:
                count = contact_result.get("count", 0)
                return f"📇 You have {count} contacts in your network. Check the UI below to view them!"
            return "📇 Contact list retrieved"
        
        elif intent_type == "contact":
            contact_result = next((r["result"] for r in results if r["agent"] == "contact"), {})
            if contact_result.get("success") and contact_result.get("contact"):
                name = contact_result["contact"].get("name", "Contact")
                return f"✅ Contact '{name}' added successfully!"
            elif "contacts" in contact_result:
                count = len(contact_result["contacts"])
                return f"📇 You have {count} contacts in your network"
            return "✅ Contact operation completed"
        
        elif intent_type == "report":
            report_result = next((r["result"] for r in results if r["agent"] == "report"), {})
            if "total_tasks" in report_result:
                return f"📊 Report generated! Analyzed {report_result['total_tasks']} tasks."
            return "📊 Report ready!"
        
        else:
            return f"✅ Done! Activated {len(results)} agents to help you."
    
    async def fetch_context(self) -> Dict[str, Any]:
        """Get current system context"""
        context = {
            "current_time": datetime.now().isoformat(),
            "energy_level": 70,
            "task_backlog": 0,
            "weather": "Clear"
        }
        
        if "task" in self.agents:
            try:
                tasks = await self.agents["task"].get_tasks()
                context["task_backlog"] = len(tasks)
            except:
                pass
        
        if "weather" in self.agents:
            try:
                weather = await self.agents["weather"].get_current_weather()
                context["weather"] = weather.get("condition", "Clear")
            except:
                pass
        
        return context
    
    async def get_context(self) -> Dict[str, Any]:
        return await self.fetch_context()
    
    async def get_paei_perspectives(self, query: str) -> Dict[str, str]:
        """Get advice from all 4 PAEI personalities"""
        return {}