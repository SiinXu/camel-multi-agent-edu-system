import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

// SVG 头像组件
const Avatar = ({ role, size = 40 }) => {
  const colors = {
    teacher: '#4CAF50',
    student: '#2196F3',
    knowledge: '#FF9800',
    faq: '#9C27B0',
    quiz: '#F44336'
  };

  const getInitials = (role) => {
    const map = {
      teacher_agent: 'T',
      student: 'S',
      knowledge_crawler: 'K',
      faq_generator: 'F',
      quiz_generator: 'Q'
    };
    return map[role] || '?';
  };

  const bgColor = colors[role.split('_')[0]] || '#757575';

  return (
    <svg width={size} height={size} viewBox="0 0 40 40">
      <circle cx="20" cy="20" r="20" fill={bgColor} />
      <text
        x="20"
        y="20"
        dominantBaseline="middle"
        textAnchor="middle"
        fill="white"
        fontSize="16"
        fontWeight="bold"
      >
        {getInitials(role)}
      </text>
    </svg>
  );
};

// Agent 头像和角色配置
const AGENTS = {
  teacher_agent: {
    name: "教师助手",
    avatar: "/avatars/teacher.png",
    role: "assistant"
  },
  student_agent: {
    name: "学生助手",
    avatar: "/avatars/student.png",
    role: "user"
  },
  knowledge_crawler: {
    name: "知识爬虫",
    avatar: "/avatars/crawler.png",
    role: "assistant"
  },
  faq_generator: {
    name: "FAQ生成器",
    avatar: "/avatars/faq.png",
    role: "assistant"
  },
  quiz_generator: {
    name: "测验生成器",
    avatar: "/avatars/quiz.png",
    role: "assistant"
  }
};

// API 配置
const API_BASE_URL = 'http://localhost:8002';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [currentAgent, setCurrentAgent] = useState('teacher_agent');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // 获取历史消息
  useEffect(() => {
    fetchHistory();
  }, []);

  // 滚动到最新消息
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 获取历史消息
  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/history/student_1`);
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  // 发送消息
  const handleSendMessage = async () => {
    if (!input.trim()) return;

    try {
      setIsLoading(true);
      const newMessage = {
        content: input,
        sender: 'student_1',
        role: 'user',
        timestamp: new Date().toISOString()
      };

      // 添加用户消息到界面
      setMessages(prev => [...prev, newMessage]);
      setInput('');

      // 发送消息到后端
      const response = await axios.post(`${API_BASE_URL}/api/ask`, {
        student_id: 'student_1',
        question: input,
        agent_name: currentAgent
      });

      if (response.data && response.data.answer) {
        // 添加 Agent 回复到界面
        const agentMessage = {
          content: response.data.answer,
          sender: currentAgent,
          role: AGENTS[currentAgent].role,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, agentMessage]);
      } else {
        console.error('Invalid response format:', response.data);
        alert('接收消息失败，请重试');
      }

    } catch (error) {
      console.error('Error sending message:', error);
      alert('发送消息失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  // 处理按键事件
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="App">
      <div className="chat-container">
        <div className="agent-selector">
          {Object.entries(AGENTS).map(([agentId, agent]) => (
            <div
              key={agentId}
              className={`agent-option ${currentAgent === agentId ? 'active' : ''}`}
              onClick={() => setCurrentAgent(agentId)}
            >
              <Avatar role={agentId} size={24} />
              <span>{agent.name}</span>
            </div>
          ))}
        </div>

        <div className="messages-container">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message ${msg.role === 'user' ? 'user-message' : 'agent-message'}`}
            >
              <Avatar role={msg.role === 'user' ? 'student' : msg.sender} />
              <div className="message-content">
                <div className="message-sender">
                  {msg.role === 'user' ? '我' : AGENTS[msg.sender]?.name}
                </div>
                <div className="message-text">{msg.content}</div>
                <div className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入消息..."
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !input.trim()}
          >
            {isLoading ? '发送中...' : '发送'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;