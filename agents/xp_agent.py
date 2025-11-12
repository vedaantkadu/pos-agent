"""
XP Agent - Gamification and progress tracking
"""

from datetime import datetime
from typing import Dict, List
import json
import os
import logging

logger = logging.getLogger(__name__)


class XPAgent:
    """Handles gamification, XP tracking, and avatar progression"""
    
    def __init__(self):
        self.data_file = "xp_data.json"
        self.avatars = {
            "Producer": {"level": 1, "xp": 0, "color": "#FF6B6B"},
            "Administrator": {"level": 1, "xp": 0, "color": "#4ECDC4"},
            "Entrepreneur": {"level": 1, "xp": 0, "color": "#FFE66D"},
            "Integrator": {"level": 1, "xp": 0, "color": "#95E1D3"}
        }
        self.xp_per_level = 100
        self.achievements = []
        self._load_data()
        
    async def initialize(self):
        """Initialize XP system"""
        logger.info("✅ XP Agent initialized")
        return True
    
    def _load_data(self):
        """Load XP data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.avatars = data.get('avatars', self.avatars)
                    self.achievements = data.get('achievements', [])
                    logger.info("XP data loaded from file")
        except Exception as e:
            logger.error(f"Error loading XP data: {e}")
    
    def _save_data(self):
        """Save XP data to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump({
                    'avatars': self.avatars,
                    'achievements': self.achievements
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving XP data: {e}")
    
    def award_xp(
        self,
        avatar: str,
        xp_amount: int,
        reason: str = "Task completed"
    ) -> Dict:
        """
        Award XP to an avatar
        
        Returns info about level ups and achievements
        """
        
        if avatar not in self.avatars:
            return {"error": "Invalid avatar"}
        
        old_level = self.avatars[avatar]["level"]
        self.avatars[avatar]["xp"] += xp_amount
        
        # Check for level up
        new_xp = self.avatars[avatar]["xp"]
        new_level = (new_xp // self.xp_per_level) + 1
        
        leveled_up = new_level > old_level
        
        if leveled_up:
            self.avatars[avatar]["level"] = new_level
            # Award achievement
            achievement = {
                "avatar": avatar,
                "title": f"{avatar} Level {new_level}!",
                "description": f"Reached level {new_level}",
                "timestamp": datetime.now().isoformat(),
                "icon": "🏆"
            }
            self.achievements.append(achievement)
            logger.info(f"🎉 {avatar} leveled up to {new_level}!")
        
        self._save_data()
        
        return {
            "avatar": avatar,
            "xp_awarded": xp_amount,
            "reason": reason,
            "new_xp": new_xp,
            "new_level": new_level,
            "leveled_up": leveled_up,
            "xp_to_next_level": self.xp_per_level - (new_xp % self.xp_per_level)
        }
    
    def get_avatar_status(self, avatar: str) -> Dict:
        """Get status of a specific avatar"""
        if avatar not in self.avatars:
            return {"error": "Invalid avatar"}
        
        data = self.avatars[avatar]
        xp_in_level = data["xp"] % self.xp_per_level
        
        return {
            "avatar": avatar,
            "level": data["level"],
            "total_xp": data["xp"],
            "xp_in_level": xp_in_level,
            "xp_to_next_level": self.xp_per_level - xp_in_level,
            "progress_percent": (xp_in_level / self.xp_per_level) * 100,
            "color": data["color"]
        }
    
    async def get_all_avatars(self) -> List[Dict]:
        """Get status of all avatars"""
        return [
            self.get_avatar_status(avatar)
            for avatar in self.avatars.keys()
        ]
    
    def get_achievements(self, limit: int = 10) -> List[Dict]:
        """Get recent achievements"""
        return self.achievements[-limit:]
    
    def calculate_task_xp(
        self,
        priority: str,
        complexity: str = "medium"
    ) -> int:
        """Calculate XP for a task"""
        base_xp = {
            "P1": 50,
            "P2": 30,
            "P3": 20,
            "P4": 10
        }
        
        complexity_multiplier = {
            "low": 1.0,
            "medium": 1.5,
            "high": 2.0
        }
        
        return int(
            base_xp.get(priority, 20) * 
            complexity_multiplier.get(complexity, 1.0)
        )
    
    def get_leaderboard(self) -> List[Dict]:
        """Get avatar leaderboard"""
        avatars = []
        for name, data in self.avatars.items():
            avatars.append({
                "avatar": name,
                "level": data["level"],
                "total_xp": data["xp"],
                "color": data["color"]
            })
        
        # Sort by level, then by XP
        avatars.sort(key=lambda x: (x["level"], x["total_xp"]), reverse=True)
        return avatars
    
    def get_daily_summary(self) -> Dict:
        """Get today's XP summary"""
        today = datetime.now().date().isoformat()
        
        today_achievements = [
            a for a in self.achievements
            if a["timestamp"].startswith(today)
        ]
        
        total_today = sum(
            self.avatars[avatar]["xp"] 
            for avatar in self.avatars
        )
        
        return {
            "date": today,
            "achievements": len(today_achievements),
            "total_xp_earned": total_today,
            "recent_achievements": today_achievements[-5:]
        }