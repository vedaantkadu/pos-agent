import React, { useState, useEffect, useRef } from 'react';
import { Send, Calendar, CheckSquare, Mail, Cloud, Trophy, TrendingUp, User, Menu, X, MessageSquare, Search, ExternalLink, Inbox, Bell, ChevronLeft, ChevronRight, Settings, LogOut, AlertCircle, Check, Users, FileText, Focus, Lock, Eye, EyeOff, Mic, MicOff, Loader, Sparkles, Bot, Trash2 } from 'lucide-react';

const API_URL = 'http://localhost:8000';

// Add encoding fix function
const fixEncoding = (text) => {
  if (!text) return text;
  return text
    .replace(/Ã¢Å"â€¦/g, '✓')
    .replace(/Ã¢â‚¬Â¦/g, '…')
    .replace(/Ã¢â‚¬Å"/g, '"')
    .replace(/Ã¢â‚¬Â/g, '"')
    .replace(/Ã¢â‚¬Â¢/g, '•');
};

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userName, setUserName] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [context, setContext] = useState(null);
  const [avatars, setAvatars] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [events, setEvents] = useState([]);
  const [emails, setEmails] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [weather, setWeather] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef(null);
  const [taskPage, setTaskPage] = useState(1);
  const [eventPage, setEventPage] = useState(1);
  const [emailPage, setEmailPage] = useState(1);
  const [contactPage, setContactPage] = useState(1);
  const itemsPerPage = 5;

  // Groq Chat State
  const [chatHistory, setChatHistory] = useState([]);
  const [groqLoading, setGroqLoading] = useState(false);
  const [groqInput, setGroqInput] = useState('');
  const chatEndRef = useRef(null);

  useEffect(() => {
    const storedAuth = localStorage.getItem('pos_auth');
    if (storedAuth) {
      const authData = JSON.parse(storedAuth);
      setIsAuthenticated(true);
      setUserName(authData.name);
      setUserEmail(authData.email);
      loadDashboardData();
      loadNotifications();
      loadChatHistory();
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      const interval = setInterval(loadNotifications, 30000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatHistory = () => {
    const stored = localStorage.getItem('pos_chat_history');
    if (stored) {
      setChatHistory(JSON.parse(stored));
    }
  };

  const saveChatHistory = (history) => {
    localStorage.setItem('pos_chat_history', JSON.stringify(history));
  };

  const loadNotifications = () => {
    const stored = localStorage.getItem('pos_notifications');
    if (stored) {
      setNotifications(JSON.parse(stored));
    }
  };

  const addNotification = (type, message) => {
    const newNotif = { id: Date.now(), type, message, time: 'Just now', read: false };
    const updated = [newNotif, ...notifications].slice(0, 20);
    setNotifications(updated);
    localStorage.setItem('pos_notifications', JSON.stringify(updated));
  };

  const loadDashboardData = async () => {
    try {
      const [contextRes, avatarsRes, tasksRes, eventsRes, weatherRes, emailsRes, contactsRes] = await Promise.all([
        fetch(`${API_URL}/context`),
        fetch(`${API_URL}/xp/avatars`),
        fetch(`${API_URL}/tasks?limit=50`),
        fetch(`${API_URL}/calendar/today`),
        fetch(`${API_URL}/weather/current`),
        fetch(`${API_URL}/email/recent?max_results=50`),
        fetch(`${API_URL}/contacts`)
      ]);

      setContext(await contextRes.json());
      setAvatars((await avatarsRes.json()).avatars || []);
      setTasks((await tasksRes.json()).tasks || []);
      setEvents((await eventsRes.json()).events || []);
      setWeather(await weatherRes.json());
      setEmails((await emailsRes.json()).emails || []);
      const contactData = await contactsRes.json();
      setContacts(contactData.contacts || []);
      console.log('Contacts loaded:', contactData.contacts?.length || 0);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    }
  };

  const loadContacts = async () => {
    try {
      const res = await fetch(`${API_URL}/contacts`);
      const data = await res.json();
      setContacts(data.contacts || []);
      console.log('Contacts reloaded:', data.contacts?.length || 0);
    } catch (error) {
      console.error('Error loading contacts:', error);
    }
  };

  const handleSubmit = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();
      setResponse(data);
      
      if (data.agents && data.agents.length > 0) {
        data.agents.forEach(agent => addNotification(agent, `✓ ${agent} Agent activated`));
      }
      
      setQuery('');
      
      const isContactAction = data.agents && data.agents.includes('contact');
      
      if (isContactAction) {
        console.log('Contact action detected, reloading contacts...');
        setTimeout(async () => {
          await loadContacts();
          addNotification('contact', '✓ Contacts updated');
        }, 500);
      }
      
      setTimeout(loadDashboardData, 1500);
      
    } catch (error) {
      console.error('Error:', error);
      setResponse({ response: 'Error processing request', error: error.message });
      addNotification('system', `❌ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGroqChat = async () => {
    if (!groqInput.trim()) return;
    
    const userMessage = {
      role: 'user',
      content: groqInput,
      timestamp: new Date().toISOString()
    };

    const updatedHistory = [...chatHistory, userMessage];
    setChatHistory(updatedHistory);
    saveChatHistory(updatedHistory);
    setGroqInput('');
    setGroqLoading(true);

    try {
      const res = await fetch(`${API_URL}/groq/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMessage.content,
          context: {
            task_backlog: tasks.length,
            energy_level: context?.energy_level,
            weather: weather?.condition,
            upcoming_events: events.length
          }
        })
      });
      
      const data = await res.json();
      
      if (data.success) {
        const aiMessage = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString(),
          model: data.model,
          tokens: data.tokens_used
        };
        
        const finalHistory = [...updatedHistory, aiMessage];
        setChatHistory(finalHistory);
        saveChatHistory(finalHistory);
        addNotification('groq', '🤖 Martin responded');
      } else {
        addNotification('groq', `❌ Error: ${data.error}`);
      }
    } catch (error) {
      console.error('Groq chat error:', error);
      addNotification('groq', `❌ Chat error: ${error.message}`);
    } finally {
      setGroqLoading(false);
    }
  };

  const clearChatHistory = () => {
    setChatHistory([]);
    localStorage.removeItem('pos_chat_history');
    addNotification('groq', '🧹 Chat history cleared');
  };

  const startRecording = async () => {
    try {
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = false;
        recognitionRef.current.lang = 'en-US';

        recognitionRef.current.onstart = () => {
          setIsRecording(true);
          addNotification('system', '🎤 Listening...');
        };

        recognitionRef.current.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          if (activeTab === 'groq') {
            setGroqInput(transcript);
          } else {
            setQuery(transcript);
          }
          addNotification('system', `🎤 Voice: "${transcript}"`);
          setIsRecording(false);
        };

        recognitionRef.current.onerror = (event) => {
          console.error('Speech recognition error:', event.error);
          addNotification('system', `❌ Voice error: ${event.error}`);
          setIsRecording(false);
        };

        recognitionRef.current.onend = () => {
          setIsRecording(false);
        };

        recognitionRef.current.start();
      } else {
        addNotification('system', '❌ Speech recognition not supported in this browser');
      }
    } catch (error) {
      console.error('Microphone error:', error);
      addNotification('system', '❌ Microphone access denied');
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }
  };

  const markNotificationRead = (id) => {
    const updated = notifications.map(n => n.id === id ? { ...n, read: true } : n);
    setNotifications(updated);
    localStorage.setItem('pos_notifications', JSON.stringify(updated));
  };

  const getPriorityColor = (priority) => {
    const colors = { P1: 'bg-red-500', P2: 'bg-orange-500', P3: 'bg-blue-500', P4: 'bg-gray-500' };
    return colors[priority] || 'bg-gray-500';
  };

  const getAvatarColor = (avatar) => {
    const colors = {
      Producer: 'from-red-500 to-pink-500',
      Administrator: 'from-teal-500 to-cyan-500',
      Entrepreneur: 'from-yellow-500 to-orange-500',
      Integrator: 'from-green-500 to-emerald-500'
    };
    return colors[avatar] || 'from-gray-500 to-gray-600';
  };

  const AuthScreen = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showLogin, setShowLogin] = useState(true);
    const [authLoading, setAuthLoading] = useState(false);
    const [authError, setAuthError] = useState('');

    const handleAuth = async (e) => {
      e.preventDefault();
      setAuthError('');
      setAuthLoading(true);

      setTimeout(() => {
        if (email && password) {
          if (!showLogin && password.length < 6) {
            setAuthError('Password must be at least 6 characters');
            setAuthLoading(false);
            return;
          }
          const name = email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1);
          const authData = { email, name, timestamp: Date.now() };
          localStorage.setItem('pos_auth', JSON.stringify(authData));
          setUserName(name);
          setUserEmail(email);
          setIsAuthenticated(true);
          setAuthLoading(false);
          loadDashboardData();
          addNotification('system', showLogin ? `👋 Welcome back, ${name}!` : `🎉 Account created!`);
        } else {
          setAuthError('Please fill all fields');
          setAuthLoading(false);
        }
      }, 1000);
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-2xl shadow-2xl p-8">
            <div className="text-center mb-8">
              <div className="inline-block p-4 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-2xl mb-4">
                <div className="text-4xl font-bold text-white">M</div>
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Present OS</h1>
              <p className="text-gray-600">Your AI-Powered Productivity Assistant</p>
            </div>

            <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
              <button type="button" onClick={() => { setShowLogin(true); setAuthError(''); }}
                className={`flex-1 py-2 px-4 rounded-md transition-all ${showLogin ? 'bg-white text-indigo-600 shadow' : 'text-gray-600'}`}>
                Login
              </button>
              <button type="button" onClick={() => { setShowLogin(false); setAuthError(''); }}
                className={`flex-1 py-2 px-4 rounded-md transition-all ${!showLogin ? 'bg-white text-indigo-600 shadow' : 'text-gray-600'}`}>
                Sign Up
              </button>
            </div>

            <form onSubmit={handleAuth} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600" required disabled={authLoading} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
                <div className="relative">
                  <input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600 pr-12"
                    required minLength={showLogin ? 1 : 6} disabled={authLoading} />
                  <button type="button" onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500" disabled={authLoading}>
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>
              {authError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
                  <AlertCircle className="w-5 h-5" />
                  <p className="text-sm">{authError}</p>
                </div>
              )}
              <button type="submit" disabled={authLoading}
                className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50">
                {authLoading ? 'Processing...' : (showLogin ? 'Sign In' : 'Create Account')}
              </button>
            </form>
            <div className="mt-6 text-center text-sm text-gray-600">
              <p className="flex items-center justify-center gap-1"><Lock className="w-4 h-4" />Secure & Encrypted</p>
            </div>
          </div>
          <div className="mt-6 text-center text-white text-sm">
            <p>✨ Demo: demo@present.os | demo123</p>
          </div>
        </div>
      </div>
    );
  };

  const Pagination = ({ currentPage, totalItems, itemsPerPage, onPageChange }) => {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    if (totalPages <= 1) return null;
    return (
      <div className="flex items-center justify-center gap-2 mt-4">
        <button onClick={() => onPageChange(currentPage - 1)} disabled={currentPage === 1}
          className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">
          <ChevronLeft className="w-4 h-4" />
        </button>
        <span className="text-sm text-gray-600">Page {currentPage} of {totalPages}</span>
        <button onClick={() => onPageChange(currentPage + 1)} disabled={currentPage === totalPages}
          className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    );
  };

  const NotificationPanel = () => (
    <div className="absolute right-0 top-16 w-80 bg-white rounded-xl shadow-2xl z-50 max-h-96 overflow-y-auto">
      <div className="p-4 border-b"><h3 className="font-bold text-lg">Notifications</h3></div>
      <div className="divide-y">
        {notifications.length === 0 ? (
          <div className="p-8 text-center text-gray-500"><Bell className="w-12 h-12 mx-auto mb-2 opacity-50" /><p>No notifications</p></div>
        ) : (
          notifications.map((notif) => (
            <div key={notif.id} className={`p-4 hover:bg-gray-50 cursor-pointer ${!notif.read ? 'bg-blue-50' : ''}`} onClick={() => markNotificationRead(notif.id)}>
              <div className="flex items-start gap-3">
                <div className="flex-1">
                  <p className="text-sm font-medium">{fixEncoding(notif.message)}</p>
                  <p className="text-xs text-gray-500 mt-1">{notif.time}</p>
                </div>
                {!notif.read && <div className="w-2 h-2 bg-blue-600 rounded-full mt-2" />}
              </div>
            </div>
          ))
        )}
      </div>
      {notifications.length > 0 && (
        <div className="p-3 border-t text-center">
          <button onClick={() => {
            const updated = notifications.map(n => ({ ...n, read: true }));
            setNotifications(updated);
            localStorage.setItem('pos_notifications', JSON.stringify(updated));
          }} className="text-sm text-blue-600 hover:text-blue-800">
            Mark all as read
          </button>
        </div>
      )}
    </div>
  );

  const ProfilePanel = () => (
    <div className="absolute right-0 top-16 w-80 bg-white rounded-xl shadow-2xl z-50">
      <div className="p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
            {userName.substring(0, 2).toUpperCase()}
          </div>
          <div>
            <h3 className="font-bold text-lg">{userName}</h3>
            <p className="text-sm text-gray-600">{userEmail}</p>
          </div>
        </div>
        <div className="space-y-3">
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-100 transition-colors">
            <Settings className="w-5 h-5 text-gray-600" />
            <span className="text-sm font-medium">Settings</span>
          </button>
          <button onClick={() => { localStorage.removeItem('pos_auth'); localStorage.removeItem('pos_notifications'); setIsAuthenticated(false); }}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-red-50 text-red-600">
            <LogOut className="w-5 h-5" />
            <span className="text-sm font-medium">Sign Out</span>
          </button>
        </div>
        <div className="mt-6 pt-6 border-t">
          <h4 className="text-xs font-bold text-gray-500 uppercase mb-3">Activity Stats</h4>
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{tasks.length}</p>
              <p className="text-xs text-gray-600">Tasks</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{events.length}</p>
              <p className="text-xs text-gray-600">Events</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const ContactView = () => {
    const startIndex = (contactPage - 1) * itemsPerPage;
    const paginatedContacts = contacts.slice(startIndex, startIndex + itemsPerPage);

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold flex items-center gap-2"><Users className="w-6 h-6" />Contacts ({contacts.length})</h2>
          <div className="flex gap-2">
            <button onClick={loadContacts} className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 flex items-center gap-2 transition-colors">
              <TrendingUp className="w-4 h-4" />Refresh
            </button>
            <button onClick={() => setQuery('Add contact John Doe email john@example.com')} className="bg-pink-600 text-white px-4 py-2 rounded-lg hover:bg-pink-700 flex items-center gap-2 transition-colors">
              <Users className="w-4 h-4" />Add Contact
            </button>
          </div>
        </div>
        {contacts.length === 0 ? (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-xl font-bold text-gray-700 mb-2">No Contacts Yet</h3>
            <p className="text-gray-500 mb-6">Start building your network by adding contacts</p>
            <button onClick={() => setQuery('Add contact Jane Smith email jane@example.com')} className="bg-pink-600 text-white px-6 py-3 rounded-lg hover:bg-pink-700 transition-colors">
              Add Your First Contact
            </button>
          </div>
        ) : (
          <>
            <div className="grid gap-4">
              {paginatedContacts.map((contact) => (
                <div key={contact.id} className="bg-white rounded-xl shadow p-6 hover:shadow-lg transition-shadow">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-pink-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
                      {contact.name ? contact.name.substring(0, 2).toUpperCase() : 'UN'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-bold text-lg">{contact.name}</h3>
                      {contact.role && contact.company && <p className="text-sm text-gray-600">{contact.role} at {contact.company}</p>}
                      <div className="space-y-1 mt-2 text-sm">
                        {contact.email && <p className="flex items-center gap-2 text-gray-700"><Mail className="w-4 h-4 flex-shrink-0" /><span className="truncate">{contact.email}</span></p>}
                        {contact.phone && <p className="text-gray-700">📱 {contact.phone}</p>}
                      </div>
                      {contact.tags && contact.tags.length > 0 && (
                        <div className="flex gap-2 flex-wrap mt-2">
                          {contact.tags.map((tag, idx) => (
                            <span key={idx} className="px-2 py-1 bg-pink-100 text-pink-700 rounded text-xs">{tag}</span>
                          ))}
                        </div>
                      )}
                      <p className="text-xs text-gray-400 mt-2">Added: {new Date(contact.added_date).toLocaleDateString()}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <Pagination currentPage={contactPage} totalItems={contacts.length} itemsPerPage={itemsPerPage} onPageChange={setContactPage} />
          </>
        )}
      </div>
    );
  };

  const GroqChatView = () => {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Bot className="w-6 h-6 text-purple-600" />
            Chat with Martin (AI Assistant)
          </h2>
          <button 
            onClick={clearChatHistory}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 flex items-center gap-2 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Clear History
          </button>
        </div>

        {/* Chat Container */}
        <div className="bg-white rounded-xl shadow-lg flex flex-col" style={{ height: 'calc(100vh - 300px)' }}>
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {chatHistory.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center mb-4">
                  <Sparkles className="w-10 h-10 text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-700 mb-2">Start a conversation with Martin</h3>
                <p className="text-gray-500 mb-6 max-w-md">
                  I'm your AI assistant powered by Groq. I can help you with productivity, 
                  answer questions, and provide intelligent insights based on your tasks and schedule.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl">
                  <button 
                    onClick={() => setGroqInput('What tasks should I focus on today?')}
                    className="p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors text-left"
                  >
                    <p className="text-sm font-medium text-purple-900">📋 What tasks should I focus on?</p>
                  </button>
                  <button 
                    onClick={() => setGroqInput('Give me a productivity tip')}
                    className="p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors text-left"
                  >
                    <p className="text-sm font-medium text-blue-900">💡 Give me a productivity tip</p>
                  </button>
                  <button 
                    onClick={() => setGroqInput('How can I improve my work-life balance?')}
                    className="p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors text-left"
                  >
                    <p className="text-sm font-medium text-green-900">🌱 Work-life balance advice</p>
                  </button>
                  <button 
                    onClick={() => setGroqInput('Suggest actions based on my current context')}
                    className="p-4 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors text-left"
                  >
                    <p className="text-sm font-medium text-orange-900">🎯 Suggest smart actions</p>
                  </button>
                </div>
              </div>
            ) : (
              <>
                {chatHistory.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                        message.role === 'user'
                          ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {message.role === 'assistant' && (
                          <Bot className="w-5 h-5 text-purple-600 flex-shrink-0 mt-1" />
                        )}
                        <div className="flex-1">
                          <p className="whitespace-pre-wrap text-sm leading-relaxed">
                            {message.content}
                          </p>
                          <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-indigo-200' : 'text-gray-500'}`}>
                            {new Date(message.timestamp).toLocaleTimeString()}
                            {message.model && ` • ${message.model}`}
                            {message.tokens && ` • ${message.tokens} tokens`}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {groqLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 rounded-2xl px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Bot className="w-5 h-5 text-purple-600" />
                        <Loader className="w-4 h-4 animate-spin text-purple-600" />
                        <span className="text-sm text-gray-600">Martin is thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </>
            )}
          </div>

          {/* Chat Input */}
          <div className="border-t p-4">
            <div className="flex gap-3">
              <input
                type="text"
                value={groqInput}
                onChange={(e) => setGroqInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleGroqChat()}
                placeholder="Ask Martin anything... (e.g., productivity tips, task advice)"
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 transition-all"
                disabled={groqLoading}
              />
              <button
                onClick={isRecording ? stopRecording : startRecording}
                className={`px-4 py-3 rounded-lg transition-colors flex items-center gap-2 ${
                  isRecording ? 'bg-red-600 hover:bg-red-700 animate-pulse' : 'bg-gray-600 hover:bg-gray-700'
                } text-white`}
                title={isRecording ? 'Stop Recording' : 'Start Voice Input'}
              >
                {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>
              <button
                onClick={handleGroqChat}
                disabled={groqLoading || !groqInput.trim()}
                className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-3 rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {groqLoading ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Thinking...
                  </>
                ) : (
                  <>
                    <Send className="w-5 h-5" />
                    Send
                  </>
                )}
              </button>
            </div>
            {isRecording && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse" />
                <p className="text-sm text-red-700 font-medium">Listening... Speak now</p>
              </div>
            )}
          </div>
        </div>

        {/* Info Panel */}
        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl p-6">
          <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-600" />
            About Martin AI
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-white rounded-lg p-4">
              <p className="font-semibold text-purple-900 mb-1">🧠 Context-Aware</p>
              <p className="text-gray-600">Martin knows your tasks, schedule, and current context</p>
            </div>
            <div className="bg-white rounded-lg p-4">
              <p className="font-semibold text-indigo-900 mb-1">⚡ Powered by Groq</p>
              <p className="text-gray-600">Fast responses using Llama 3.3 70B model</p>
            </div>
            <div className="bg-white rounded-lg p-4">
              <p className="font-semibold text-blue-900 mb-1">💬 Conversational</p>
              <p className="text-gray-600">Natural conversations with memory and context</p>
            </div>
          </div>
          {chatHistory.length > 0 && (
            <div className="mt-4 p-3 bg-white rounded-lg">
              <p className="text-sm text-gray-700">
                <strong>Conversation stats:</strong> {chatHistory.length} messages • 
                {chatHistory.filter(m => m.role === 'assistant').length} AI responses
              </p>
            </div>
          )}
        </div>
      </div>
    );
  };

  const DashboardView = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Welcome back, {userName}! 👋</h1>
            <p className="text-indigo-100">Your AI-powered productivity assistant</p>
          </div>
          {weather && (
            <div className="text-right">
              <div className="flex items-center justify-end gap-2 mb-1">
                <Cloud className="w-6 h-6" />
                <span className="text-2xl font-bold">{weather.temp}°C</span>
              </div>
              <p className="text-indigo-100">{weather.condition}</p>
            </div>
          )}
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {avatars.map((avatar) => (
          <div key={avatar.avatar} className={`bg-gradient-to-br ${getAvatarColor(avatar.avatar)} rounded-xl p-5 text-white shadow-lg hover:shadow-xl transition-all cursor-pointer transform hover:scale-105`}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-lg">{avatar.avatar}</h3>
              <Trophy className="w-5 h-5" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Level {avatar.level}</span>
                <span>{avatar.xp_in_level} / {avatar.xp_in_level + avatar.xp_to_next_level} XP</span>
              </div>
              <div className="bg-white/20 rounded-full h-2 overflow-hidden">
                <div className="bg-white h-full rounded-full transition-all duration-500" style={{ width: `${avatar.progress_percent}%` }} />
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold flex items-center gap-2"><CheckSquare className="w-5 h-5 text-blue-600" />Recent Tasks</h2>
            <button onClick={() => setActiveTab('tasks')} className="text-sm text-blue-600 hover:text-blue-800 transition-colors">View All</button>
          </div>
          <div className="space-y-3">
            {tasks.slice(0, 5).map((task) => (
              <div key={task.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                <div className={`w-2 h-2 rounded-full ${getPriorityColor(task.priority)}`} />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{task.title}</p>
                  <p className="text-xs text-gray-500">{task.avatar} • {task.status}</p>
                </div>
              </div>
            ))}
            {tasks.length === 0 && <p className="text-center text-gray-500 py-8">No tasks yet</p>}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold flex items-center gap-2"><Calendar className="w-5 h-5 text-purple-600" />Today's Schedule</h2>
            <button onClick={() => setActiveTab('calendar')} className="text-sm text-purple-600 hover:text-purple-800 transition-colors">View</button>
          </div>
          <div className="space-y-3">
            {events.slice(0, 5).map((event) => (
              <div key={event.id} className="p-3 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors cursor-pointer">
                <p className="font-medium text-sm">{event.title}</p>
                <p className="text-xs text-gray-600 mt-1">{new Date(event.start).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}</p>
              </div>
            ))}
            {events.length === 0 && <p className="text-center text-gray-500 py-8">No events today</p>}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold flex items-center gap-2"><Mail className="w-5 h-5 text-green-600" />Recent Emails</h2>
            <button onClick={() => setActiveTab('email')} className="text-sm text-green-600 hover:text-green-800 transition-colors">View All</button>
          </div>
          <div className="space-y-3">
            {emails.slice(0, 5).map((email) => (
              <div key={email.id} className="p-3 bg-green-50 rounded-lg hover:bg-green-100 transition-colors cursor-pointer">
                <p className="font-medium text-sm truncate">{email.subject}</p>
                <p className="text-xs text-gray-600 mt-1 truncate">{email.from}</p>
              </div>
            ))}
            {emails.length === 0 && <p className="text-center text-gray-500 py-8">No emails</p>}
          </div>
        </div>
      </div>
      {context && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6">
          <h3 className="font-bold text-lg mb-4 flex items-center gap-2"><TrendingUp className="w-5 h-5 text-indigo-600" />System Context</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600">Energy Level</p>
              <p className="text-2xl font-bold text-blue-600">{context.energy_level}%</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Task Backlog</p>
              <p className="text-2xl font-bold text-orange-600">{context.task_backlog}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Weather</p>
              <p className="text-lg font-medium">{context.weather}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <p className="text-sm font-medium text-green-600">All Systems Active</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const TasksView = () => {
    const startIndex = (taskPage - 1) * itemsPerPage;
    const paginatedTasks = tasks.slice(startIndex, startIndex + itemsPerPage);
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold">All Tasks</h2>
          <button onClick={() => setQuery('Create a new high-priority task')} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2 transition-colors">
            <CheckSquare className="w-4 h-4" />New Task
          </button>
        </div>
        <div className="grid gap-4">
          {paginatedTasks.map((task) => (
            <div key={task.id} className="bg-white rounded-xl shadow p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium text-white ${getPriorityColor(task.priority)}`}>{task.priority}</span>
                    <span className={`text-sm px-2 py-1 rounded ${task.avatar === 'Producer' ? 'bg-red-100 text-red-700' : task.avatar === 'Administrator' ? 'bg-teal-100 text-teal-700' : task.avatar === 'Entrepreneur' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>
                      {task.avatar}
                    </span>
                    <span className={`text-sm flex items-center gap-1 ${task.status === 'Done' ? 'text-green-600' : 'text-orange-600'}`}>
                      {task.status === 'Done' && <Check className="w-3 h-3" />}
                      {task.status}
                    </span>
                  </div>
                  <h3 className="font-bold text-lg mb-2">{task.title}</h3>
                  {task.due_date && <p className="text-sm text-gray-500">Due: {new Date(task.due_date).toLocaleDateString()}</p>}
                </div>
              </div>
            </div>
          ))}
          {tasks.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <CheckSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No tasks yet</p>
            </div>
          )}
        </div>
        <Pagination currentPage={taskPage} totalItems={tasks.length} itemsPerPage={itemsPerPage} onPageChange={setTaskPage} />
      </div>
    );
  };

  const CalendarView = () => {
    const startIndex = (eventPage - 1) * itemsPerPage;
    const paginatedEvents = events.slice(startIndex, startIndex + itemsPerPage);
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold">Calendar Events</h2>
          <button onClick={() => setQuery('Schedule meeting tomorrow at 2pm')} className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 flex items-center gap-2 transition-colors">
            <Calendar className="w-4 h-4" />New Event
          </button>
        </div>
        <div className="grid gap-4">
          {paginatedEvents.map((event) => (
            <div key={event.id} className="bg-white rounded-xl shadow p-6 hover:shadow-lg transition-shadow">
              <h3 className="font-bold text-lg mb-2">{event.title}</h3>
              <div className="space-y-1 text-sm text-gray-600">
                <p><strong>Start:</strong> {new Date(event.start).toLocaleString()}</p>
                <p><strong>End:</strong> {new Date(event.end).toLocaleString()}</p>
                {event.location && <p><strong>Location:</strong> {event.location}</p>}
                {event.description && <p><strong>Description:</strong> {event.description}</p>}
              </div>
              {event.link && (
                <a href={event.link} target="_blank" rel="noopener noreferrer" className="text-purple-600 text-sm mt-2 inline-flex items-center gap-1 hover:text-purple-800 transition-colors">
                  View in Calendar <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          ))}
          {events.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No events scheduled</p>
            </div>
          )}
        </div>
        <Pagination currentPage={eventPage} totalItems={events.length} itemsPerPage={itemsPerPage} onPageChange={setEventPage} />
      </div>
    );
  };

  const EmailView = () => {
    const startIndex = (emailPage - 1) * itemsPerPage;
    const paginatedEmails = emails.slice(startIndex, startIndex + itemsPerPage);
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold">Email Inbox</h2>
          <button onClick={() => setQuery('Send an email to team about project update')} className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2 transition-colors">
            <Send className="w-4 h-4" />Compose
          </button>
        </div>
        <div className="grid gap-4">
          {paginatedEmails.map((email) => (
            <div key={email.id} className="bg-white rounded-xl shadow p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <Inbox className="w-4 h-4 text-green-600 flex-shrink-0" />
                    <span className="text-sm text-gray-600 truncate">{email.from}</span>
                    <span className="text-xs text-gray-400">{email.date}</span>
                  </div>
                  <h3 className="font-bold text-lg mb-2">{email.subject}</h3>
                  <p className="text-sm text-gray-600">{email.snippet}</p>
                </div>
              </div>
            </div>
          ))}
          {emails.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <Mail className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No emails found</p>
            </div>
          )}
        </div>
        <Pagination currentPage={emailPage} totalItems={emails.length} itemsPerPage={itemsPerPage} onPageChange={setEmailPage} />
      </div>
    );
  };

  const WeatherView = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Weather Information</h2>
      {weather ? (
        <div className="bg-gradient-to-br from-blue-400 to-cyan-500 rounded-xl p-8 text-white">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-4xl font-bold mb-2">{weather.temp}°C</h3>
              <p className="text-xl">{weather.condition}</p>
              <p className="text-blue-100 mt-2">{weather.location}</p>
            </div>
            <Cloud className="w-24 h-24 opacity-80" />
          </div>
          {weather.feels_like && weather.humidity && weather.wind_kph && (
            <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-white/20">
              <div>
                <p className="text-sm text-blue-100">Feels Like</p>
                <p className="text-2xl font-bold">{weather.feels_like}°C</p>
              </div>
              <div>
                <p className="text-sm text-blue-100">Humidity</p>
                <p className="text-2xl font-bold">{weather.humidity}%</p>
              </div>
              <div>
                <p className="text-sm text-blue-100">Wind</p>
                <p className="text-2xl font-bold">{weather.wind_kph} km/h</p>
              </div>
            </div>
          )}
        </div>
      ) : (
        <p className="text-center text-gray-500 py-8">Loading weather data...</p>
      )}
    </div>
  );

  if (!isAuthenticated) return <AuthScreen />;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button onClick={() => setSidebarOpen(!sidebarOpen)} className="lg:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors">
                {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">Present OS</h1>
              <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded">9 Agents Active</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="relative">
                <button onClick={() => { setShowNotifications(!showNotifications); setShowProfile(false); }} className="relative p-2 hover:bg-gray-100 rounded-lg transition-colors">
                  <Bell className="w-6 h-6 text-gray-600" />
                  {notifications.filter(n => !n.read).length > 0 && (
                    <div className="absolute top-0 right-0 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
                      {notifications.filter(n => !n.read).length}
                    </div>
                  )}
                </button>
                {showNotifications && <NotificationPanel />}
              </div>
              <div className="relative">
                <button onClick={() => { setShowProfile(!showProfile); setShowNotifications(false); }} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                  <User className="w-6 h-6 text-gray-600" />
                </button>
                {showProfile && <ProfilePanel />}
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-6">
          {sidebarOpen && (
            <aside className="w-64 bg-white rounded-xl shadow-lg p-4 h-fit sticky top-24">
              <nav className="space-y-2">
                {[
                  { id: 'dashboard', label: 'Dashboard', icon: TrendingUp },
                  { id: 'tasks', label: 'Tasks', icon: CheckSquare },
                  { id: 'calendar', label: 'Calendar', icon: Calendar },
                  { id: 'email', label: 'Email', icon: Mail },
                  { id: 'groq', label: 'AI Chat', icon: MessageSquare },
                  { id: 'weather', label: 'Weather', icon: Cloud },
                  { id: 'contact', label: 'Contacts', icon: Users },
                ].map((item) => (
                  <button key={item.id} onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === item.id ? 'bg-indigo-600 text-white shadow-md' : 'hover:bg-gray-100 text-gray-700'}`}>
                    <item.icon className="w-5 h-5" />
                    {item.label}
                  </button>
                ))}
              </nav>
              <div className="mt-6 pt-6 border-t">
                <h3 className="text-xs font-bold text-gray-500 uppercase mb-2">All 9 Agents</h3>
                <div className="space-y-1 text-xs text-gray-600">
                  <p className="flex items-center gap-2"><Check className="w-3 h-3 text-green-600" /> Task Agent</p>
                  <p className="flex items-center gap-2"><Check className="w-3 h-3 text-green-600" /> Calendar Agent</p>
                  <p className="flex items-center gap-2"><Check className="w-3 h-3 text-green-600" /> Email Agent</p>
                  <p className="flex items-center gap-2"><Check className="w-3 h-3 text-green-600" /> Weather Agent</p>
                  <p className="flex items-center gap-2"><Check className="w-3 h-3 text-green-600" /> XP Agent</p>
                  <p className="flex items-center gap-2"><Check className="w-3 h-3 text-green-600" /> Groq AI Agent</p>
                  <p className="flex items-center gap-2"><Check className="w-3 h-3 text-green-600" /> Report Agent</p>
                  <p className="flex items-center gap-2"><Check className="w-3 h-3 text-green-600" /> Contact Agent</p>
                  <p className="flex items-center gap-2"><Check className="w-3 h-3 text-green-600" /> Focus Agent</p>
                </div>
              </div>
            </aside>
          )}

          <main className="flex-1">
            {activeTab === 'dashboard' && <DashboardView />}
            {activeTab === 'tasks' && <TasksView />}
            {activeTab === 'calendar' && <CalendarView />}
            {activeTab === 'email' && <EmailView />}
            {activeTab === 'groq' && <GroqChatView />}
            {activeTab === 'weather' && <WeatherView />}
            {activeTab === 'contact' && <ContactView />}
          </main>
        </div>

        <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <Sparkles className="w-6 h-6 text-indigo-600" />
            <h2 className="text-xl font-bold">AI Command Center</h2>
          </div>
          
          {response && (
            <div className="mb-6 p-4 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg">
              <div className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <p className="font-medium text-green-900 mb-2">{fixEncoding(response.response)}</p>
                  {response.agents && response.agents.length > 0 && (
                    <div className="flex gap-2 flex-wrap">
                      {response.agents.map((agent, idx) => (
                        <span key={idx} className="px-2 py-1 bg-green-600 text-white text-xs rounded-full">
                          ✓ {agent}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
              placeholder="Try: 'Create a task', 'What's my schedule?', 'Add contact John', 'Send email to team'..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600 transition-all"
              disabled={loading}
            />
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`px-4 py-3 rounded-lg transition-colors flex items-center gap-2 ${
                isRecording ? 'bg-red-600 hover:bg-red-700 animate-pulse' : 'bg-gray-600 hover:bg-gray-700'
              } text-white`}
              title={isRecording ? 'Stop Recording' : 'Start Voice Input'}
            >
              {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading || !query.trim()}
              className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-lg hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  Execute
                </>
              )}
            </button>
          </div>

          {isRecording && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
              <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse" />
              <p className="text-sm text-red-700 font-medium">Listening... Speak your command now</p>
            </div>
          )}

          <div className="mt-4 flex flex-wrap gap-2">
            <button onClick={() => setQuery('Create a high-priority task for today')} className="px-3 py-2 bg-blue-50 text-blue-700 text-sm rounded-lg hover:bg-blue-100 transition-colors">
              + Quick Task
            </button>
            <button onClick={() => setQuery('Schedule meeting tomorrow at 10am')} className="px-3 py-2 bg-purple-50 text-purple-700 text-sm rounded-lg hover:bg-purple-100 transition-colors">
              + Schedule Event
            </button>
            <button onClick={() => setQuery('Add contact Sarah email sarah@example.com')} className="px-3 py-2 bg-pink-50 text-pink-700 text-sm rounded-lg hover:bg-pink-100 transition-colors">
              + Add Contact
            </button>
            <button onClick={() => setQuery('Send email to team about project status')} className="px-3 py-2 bg-green-50 text-green-700 text-sm rounded-lg hover:bg-green-100 transition-colors">
              + Send Email
            </button>
            <button onClick={() => setActiveTab('groq')} className="px-3 py-2 bg-indigo-50 text-indigo-700 text-sm rounded-lg hover:bg-indigo-100 transition-colors">
              💬 Chat with AI
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;