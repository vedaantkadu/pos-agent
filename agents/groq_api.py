"""
Groq Agent - AI Chatbot Integration
Uses Groq API for intelligent conversations and assistance
"""

import os
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GroqAgent:
    """Groq-powered AI chatbot agent"""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            logger.warning("⚠️ GROQ_API_KEY not found in environment")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
        
        # Conversation history for context
        self.conversation_history = []
        self.max_history = 10  # Keep last 10 messages for context

    async def initialize(self):
        """Initialize Groq agent"""
        if not self.client:
            logger.error("❌ Groq Agent failed: No API key")
            return False
        
        logger.info("✅ Groq Agent initialized")
        return True

    async def chat(
        self, 
        user_message: str, 
        system_context: Optional[Dict] = None,
        model: str = "llama-3.3-70b-versatile"
    ) -> Dict:
        """
        Send a message to Groq and get AI response
        
        Args:
            user_message: The user's input
            system_context: Optional context (tasks, calendar, etc.)
            model: Groq model to use (default: llama-3.3-70b-versatile)
        
        Returns:
            Dict with response, success status, and metadata
        """
        if not self.client:
            return {
                "success": False,
                "error": "Groq API not configured",
                "response": "I'm unable to connect to the AI service. Please check your API key."
            }

        try:
            # Build system prompt with context
            system_prompt = self._build_system_prompt(system_context)
            
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Keep history manageable
            if len(self.conversation_history) > self.max_history * 2:
                self.conversation_history = self.conversation_history[-(self.max_history * 2):]
            
            # Prepare messages for API
            messages = [
                {"role": "system", "content": system_prompt},
                *self.conversation_history
            ]
            
            # Call Groq API
            logger.info(f"🤖 Sending message to Groq: {user_message[:50]}...")
            
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=0.7,
                max_tokens=2048,
                top_p=0.9,
                stream=False
            )
            
            # Extract response
            ai_response = chat_completion.choices[0].message.content
            
            # Add AI response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            logger.info(f"✅ Got response from Groq ({len(ai_response)} chars)")
            
            return {
                "success": True,
                "response": ai_response,
                "model": model,
                "tokens_used": chat_completion.usage.total_tokens if hasattr(chat_completion, 'usage') else None,
                "conversation_length": len(self.conversation_history) // 2
            }
            
        except Exception as e:
            logger.error(f"❌ Groq API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"I encountered an error: {str(e)}"
            }

    def _build_system_prompt(self, context: Optional[Dict] = None) -> str:
        """Build system prompt with context awareness"""
        
        base_prompt = """You are Martin, an AI assistant integrated into Present OS - a productivity system based on the PAEI framework.

Your role:
- Help users manage tasks, calendar, emails, and productivity
- Provide intelligent advice and insights
- Be conversational, helpful, and proactive
- Use the user's context (tasks, calendar, weather) to give relevant suggestions

Personality:
- Professional but friendly
- Concise and actionable
- Empathetic and understanding
- Solution-oriented

When responding:
- Be direct and helpful
- Suggest actions when appropriate
- Reference the user's context naturally
- Keep responses focused and practical"""

        if context:
            context_info = "\n\nCurrent Context:"
            
            if context.get("task_backlog"):
                context_info += f"\n- You have {context['task_backlog']} pending tasks"
            
            if context.get("energy_level"):
                context_info += f"\n- Current energy level: {context['energy_level']}%"
            
            if context.get("weather"):
                context_info += f"\n- Weather: {context['weather']}"
            
            if context.get("upcoming_events"):
                context_info += f"\n- Upcoming events: {context['upcoming_events']}"
            
            base_prompt += context_info

        return base_prompt

    async def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("🧹 Conversation history cleared")
        return {"success": True, "message": "History cleared"}

    async def get_conversation_summary(self) -> Dict:
        """Get summary of current conversation"""
        return {
            "message_count": len(self.conversation_history),
            "last_messages": self.conversation_history[-4:] if self.conversation_history else []
        }

    async def suggest_actions(self, user_context: Dict) -> Dict:
        """Proactively suggest actions based on context"""
        
        if not self.client:
            return {"success": False, "error": "Groq API not configured"}
        
        try:
            prompt = f"""Based on this user context, suggest 3-5 helpful actions they could take:

Context:
- Tasks pending: {user_context.get('task_backlog', 0)}
- Energy level: {user_context.get('energy_level', 'unknown')}%
- Weather: {user_context.get('weather', 'unknown')}
- Time: {user_context.get('current_time', 'unknown')}

Provide concise, actionable suggestions in a bullet list."""

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful productivity assistant."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.8,
                max_tokens=500
            )
            
            suggestions = chat_completion.choices[0].message.content
            
            return {
                "success": True,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating suggestions: {e}")
            return {
                "success": False,
                "error": str(e)
            }