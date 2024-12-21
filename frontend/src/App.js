import React, { useState, useEffect, Fragment, useCallback, useRef } from 'react';
import axios from 'axios';
import { Dialog, Transition, Menu, Listbox } from '@headlessui/react';
import { ChevronDownIcon, CheckIcon, SunIcon, MoonIcon } from '@heroicons/react/20/solid';
import Particles from "react-tsparticles";
import { loadFull } from "tsparticles";
import particlesConfig from "./particlesConfig.json";
import SettingsPage from './components/SettingsPage';

const API_BASE_URL = 'http://localhost:8000/api';

function App() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [audioData, setAudioData] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState('teacher_agent');
  const [currentTopic, setCurrentTopic] = useState('');
  const [message, setMessage] = useState('');
  const [action, setAction] = useState('ask_question');
  const [isOpen, setIsOpen] = useState(false);
  const [pdfFile, setPdfFile] = useState(null);
  const [imageUrl, setImageUrl] = useState('');
  const [multimodalQuestion, setMultimodalQuestion] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [apiKeys, setApiKeys] = useState({
    modelscope: '',
    fish_audio: '',
    chunkr: '',
    firecrawl: ''
  });
  const [interruptAgent, setInterruptAgent] = useState("");
  const [messages, setMessages] = useState([]); // 新增：消息列表
  const [agentStatus, setAgentStatus] = useState({});
  const [socket, setSocket] = useState(null);
  const messagesEndRef = useRef(null);

  // 从 localStorage 加载 API 密钥
  const [modelscopeApiKey, setModelscopeApiKey] = useState(localStorage.getItem('modelscopeApiKey') || '');
  const [fishAudioApiKey, setFishAudioApiKey] = useState(localStorage.getItem('fishAudioApiKey') || '');
  const [fishAudioApi, setFishAudioApi] = useState(localStorage.getItem('fishAudioApi') || '');
  const [chunkrApiKey, setChunkrApiKey] = useState(localStorage.getItem('chunkrApiKey') || '');
  const [firecrawlApiKey, setFirecrawlApiKey] = useState(localStorage.getItem('firecrawlApiKey') || '');

  const agents = [
    { name: 'Teacher Agent', value: 'teacher_agent' },
    { name: 'Student Agent 1 (Alice)', value: 'student_agent_1' },
    { name: 'Student Agent 2 (Bob)', value: 'student_agent_2' },
    { name: 'Multimodal Agent', value: 'multimodal_agent' },
  ];

  const topics = [
    { name: 'Select a topic', value: '' },
    { name: 'Photosynthesis', value: 'photosynthesis' },
    { name: 'Math Functions', value: 'math_functions' },
    { name: 'World History', value: 'world_history' },
  ];

  // 保存 API 密钥到 localStorage
  const saveApiKeys = () => {
    localStorage.setItem('modelscopeApiKey', modelscopeApiKey);
    localStorage.setItem('fishAudioApiKey', fishAudioApiKey);
    localStorage.setItem('fishAudioApi', fishAudioApi);
    localStorage.setItem('chunkrApiKey', chunkrApiKey);
    localStorage.setItem('firecrawlApiKey', firecrawlApiKey);
    alert('API keys saved!');
  };

  const handleAskQuestion = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/ask`, {
        student_id: 'student_1',
        question: question,
        agent_name: selectedAgent,
        topic: currentTopic,
      }, {
        headers: {
          'ModelScope-Api-Key': modelscopeApiKey,
        }
      });
      setAnswer(response.data.answer);
    } catch (error) {
      console.error('Error asking question:', error);
      setAnswer('Error asking question.');
    }
  };

  const handleTextToSpeech = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/text_to_speech`, {
        text: answer,
      }, {
        responseType: 'blob',
        headers: {
          'Fish-Audio-Api-Key': fishAudioApiKey,
          'Fish-Audio-Api': fishAudioApi,
        }
      });

      const reader = new FileReader();
      reader.readAsDataURL(response.data);
      reader.onloadend = () => {
        const base64Audio = reader.result;
        setAudioData(base64Audio);
      };
    } catch (error) {
      console.error('Error converting text to speech:', error);
    }
  };

  const playAudio = () => {
    if (audioData) {
      const audio = new Audio(audioData);
      audio.play();
    }
  };

  const handleTopicChange = (value) => {
    setCurrentTopic(value);
  };

  const handleStudentInteract = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/interact`, {
        sender_id: 'student_agent_1',
        receiver_id: 'student_agent_2',
        action: action,
        content: message,
      }, {
        headers: {
          'ModelScope-Api-Key': modelscopeApiKey,
        }
      });
      setAnswer(response.data.message);
    } catch (error) {
      console.error('Error during student interaction:', error);
      setAnswer('Error during student interaction.');
    }
  };

  const handlePdfUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload_pdf`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Chunkr-Api-Key': chunkrApiKey,
        },
      });
      console.log(response.data);
      alert(`PDF Upload Success: ${response.data.message}`);
    } catch (error) {
      console.error('Error uploading PDF:', error);
      alert('Error uploading PDF.');
    }
  };

  const handleImageUrlChange = (event) => {
    setImageUrl(event.target.value);
  };

  const handleMultimodalAsk = async () => {
    if (!imageUrl) {
      alert('Please enter an image URL.');
      return;
    }
  
    try {
      const response = await fetch(imageUrl);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const blob = await response.blob();
  
      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onloadend = async () => {
        const base64Image = reader.result.split(',')[1];
  
        try {
          const multimodalResponse = await axios.post(`${API_BASE_URL}/multimodal`, {
            question: multimodalQuestion,
            image: base64Image,
          }, {
            headers: {
              'ModelScope-Api-Key': modelscopeApiKey,
              'Firecrawl-Api-Key': firecrawlApiKey,
            }
          });
          setAnswer(multimodalResponse.data.answer);
        } catch (multimodalError) {
          console.error('Error sending multimodal question:', multimodalError);
          setAnswer('Error sending multimodal question.');
        }
      };
    } catch (error) {
      console.error('Error fetching image:', error);
      setAnswer('Error fetching image.');
    }
  };

  const handleInterrupt = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/interrupt`, null, {
        params: {
          agent_name: interruptAgent,
        },
      });
      setAnswer(response.data.message);
      setInterruptAgent("");
    } catch (error) {
      console.error('Error interrupting agent:', error);
      setAnswer('Error interrupting agent.');
    }
  };

  // 获取消息的函数
  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/messages`);
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  // 每隔一段时间获取一次消息
  useEffect(() => {
    const intervalId = setInterval(() => {
      fetchMessages();
    }, 1000); // 每秒获取一次消息

    return () => clearInterval(intervalId); // 组件卸载时清除定时器
  }, []);

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  useEffect(() => {
    // 根据 isDarkMode 更新 body 的 class
    document.documentElement.classList.toggle('dark', isDarkMode);
  }, [isDarkMode]);

  const particlesInit = useCallback(main => {
    loadFull(main);
  }, []);

  // WebSocket 连接
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setSocket(ws);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'message') {
        setMessages(prev => [...prev, data.data]);
      } else if (data.type === 'agent_status') {
        setAgentStatus(data.data);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setSocket(null);
    };

    return () => {
      if (ws) ws.close();
    };
  }, []);

  // 获取状态显示的样式
  const getStatusStyle = (status) => {
    switch (status) {
      case 'thinking':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'using_tool':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'crawling':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'generating_faq':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'generating_quiz':
        return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200';
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  return (
    <div className={`min-h-screen ${isDarkMode ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-900'} py-6 flex flex-col justify-center sm:py-12 relative`}>
      <Particles init={particlesInit} options={particlesConfig} className="absolute top-0 left-0 w-full h-full" />
      <div className="relative z-10">
        <div className="absolute top-4 right-4">
          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            className="bg-gray-200 dark:bg-gray-700 rounded-full p-2 focus:outline-none"
          >
            {isDarkMode ? (
              <SunIcon className="h-6 w-6 text-yellow-500" />
            ) : (
              <MoonIcon className="h-6 w-6 text-gray-800 dark:text-gray-200" />
            )}
          </button>
        </div>
        <div className='absolute top-4 left-4'>
          <button onClick={() => setShowSettings(true)} className="bg-gray-200 dark:bg-gray-700 rounded-full p-2 focus:outline-none">
              ⚙️
          </button>
        </div>
        <h1 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-8">
          Intelligent Education System
        </h1>
        
        {/* 设置页面 */}
        <SettingsPage 
          isOpen={showSettings}
          setIsOpen={setShowSettings}
          apiKeys={apiKeys}
          setApiKeys={setApiKeys}
          onSave={saveApiKeys}
        />

        {/* 中断 Agent 功能 */}
        <div className="mb-6">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Interrupt Agent</h2>
          <div className="mb-4">
            <label htmlFor="interruptAgent" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Agent to Interrupt:
            </label>
            <select
              id="interruptAgent"
              value={interruptAgent}
              onChange={(e) => setInterruptAgent(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-700 dark:bg-gray-800 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              <option value="">Select an Agent</option>
              {agents.map((agent) => (
                <option key={agent.value} value={agent.value}>
                  {agent.name}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleInterrupt}
            className="mt-2 w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            disabled={!interruptAgent}
          >
            Interrupt
          </button>
        </div>

        {/* Agent 状态显示 */}
        <div className="mb-6">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Agent Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(agentStatus).map(([agentName, status]) => (
              <div 
                key={agentName}
                className={`p-4 rounded-lg ${getStatusStyle(status.status)}`}
              >
                <div className="font-medium">{agentName}</div>
                <div className="text-sm mt-1">
                  Status: {status.status}
                  {status.message && (
                    <div className="mt-1 text-sm opacity-75">{status.message}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 消息列表 */}
        <div className="mb-6">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Messages</h2>
          <div className="border border-gray-300 dark:border-gray-700 rounded-md p-3 h-64 overflow-y-auto bg-white dark:bg-gray-800 shadow-sm">
            {messages.map((msg, index) => (
              <div 
                key={index} 
                className={`mb-3 ${
                  msg.sender === selectedAgent 
                    ? 'ml-auto' 
                    : 'mr-auto'
                }`}
              >
                <div className={`max-w-[80%] ${
                  msg.sender === selectedAgent 
                    ? 'ml-auto' 
                    : 'mr-auto'
                }`}>
                  <div className={`text-sm font-medium mb-1 ${
                    msg.sender === selectedAgent 
                      ? 'text-right text-blue-600 dark:text-blue-400' 
                      : 'text-left text-gray-600 dark:text-gray-400'
                  }`}>
                    {msg.sender}
                  </div>
                  <div className={`p-3 rounded-lg break-words ${
                    msg.sender === selectedAgent 
                      ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100' 
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
                  }`}>
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    <div className="text-xs mt-1 text-gray-500 dark:text-gray-400">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="mb-6">
          <Listbox value={selectedAgent} onChange={setSelectedAgent}>
              <Listbox.Label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Choose an Agent:</Listbox.Label>
              <div className="relative mt-1">
              <Listbox.Button className="relative w-full cursor-default rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 py-2 pl-3 pr-10 text-left shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 sm:text-sm">
                  <span className="block truncate">
                      {agents.find(agent => agent.value === selectedAgent)?.name}
                  </span>
                  <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                  <ChevronDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                  </span>
              </Listbox.Button>

              <Transition
                  as={Fragment}
                  leave="transition ease-in duration-100"
                  leaveFrom="opacity-100"
                  leaveTo="opacity-0"
              >
                  <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white dark:bg-gray-800 py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                  {agents.map((agent) => (
                      <Listbox.Option
                      key={agent.value}
                      value={agent.value}
                      className={({ active }) =>
                          `relative cursor-default select-none py-2 pl-3 pr-9 ${
                          active ? 'bg-blue-100 dark:bg-blue-700 text-blue-900 dark:text-white' : 'text-gray-900 dark:text-gray-300'
                          }`
                      }
                      >
                      {({ selected }) => (
                          <>
                          <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>
                              {agent.name}
                          </span>
                          {selected && (
                              <span className="absolute inset-y-0 right-0 flex items-center pr-4 text-blue-600 dark:text-blue-400">
                              <CheckIcon className="h-5 w-5" aria-hidden="true" />
                              </span>
                          )}
                          </>
                      )}
                      </Listbox.Option>
                  ))}
                  </Listbox.Options>
              </Transition>
              </div>
          </Listbox>
          </div>

          <div className="mb-6">
              <Listbox value={currentTopic} onChange={setCurrentTopic}>
                  <Listbox.Label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Current Topic:</Listbox.Label>
                  <div className="relative mt-1">
                  <Listbox.Button className="relative w-full cursor-default rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 py-2 pl-3 pr-10 text-left shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 sm:text-sm">
                      <span className="block truncate">
                          {topics.find(topic => topic.value === currentTopic)?.name || 'Select a topic'}
                      </span>
                      <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                      <ChevronDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                      </span>
                  </Listbox.Button>

                  <Transition
                      as={Fragment}
                      leave="transition ease-in duration-100"
                      leaveFrom="opacity-100"
                      leaveTo="opacity-0"
                  >
                      <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white dark:bg-gray-800 py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                      {topics.map((topic) => (
                          <Listbox.Option
                          key={topic.value}
                          value={topic.value}
                          className={({ active }) =>
                              `relative cursor-default select-none py-2 pl-3 pr-9 ${
                              active ? 'bg-blue-100 dark:bg-blue-700 text-blue-900 dark:text-white' : 'text-gray-900 dark:text-gray-300'
                              }`
                          }
                          >
                          {({ selected }) => (
                              <>
                              <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>
                                  {topic.name}
                              </span>
                              {selected && (
                                  <span className="absolute inset-y-0 right-0 flex items-center pr-4 text-blue-600 dark:text-blue-400">
                                      <CheckIcon className="h-5 w-5" aria-hidden="true" />
                                  </span>
                              )}
                              </>
                          )}
                          </Listbox.Option>
                      ))}
                      </Listbox.Options>
                  </Transition>
                  </div>
              </Listbox>
          </div>

        <div className="mb-4">
          <label htmlFor="question" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Question:
          </label>
          <textarea
            id="question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter your question here..."
            rows="3"
            className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-700 dark:bg-gray-800 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
          <button
            onClick={handleAskQuestion}
            className="mt-2 w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Ask
          </button>
        </div>

        <div className="mb-6">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Answer:</p>
          <div className="mt-1 p-3 rounded-md bg-gray-50 dark:bg-gray-700">
            <p className="text-gray-900 dark:text-gray-100">{answer}</p>
          </div>
          {answer && (
            <button
              onClick={handleTextToSpeech}
              className="mt-2 w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Convert to Speech
            </button>
          )}
          {audioData && (
            <div className="mt-4">
              <audio controls src={audioData} />
            </div>
          )}
        </div>
        <div>
          <input type="file" onChange={handlePdfUpload} accept="application/pdf" className="mt-2" />
       </div>
       <div>
          <label htmlFor="imageUrl" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Image URL:</label>
          <input
            type="text"
            id="imageUrl"
            value={imageUrl}
            onChange={handleImageUrlChange}
            placeholder="Enter image URL here..."
            className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-700 dark:bg-gray-800 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
        </div>
        <div>
        <label htmlFor="multimodalQuestion" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Question:</label>
          <textarea
            id="multimodalQuestion"
            value={multimodalQuestion}
            onChange={(e) => setMultimodalQuestion(e.target.value)}
            placeholder="Enter your question about the image here..."
            rows="3"
            className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-700 dark:bg-gray-800 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
          <button
            onClick={handleMultimodalAsk}
            className="mt-2 w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Ask about Image
          </button>
        </div>
        <div className="mb-6">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Student Interaction</h2>
          <div className="mb-4">
            <label htmlFor="action" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Action:
            </label>
            <select
              id="action"
              value={action}
              onChange={(e) => setAction(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-700 dark:bg-gray-800 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              <option value="ask_question">Ask Question</option>
              <option value="send_message">Send Message</option>
              <option value="test">Test</option>
              <option value="check_records">Check Records</option>
            </select>
          </div>
          <div className="mb-4">
            <label htmlFor="message" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Message/Content:
            </label>
            <textarea
              id="message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Enter message or content here..."
              rows="3"
              className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-700 dark:bg-gray-800 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
            <button
              onClick={handleStudentInteract}
              className="mt-2 w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Interact
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;  