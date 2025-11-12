"""
Interrupt Agent - Handles urgent notifications intelligently
Implements ADHD-friendly notification management
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class InterruptAgent:
    """
    Manages interruptions intelligently based on:
    - Current focus state
    - Task priority
    - Energy levels
    - Time-based rules (deep work windows)
    """
    
    def __init__(self):
        self.focus_mode = False
        self.focus_start = None
        self.focus_duration = 25  # Pomodoro default
        self.notifications_queue = []
        self.notification_rules = self._default_rules()
        
    async def initialize(self):
        """Initialize interrupt agent"""
        logger.info("✅ Interrupt Agent initialized")
        return True
    
    def _default_rules(self) -> Dict:
        """Default notification rules"""
        return {
            "focus_mode": {
                "allow_p1": True,  # Allow P1 urgencies
                "allow_p2": False,
                "allow_p3": False,
                "allow_p4": False,
                "allow_messages": False
            },
            "normal_mode": {
                "allow_p1": True,
                "allow_p2": True,
                "allow_p3": True,
                "allow_p4": True,
                "allow_messages": True
            },
            "deep_work_hours": {
                "start": 9,  # 9 AM
                "end": 12,   # 12 PM
                "allow_interrupts": False
            },
            "low_energy_hours": {
                "start": 14,  # 2 PM (post-lunch)
                "end": 16,    # 4 PM
                "reduce_notifications": True
            }
        }
    
    async def start_focus_mode(
        self,
        duration_minutes: int = 25,
        task_name: Optional[str] = None
    ) -> Dict:
        """
        Start focus mode (Pomodoro-style)
        """
        
        self.focus_mode = True
        self.focus_start = datetime.now()
        self.focus_duration = duration_minutes
        
        logger.info(f"Focus mode started: {duration_minutes}min for '{task_name}'")
        
        return {
            "success": True,
            "focus_mode": True,
            "duration_minutes": duration_minutes,
            "task_name": task_name,
            "start_time": self.focus_start.isoformat(),
            "end_time": (
                self.focus_start + timedelta(minutes=duration_minutes)
            ).isoformat()
        }
    
    async def end_focus_mode(self) -> Dict:
        """
        End focus mode and flush queued notifications
        """
        
        if not self.focus_mode:
            return {
                "success": False,
                "error": "Focus mode not active"
            }
        
        duration = (datetime.now() - self.focus_start).total_seconds() / 60
        
        self.focus_mode = False
        queued_count = len(self.notifications_queue)
        
        logger.info(f"Focus mode ended: {duration:.1f}min, {queued_count} queued")
        
        return {
            "success": True,
            "focus_mode": False,
            "duration_minutes": round(duration, 1),
            "queued_notifications": self.notifications_queue.copy(),
            "message": f"Focus session complete! {queued_count} notifications queued"
        }
    
    async def handle_notification(
        self,
        notification_type: str,
        priority: str,
        content: Dict,
        source: str = "system"
    ) -> Dict:
        """
        Intelligently handle an incoming notification
        
        Returns decision on whether to interrupt or queue
        """
        
        decision = self._should_interrupt(
            notification_type,
            priority,
            source
        )
        
        notification = {
            "id": f"notif_{datetime.now().timestamp()}",
            "type": notification_type,
            "priority": priority,
            "content": content,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "interrupted": decision["interrupt"]
        }
        
        if decision["interrupt"]:
            logger.info(f"INTERRUPT: {notification_type} - {priority}")
            return {
                "action": "interrupt",
                "notification": notification,
                "reason": decision["reason"]
            }
        else:
            # Queue for later
            self.notifications_queue.append(notification)
            logger.info(f"QUEUED: {notification_type} - {priority}")
            return {
                "action": "queue",
                "notification": notification,
                "reason": decision["reason"],
                "queued_count": len(self.notifications_queue)
            }
    
    def _should_interrupt(
        self,
        notification_type: str,
        priority: str,
        source: str
    ) -> Dict:
        """
        Decision logic for interruption
        """
        
        # Always interrupt for P1 emergencies
        if priority == "P1":
            return {
                "interrupt": True,
                "reason": "P1 emergency - always interrupt"
            }
        
        # Check focus mode
        if self.focus_mode:
            rules = self.notification_rules["focus_mode"]
            
            # Check if time is up
            if self.focus_start:
                elapsed = (datetime.now() - self.focus_start).total_seconds() / 60
                if elapsed >= self.focus_duration:
                    self.focus_mode = False
                    return {
                        "interrupt": True,
                        "reason": "Focus session complete"
                    }
            
            # Apply focus mode rules
            if priority == "P2" and rules["allow_p2"]:
                return {
                    "interrupt": True,
                    "reason": "P2 allowed in focus mode"
                }
            
            return {
                "interrupt": False,
                "reason": "Focus mode active - queuing notification"
            }
        
        # Check deep work hours
        current_hour = datetime.now().hour
        deep_work = self.notification_rules["deep_work_hours"]
        
        if deep_work["start"] <= current_hour < deep_work["end"]:
            if not deep_work["allow_interrupts"] and priority not in ["P1"]:
                return {
                    "interrupt": False,
                    "reason": "Deep work hours - queuing notification"
                }
        
        # Check low energy hours (reduce non-urgent notifications)
        low_energy = self.notification_rules["low_energy_hours"]
        if low_energy["start"] <= current_hour < low_energy["end"]:
            if low_energy["reduce_notifications"] and priority in ["P3", "P4"]:
                return {
                    "interrupt": False,
                    "reason": "Low energy period - reducing notifications"
                }
        
        # Normal mode - allow most notifications
        return {
            "interrupt": True,
            "reason": "Normal mode - notification allowed"
        }
    
    async def get_queued_notifications(
        self,
        clear: bool = False
    ) -> List[Dict]:
        """
        Get queued notifications
        """
        
        notifications = self.notifications_queue.copy()
        
        if clear:
            self.notifications_queue = []
            logger.info(f"Cleared {len(notifications)} queued notifications")
        
        return notifications
    
    async def set_deep_work_window(
        self,
        start_hour: int,
        end_hour: int
    ) -> Dict:
        """
        Set custom deep work hours
        """
        
        if not (0 <= start_hour < 24 and 0 <= end_hour < 24):
            return {
                "success": False,
                "error": "Hours must be between 0-23"
            }
        
        if start_hour >= end_hour:
            return {
                "success": False,
                "error": "Start hour must be before end hour"
            }
        
        self.notification_rules["deep_work_hours"]["start"] = start_hour
        self.notification_rules["deep_work_hours"]["end"] = end_hour
        
        logger.info(f"Deep work window set: {start_hour}:00 - {end_hour}:00")
        
        return {
            "success": True,
            "deep_work_window": f"{start_hour}:00 - {end_hour}:00"
        }
    
    async def get_focus_status(self) -> Dict:
        """
        Get current focus mode status
        """
        
        if not self.focus_mode:
            return {
                "focus_mode": False,
                "queued_notifications": len(self.notifications_queue)
            }
        
        elapsed = (datetime.now() - self.focus_start).total_seconds() / 60
        remaining = max(0, self.focus_duration - elapsed)
        
        return {
            "focus_mode": True,
            "start_time": self.focus_start.isoformat(),
            "elapsed_minutes": round(elapsed, 1),
            "remaining_minutes": round(remaining, 1),
            "progress_percent": min(100, (elapsed / self.focus_duration) * 100),
            "queued_notifications": len(self.notifications_queue)
        }
    
    async def snooze_notification(
        self,
        notification_id: str,
        snooze_minutes: int = 15
    ) -> Dict:
        """
        Snooze a notification
        """
        
        notification = next(
            (n for n in self.notifications_queue if n["id"] == notification_id),
            None
        )
        
        if not notification:
            return {
                "success": False,
                "error": "Notification not found"
            }
        
        # Update notification with snooze time
        notification["snoozed_until"] = (
            datetime.now() + timedelta(minutes=snooze_minutes)
        ).isoformat()
        
        logger.info(f"Notification snoozed: {notification_id} for {snooze_minutes}min")
        
        return {
            "success": True,
            "notification_id": notification_id,
            "snoozed_until": notification["snoozed_until"]
        }
    
    async def get_interrupt_stats(self) -> Dict:
        """
        Get statistics about interruptions
        """
        
        total_notifications = len(self.notifications_queue)
        
        # Count by priority
        priority_counts = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
        for notif in self.notifications_queue:
            priority = notif.get("priority", "P3")
            if priority in priority_counts:
                priority_counts[priority] += 1
        
        # Count interrupted vs queued
        interrupted = sum(1 for n in self.notifications_queue if n.get("interrupted"))
        queued = total_notifications - interrupted
        
        return {
            "total_notifications": total_notifications,
            "interrupted": interrupted,
            "queued": queued,
            "priority_breakdown": priority_counts,
            "focus_mode_active": self.focus_mode,
            "deep_work_window": f"{self.notification_rules['deep_work_hours']['start']}:00 - {self.notification_rules['deep_work_hours']['end']}:00"
        }