"""
FastAPI Backend for Present Operating System (POS)
Main server with all endpoints
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import agents
from parent_agent import ParentAgent
from agents.task_agent import TaskAgent
from agents.calendar_agent import CalendarAgent
from agents.email_agent import EmailAgent
from agents.weather_agent import WeatherAgent
from agents.xp_agent import XPAgent

# Global agent instances
parent_agent: Optional[ParentAgent] = None
agents: Dict[str, Any] = {}


# ====== LIFESPAN EVENT (REPLACES @app.on_event("startup")) ======
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global parent_agent, agents
    
    # Startup
    print("ðŸš€ Starting Present Operating System...")
    
    try:
        # Initialize parent agent
        parent_agent = ParentAgent()
        await parent_agent.initialize()
        
        # Store agent references
        agents = parent_agent.agents
        
        print("âœ… All agents initialized successfully")
        print(f"ðŸ“¡ Server running on {os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', 8000)}")
        
    except Exception as e:
        print(f"âŒ Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    print("Shutting down...")
    try:
        if "browser" in agents:
            await agents["browser"].cleanup()
    except:
        pass


# Initialize FastAPI with lifespan
app = FastAPI(
    title="Present Operating System API",
    description="AI-powered personal assistant with PAEI framework",
    version="1.0.0",
    lifespan=lifespan  # <--- THIS IS THE FIX
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", "http://localhost:5173")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict] = None


class TaskCreate(BaseModel):
    title: str
    avatar: str = "Producer"
    priority: str = "P3"
    rpm_result: Optional[str] = None
    rpm_purpose: Optional[str] = None
    due_date: Optional[str] = None
    tags: Optional[List[str]] = None


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    avatar: Optional[str] = None
    due_date: Optional[str] = None


class EventCreate(BaseModel):
    title: str
    start_time: str  # ISO format
    end_time: str
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    reminders: Optional[List[int]] = None


class EmailSend(BaseModel):
    to: str
    subject: str
    body: str
    cc: Optional[List[str]] = None


class XPAward(BaseModel):
    avatar: str
    xp_amount: int
    reason: str = "Task completed"


# Add this to your main.py after the XP endpoints and before Contact endpoints
class ChatRequest(BaseModel):
    message: str
    include_context: bool = True


# Health check
@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "online",
        "service": "Present Operating System",
        "version": "1.0.0",
        "agents": list(agents.keys()) if agents else []
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    agent_status = {}
    
    for name, agent in agents.items():
        agent_status[name] = "initialized"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents": agent_status
    }


# Main processing endpoint
@app.post("/process")
async def process_query(request: QueryRequest):
    """
    Main endpoint - processes user query through parent agent
    Returns unified response with PAEI perspectives
    """
    
    if not parent_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await parent_agent.process(request.query)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Context endpoint
@app.get("/context")
async def get_context():
    """Get current system context (energy, calendar, tasks, weather)"""
    
    if not parent_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        context = await parent_agent.get_context()
        return context
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# PAEI Perspectives endpoint
@app.post("/paei")
async def get_paei_perspectives(request: QueryRequest):
    """Get advice from all 4 PAEI personalities"""
    
    if not parent_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        perspectives = await parent_agent.get_paei_perspectives(request.query)
        return perspectives
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TASK AGENT ENDPOINTS ====================

@app.post("/tasks")
async def create_task(task: TaskCreate):
    """Create a new task"""
    
    if "task" not in agents:
        raise HTTPException(status_code=503, detail="Task agent not available")
    
    try:
        result = await agents["task"].create_task(
            title=task.title,
            avatar=task.avatar,
            priority=task.priority,
            rpm_result=task.rpm_result,
            rpm_purpose=task.rpm_purpose,
            due_date=task.due_date,
            tags=task.tags
        )
        
        # Award XP
        if result.get("success") and "xp" in agents:
            xp_result = agents["xp"].award_xp(
                avatar=task.avatar,
                xp_amount=agents["xp"].calculate_task_xp(task.priority),
                reason=f"Created task: {task.title}"
            )
            result["xp_awarded"] = xp_result
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks")
async def get_tasks(
    status: Optional[str] = None,
    avatar: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100
):
    """Get tasks with optional filters"""
    
    if "task" not in agents:
        raise HTTPException(status_code=503, detail="Task agent not available")
    
    try:
        tasks = await agents["task"].get_tasks(
            status=status,
            avatar=avatar,
            priority=priority,
            limit=limit
        )
        return {"tasks": tasks, "count": len(tasks)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/today")
async def get_today_tasks():
    """Get tasks due today"""
    
    if "task" not in agents:
        raise HTTPException(status_code=503, detail="Task agent not available")
    
    try:
        tasks = await agents["task"].get_today_tasks()
        return {"tasks": tasks, "count": len(tasks)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/overdue")
async def get_overdue_tasks():
    """Get overdue tasks"""
    
    if "task" not in agents:
        raise HTTPException(status_code=503, detail="Task agent not available")
    
    try:
        tasks = await agents["task"].get_overdue_tasks()
        return {"tasks": tasks, "count": len(tasks)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/tasks/{task_id}")
async def update_task(task_id: str, updates: TaskUpdate):
    """Update a task"""
    
    if "task" not in agents:
        raise HTTPException(status_code=503, detail="Task agent not available")
    
    try:
        update_dict = updates.dict(exclude_none=True)
        result = await agents["task"].update_task(task_id, **update_dict)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str):
    """Mark task as complete and award XP"""
    
    if "task" not in agents:
        raise HTTPException(status_code=503, detail="Task agent not available")
    
    try:
        result = await agents["task"].complete_task(task_id)
        
        # Award XP for completion
        if result.get("success") and "xp" in agents:
            # Get task details to determine XP
            tasks = await agents["task"].get_tasks()
            task = next((t for t in tasks if t["id"] == task_id), None)
            
            if task:
                xp_result = agents["xp"].award_xp(
                    avatar=task.get("avatar", "Producer"),
                    xp_amount=agents["xp"].calculate_task_xp(
                        task.get("priority", "P3")
                    ) * 2,  # Double XP for completion
                    reason=f"Completed: {task.get('title', 'task')}"
                )
                result["xp_awarded"] = xp_result
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CALENDAR AGENT ENDPOINTS ====================

@app.post("/calendar/events")
async def create_event(event: EventCreate):
    """Create a calendar event"""

    if "calendar" not in agents:
        raise HTTPException(status_code=503, detail="Calendar agent not available")

    try:
        # Convert ISO strings to datetime if provided
        start_time = datetime.fromisoformat(event.start_time.replace('Z', '+00:00')) if event.start_time else None
        end_time = datetime.fromisoformat(event.end_time.replace('Z', '+00:00')) if event.end_time else None

        # Ensure reminders is a list of dicts or None
        reminders = event.reminders if hasattr(event, "reminders") else None

        result = await agents["calendar"].create_event(
            title=event.title,
            start_time=start_time,
            end_time=end_time,
            description=event.description,
            location=event.location,
            attendees=event.attendees,
            reminders=reminders
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/calendar/today")
async def get_today_events():
    """Get today's events"""
    
    if "calendar" not in agents:
        raise HTTPException(status_code=503, detail="Calendar agent not available")
    
    try:
        events = await agents["calendar"].get_today_events()
        return {"events": events, "count": len(events)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/calendar/upcoming")
async def get_upcoming_events(hours: int = 24):
    """Get upcoming events"""
    
    if "calendar" not in agents:
        raise HTTPException(status_code=503, detail="Calendar agent not available")
    
    try:
        events = await agents["calendar"].get_upcoming_events(hours=hours)
        return {"events": events, "count": len(events)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/calendar/availability")
async def check_availability(start_time: str, end_time: str):
    """Check availability for a time slot"""
    
    if "calendar" not in agents:
        raise HTTPException(status_code=503, detail="Calendar agent not available")
    
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        availability = await agents["calendar"].check_availability(start, end)
        return availability
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/calendar/summary")
async def get_calendar_summary():
    """Get calendar summary"""
    
    if "calendar" not in agents:
        raise HTTPException(status_code=503, detail="Calendar agent not available")
    
    try:
        summary = await agents["calendar"].get_calendar_summary()
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== EMAIL AGENT ENDPOINTS ====================

@app.post("/email/send")
async def send_email(email: EmailSend):
    """Send an email"""
    
    if "email" not in agents:
        raise HTTPException(status_code=503, detail="Email agent not available")
    
    try:
        result = await agents["email"].send_email(
            to=email.to,
            subject=email.subject,
            body=email.body,
            cc=email.cc
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/email/recent")
async def get_recent_emails(max_results: int = 10, query: str = "is:unread"):
    """Get recent emails"""
    
    if "email" not in agents:
        raise HTTPException(status_code=503, detail="Email agent not available")
    
    try:
        emails = await agents["email"].get_recent_emails(
            max_results=max_results,
            query=query
        )
        return {"emails": emails, "count": len(emails)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/email/unread")
async def get_unread_count():
    """Get count of unread emails"""
    
    if "email" not in agents:
        raise HTTPException(status_code=503, detail="Email agent not available")
    
    try:
        count = await agents["email"].get_unread_count()
        return {"unread_count": count}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WEATHER AGENT ENDPOINTS ====================

@app.get("/weather/current")
async def get_current_weather():
    """Get current weather"""
    
    if "weather" not in agents:
        raise HTTPException(status_code=503, detail="Weather agent not available")
    
    try:
        weather = await agents["weather"].get_current_weather()
        return weather
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/weather/forecast")
async def get_weather_forecast(days: int = 3):
    """Get weather forecast"""
    
    if "weather" not in agents:
        raise HTTPException(status_code=503, detail="Weather agent not available")
    
    try:
        forecast = await agents["weather"].get_forecast(days=days)
        return {"forecast": forecast, "days": len(forecast)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== XP AGENT ENDPOINTS ====================

@app.post("/xp/award")
async def award_xp(xp: XPAward):
    """Award XP to an avatar"""
    
    if "xp" not in agents:
        raise HTTPException(status_code=503, detail="XP agent not available")
    
    try:
        result = agents["xp"].award_xp(
            avatar=xp.avatar,
            xp_amount=xp.xp_amount,
            reason=xp.reason
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/xp/avatars")
async def get_all_avatars():
    """Get status of all avatars"""
    
    if "xp" not in agents:
        raise HTTPException(status_code=503, detail="XP agent not available")
    
    try:
        avatars = await agents["xp"].get_all_avatars()
        return {"avatars": avatars}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/xp/avatars/{avatar}")
async def get_avatar_status(avatar: str):
    """Get status of a specific avatar"""
    
    if "xp" not in agents:
        raise HTTPException(status_code=503, detail="XP agent not available")
    
    try:
        status = agents["xp"].get_avatar_status(avatar)
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/xp/achievements")
async def get_achievements(limit: int = 10):
    """Get recent achievements"""
    
    if "xp" not in agents:
        raise HTTPException(status_code=503, detail="XP agent not available")
    
    try:
        achievements = agents["xp"].get_achievements(limit=limit)
        return {"achievements": achievements, "count": len(achievements)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== GROQ AGENT ENDPOINTS ====================

@app.post("/groq/chat")
async def chat_with_groq(request: ChatRequest):
    """Chat with Groq AI assistant"""
    
    if "groq" not in agents:
        raise HTTPException(status_code=503, detail="Groq agent not available")
    
    try:
        # Get system context if requested
        context = None
        if request.include_context and parent_agent:
            context = await parent_agent.fetch_context()
        
        result = await agents["groq"].chat(
            user_message=request.message,
            system_context=context
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/groq/clear")
async def clear_groq_history():
    """Clear conversation history"""
    
    if "groq" not in agents:
        raise HTTPException(status_code=503, detail="Groq agent not available")
    
    try:
        result = await agents["groq"].clear_history()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/groq/summary")
async def get_groq_summary():
    """Get conversation summary"""
    
    if "groq" not in agents:
        raise HTTPException(status_code=503, detail="Groq agent not available")
    
    try:
        summary = await agents["groq"].get_conversation_summary()
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/groq/suggest")
async def get_groq_suggestions():
    """Get AI-powered action suggestions based on current context"""
    
    if "groq" not in agents:
        raise HTTPException(status_code=503, detail="Groq agent not available")
    
    if not parent_agent:
        raise HTTPException(status_code=503, detail="Parent agent not available")
    
    try:
        context = await parent_agent.fetch_context()
        suggestions = await agents["groq"].suggest_actions(context)
        return suggestions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CONTACT AGENT ENDPOINTS ====================

@app.get("/contacts")
async def get_all_contacts():
    """Get all contacts"""
    
    if "contact" not in agents:
        raise HTTPException(status_code=503, detail="Contact agent not available")
    
    try:
        contacts = await agents["contact"].get_all_contacts()
        return {
            "contacts": contacts,
            "count": len(contacts),
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/contacts")
async def add_contact(contact: Dict):
    """Add a new contact"""
    
    if "contact" not in agents:
        raise HTTPException(status_code=503, detail="Contact agent not available")
    
    try:
        result = await agents["contact"].add_contact(
            name=contact.get("name"),
            email=contact.get("email"),
            phone=contact.get("phone"),
            company=contact.get("company"),
            role=contact.get("role"),
            tags=contact.get("tags"),
            notes=contact.get("notes"),
            raw_text=contact.get("raw_text")
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/contacts/search")
async def search_contacts(query: str):
    """Search contacts"""
    
    if "contact" not in agents:
        raise HTTPException(status_code=503, detail="Contact agent not available")
    
    try:
        results = await agents["contact"].search_contacts(query)
        return {
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str):
    """Delete a contact"""
    
    if "contact" not in agents:
        raise HTTPException(status_code=503, detail="Contact agent not available")
    
    try:
        result = await agents["contact"].delete_contact(contact_id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run server
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )