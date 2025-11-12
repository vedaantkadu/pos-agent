"""
Report Agent - REAL DATA FROM OTHER AGENTS
Generates reports using actual task, calendar, and email data
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ReportAgent:
    """Report generation using real data from other agents"""
    
    def __init__(self):
        self.report_history = []
        self.task_agent = None
        self.calendar_agent = None
        self.email_agent = None
        self.xp_agent = None
        
    async def initialize(self):
        """Initialize"""
        logger.info("✅ Report Agent ready")
        return True
    
    def set_agents(self, task_agent, calendar_agent, email_agent, xp_agent):
        """Set references to other agents for data access"""
        self.task_agent = task_agent
        self.calendar_agent = calendar_agent
        self.email_agent = email_agent
        self.xp_agent = xp_agent
        logger.info("✅ Report Agent connected to other agents")
    
    async def generate_daily_report(self, date: Optional[datetime] = None) -> Dict:
        """Generate daily report using REAL data from agents"""
        
        if date is None:
            date = datetime.now()
        
        report_date = date.date()
        
        try:
            # ===== GET REAL TASK DATA =====
            all_tasks = []
            tasks_completed_today = []
            
            if self.task_agent:
                try:
                    all_tasks = await self.task_agent.get_tasks(limit=1000)
                    
                    # Filter tasks completed today
                    for task in all_tasks:
                        if task.get("status") == "Done":
                            created_date = task.get("created", "")
                            if created_date:
                                try:
                                    task_date = datetime.fromisoformat(created_date.replace('Z', '')).date()
                                    if task_date == report_date:
                                        tasks_completed_today.append(task)
                                except:
                                    pass
                    
                    logger.info(f"📊 Found {len(tasks_completed_today)} tasks completed today")
                except Exception as e:
                    logger.error(f"Error fetching tasks: {e}")
            
            # ===== GET REAL CALENDAR DATA =====
            events_today = []
            
            if self.calendar_agent:
                try:
                    events_today = await self.calendar_agent.get_today_events()
                    logger.info(f"📅 Found {len(events_today)} events today")
                except Exception as e:
                    logger.error(f"Error fetching events: {e}")
            
            # ===== GET REAL EMAIL DATA =====
            emails_processed = []
            
            if self.email_agent:
                try:
                    emails_processed = await self.email_agent.get_recent_emails(max_results=50)
                    logger.info(f"📧 Found {len(emails_processed)} recent emails")
                except Exception as e:
                    logger.error(f"Error fetching emails: {e}")
            
            # ===== GET REAL XP DATA =====
            xp_data = {}
            avatars_status = []
            
            if self.xp_agent:
                try:
                    avatars_status = await self.xp_agent.get_all_avatars()
                    for avatar in avatars_status:
                        xp_data[avatar['avatar']] = avatar['total_xp']
                    logger.info(f"🏆 Retrieved XP data for {len(avatars_status)} avatars")
                except Exception as e:
                    logger.error(f"Error fetching XP: {e}")
            
            # ===== ANALYZE TASK DATA =====
            total_tasks = len(tasks_completed_today)
            
            # Priority breakdown
            priority_breakdown = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
            for task in tasks_completed_today:
                priority = task.get("priority", "P3")
                if priority in priority_breakdown:
                    priority_breakdown[priority] += 1
            
            # Avatar breakdown
            avatar_breakdown = {
                "Producer": 0,
                "Administrator": 0,
                "Entrepreneur": 0,
                "Integrator": 0
            }
            for task in tasks_completed_today:
                avatar = task.get("avatar", "Producer")
                if avatar in avatar_breakdown:
                    avatar_breakdown[avatar] += 1
            
            # Calculate productivity score (0-100)
            productivity_score = min(100, (total_tasks * 10) + (priority_breakdown["P1"] * 15) + (priority_breakdown["P2"] * 10))
            
            # ===== GENERATE INSIGHTS =====
            insights = []
            
            if priority_breakdown["P1"] > 0:
                insights.append(f"🔥 Completed {priority_breakdown['P1']} urgent task(s) - great prioritization!")
            
            if total_tasks >= 5:
                insights.append(f"💪 Productive day! Completed {total_tasks} tasks")
            elif total_tasks == 0:
                insights.append("🤔 No tasks completed today - time to plan tomorrow?")
            else:
                insights.append(f"✅ Completed {total_tasks} task(s) today")
            
            if len(events_today) >= 3:
                insights.append(f"📅 Busy calendar with {len(events_today)} events")
            elif len(events_today) > 0:
                insights.append(f"📅 Attended {len(events_today)} event(s)")
            
            if len(emails_processed) > 20:
                insights.append(f"📧 High email activity: {len(emails_processed)} emails")
            
            # Dominant avatar
            if sum(avatar_breakdown.values()) > 0:
                dominant = max(avatar_breakdown, key=avatar_breakdown.get)
                if avatar_breakdown[dominant] > 0:
                    insights.append(f"🎭 Mostly {dominant} mode today ({avatar_breakdown[dominant]} tasks)")
            
            # XP insights
            if xp_data:
                total_xp_today = sum(xp_data.values())
                insights.append(f"🏆 Total XP earned: {total_xp_today}")
            
            # ===== BUILD REPORT =====
            report = {
                "date": report_date.isoformat(),
                "type": "daily",
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_tasks_completed": total_tasks,
                    "events_attended": len(events_today),
                    "emails_processed": len(emails_processed),
                    "productivity_score": productivity_score,
                    "total_xp": sum(xp_data.values()) if xp_data else 0
                },
                "priority_breakdown": priority_breakdown,
                "avatar_breakdown": avatar_breakdown,
                "insights": insights,
                "tasks_detail": tasks_completed_today[:10],  # Top 10 tasks
                "events_detail": events_today[:5],  # Top 5 events
                "xp_status": avatars_status,
                "recommendations": self._generate_recommendations(
                    total_tasks, 
                    priority_breakdown, 
                    avatar_breakdown, 
                    len(events_today)
                )
            }
            
            self.report_history.append(report)
            logger.info(f"📊 Daily report generated: {total_tasks} tasks, {len(events_today)} events")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Daily report generation error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e), "date": report_date.isoformat()}
    
    async def generate_weekly_report(self, weeks_back: int = 1) -> Dict:
        """Generate weekly report using real data"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks_back)
        
        try:
            # Generate daily reports for each day in the week
            daily_reports = []
            current_date = start_date
            
            while current_date <= end_date:
                daily_report = await self.generate_daily_report(current_date)
                if "error" not in daily_report:
                    daily_reports.append(daily_report)
                current_date += timedelta(days=1)
            
            if not daily_reports:
                return {"error": "No data available for weekly report"}
            
            # Aggregate data
            total_tasks = sum(r.get("summary", {}).get("total_tasks_completed", 0) for r in daily_reports)
            total_events = sum(r.get("summary", {}).get("events_attended", 0) for r in daily_reports)
            total_emails = sum(r.get("summary", {}).get("emails_processed", 0) for r in daily_reports)
            avg_productivity = sum(r.get("summary", {}).get("productivity_score", 0) for r in daily_reports) / len(daily_reports)
            total_xp = sum(r.get("summary", {}).get("total_xp", 0) for r in daily_reports)
            
            # Priority totals
            priority_totals = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
            for report in daily_reports:
                breakdown = report.get("priority_breakdown", {})
                for priority, count in breakdown.items():
                    if priority in priority_totals:
                        priority_totals[priority] += count
            
            # Avatar totals
            avatar_totals = {
                "Producer": 0,
                "Administrator": 0,
                "Entrepreneur": 0,
                "Integrator": 0
            }
            for report in daily_reports:
                breakdown = report.get("avatar_breakdown", {})
                for avatar, count in breakdown.items():
                    if avatar in avatar_totals:
                        avatar_totals[avatar] += count
            
            # Trends
            task_counts = [r.get("summary", {}).get("total_tasks_completed", 0) for r in daily_reports]
            task_trend = self._calculate_trend(task_counts)
            
            productivity_scores = [r.get("summary", {}).get("productivity_score", 0) for r in daily_reports]
            productivity_trend = self._calculate_trend(productivity_scores)
            
            # Insights
            insights = []
            
            if task_trend == "increasing":
                insights.append("📈 Productivity trending up throughout the week!")
            elif task_trend == "decreasing":
                insights.append("📉 Productivity dip detected - consider reassessing priorities")
            else:
                insights.append("📊 Stable productivity throughout the week")
            
            if total_tasks >= 35:  # 5 per day
                insights.append(f"💪 Excellent week! Completed {total_tasks} tasks")
            elif total_tasks >= 21:  # 3 per day
                insights.append(f"✅ Good week! Completed {total_tasks} tasks")
            else:
                insights.append(f"📝 Completed {total_tasks} tasks this week")
            
            # Find most productive day
            if daily_reports:
                most_productive = max(daily_reports, key=lambda x: x.get("summary", {}).get("total_tasks_completed", 0))
                most_productive_date = most_productive.get("date", "")
                most_productive_tasks = most_productive.get("summary", {}).get("total_tasks_completed", 0)
                if most_productive_tasks > 0:
                    insights.append(f"🌟 Most productive day: {most_productive_date} ({most_productive_tasks} tasks)")
            
            # Dominant avatar
            if sum(avatar_totals.values()) > 0:
                dominant_avatar = max(avatar_totals, key=avatar_totals.get)
                insights.append(f"🎭 This week you operated mostly in {dominant_avatar} mode")
            
            return {
                "date": datetime.now().isoformat(),
                "type": "weekly",
                "period": {
                    "start": start_date.date().isoformat(),
                    "end": end_date.date().isoformat(),
                    "days": len(daily_reports)
                },
                "summary": {
                    "total_tasks": total_tasks,
                    "total_events": total_events,
                    "total_emails": total_emails,
                    "avg_daily_tasks": round(total_tasks / len(daily_reports), 1),
                    "avg_productivity_score": round(avg_productivity, 1),
                    "total_xp": total_xp
                },
                "priority_breakdown": priority_totals,
                "avatar_breakdown": avatar_totals,
                "trends": {
                    "tasks": task_trend,
                    "productivity": productivity_trend
                },
                "insights": insights,
                "daily_reports": daily_reports,
                "recommendations": self._generate_weekly_recommendations(
                    total_tasks,
                    priority_totals,
                    avatar_totals,
                    task_trend
                )
            }
            
        except Exception as e:
            logger.error(f"❌ Weekly report error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from values"""
        if len(values) < 2:
            return "stable"
        
        try:
            first_half = sum(values[:len(values)//2]) / (len(values)//2) if len(values)//2 > 0 else 0
            second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            
            diff = second_half - first_half
            
            if diff > first_half * 0.1:
                return "increasing"
            elif diff < -first_half * 0.1:
                return "decreasing"
            else:
                return "stable"
        except:
            return "stable"
    
    def _generate_recommendations(self, total_tasks: int, priority_breakdown: Dict, avatar_breakdown: Dict, events_count: int) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        if total_tasks < 3:
            recommendations.append("📝 Consider setting more daily goals to boost productivity")
        
        if priority_breakdown["P1"] > 5:
            recommendations.append("⚠️ Many urgent tasks - review your planning process")
        
        if priority_breakdown["P4"] > priority_breakdown["P1"] + priority_breakdown["P2"]:
            recommendations.append("🎯 Focus on higher priority tasks for better impact")
        
        if events_count > 5:
            recommendations.append("📅 Heavy meeting schedule - ensure time for deep work")
        
        # Avatar balance
        avatar_values = list(avatar_breakdown.values())
        if avatar_values and max(avatar_values) > sum(avatar_values) * 0.6:
            dominant = max(avatar_breakdown, key=avatar_breakdown.get)
            recommendations.append(f"⚖️ Consider balancing with other roles beyond {dominant}")
        
        if not recommendations:
            recommendations.append("✨ Great balance! Keep up the good work")
        
        return recommendations
    
    def _generate_weekly_recommendations(self, total_tasks: int, priority_breakdown: Dict, avatar_breakdown: Dict, trend: str) -> List[str]:
        """Generate weekly recommendations"""
        recommendations = []
        
        if trend == "decreasing":
            recommendations.append("📉 Productivity declining - schedule a weekly review")
        elif trend == "increasing":
            recommendations.append("🚀 Great momentum! Maintain this upward trend")
        
        if total_tasks < 21:  # Less than 3 per day
            recommendations.append("📊 Low task completion - break down larger goals into smaller tasks")
        
        if priority_breakdown["P1"] > total_tasks * 0.3:
            recommendations.append("🔥 Too many urgent tasks - improve planning to reduce firefighting")
        
        return recommendations
    
    async def get_performance_metrics(self, days: int = 7) -> Dict:
        """Get performance metrics for specified period"""
        cutoff = datetime.now() - timedelta(days=days)
        
        recent = [
            r for r in self.report_history
            if datetime.fromisoformat(r["date"]) >= cutoff.date()
        ]
        
        if not recent:
            # Generate fresh report if no history
            try:
                report = await self.generate_daily_report()
                recent = [report]
            except:
                return {"error": "No data available"}
        
        avg_tasks = sum(r.get("summary", {}).get("total_tasks_completed", 0) for r in recent) / len(recent) if recent else 0
        total_xp = sum(r.get("summary", {}).get("total_xp", 0) for r in recent)
        
        return {
            "period_days": days,
            "reports_count": len(recent),
            "avg_tasks_per_day": round(avg_tasks, 1),
            "total_xp": total_xp,
            "total_tasks": sum(r.get("summary", {}).get("total_tasks_completed", 0) for r in recent)
        }