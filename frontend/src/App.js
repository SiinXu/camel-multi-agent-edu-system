import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import axios from 'axios';
import ChatLayout from './components/ChatLayout';
import NotFound from './components/NotFound';
import { useWebSocket } from './hooks/useWebSocket';
import { SunIcon, MoonIcon } from '@heroicons/react/24/outline';
import SettingsPage from './components/SettingsPage';

function App() {
  const [messages, setMessages] = useState([]);
  const [agentStatus, setAgentStatus] = useState({});
  const [selectedAgent, setSelectedAgent] = useState('teacher_agent');
  const [currentTopic, setCurrentTopic] = useState('');
  const [message, setMessage] = useState('');
  const [action, setAction] = useState('ask_question');
  const [pdfFile, setPdfFile] = useState(null);
  const [imageUrl, setImageUrl] = useState('');
  const [multimodalQuestion, setMultimodalQuestion] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [apiKeys, setApiKeys] = useState(() => ({
    modelscope: localStorage.getItem('modelscopeApiKey') || '',
    fish_audio: localStorage.getItem('fishAudioApiKey') || '',
    chunkr: localStorage.getItem('chunkrApiKey') || '',
    model_name: 'Qwen/Qwen2.5-32B-Instruct',
  }));

  const { socket, connected } = useWebSocket('ws://localhost:8000/ws');

  useEffect(() => {
    if (socket) {
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'message') {
          setMessages(prev => [...prev, data.data]);
        } else if (data.type === 'agent_status') {
          setAgentStatus(data.data);
        }
      };
    }
  }, [socket]);

  const handleSendMessage = async (message) => {
    try {
      const response = await axios.post('http://localhost:8000/api/ask', {
        student_id: 'student_1',
        question: message,
        agent_name: selectedAgent,
        topic: currentTopic,
      });
      
      if (response.data && response.data.answer) {
        setMessages(prev => [...prev, { role: 'user', content: message }, { role: 'assistant', content: response.data.answer }]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleSendFile = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post('http://localhost:8000/api/upload_pdf', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      if (response.data && response.data.message) {
        setMessages(prev => [...prev, { role: 'system', content: response.data.message }]);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  const handleAskQuestion = async () => {
    if (!message.trim()) return;
    
    try {
      const response = await axios.post('http://localhost:8000/api/ask', {
        student_id: 'student_1',
        question: message,
        agent_name: selectedAgent,
        topic: currentTopic,
      });
      
      if (response.data && response.data.answer) {
        setMessages(prev => [...prev, { role: 'user', content: message }, { role: 'assistant', content: response.data.answer }]);
        setMessage('');
      }
    } catch (error) {
      console.error('Error asking question:', error);
    }
  };

  const handlePdfUpload = async () => {
    if (!pdfFile) return;
    
    try {
      const formData = new FormData();
      formData.append('file', pdfFile);
      
      const response = await axios.post('http://localhost:8000/api/upload_pdf', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      if (response.data && response.data.message) {
        setMessages(prev => [...prev, { role: 'system', content: response.data.message }]);
        setPdfFile(null);
      }
    } catch (error) {
      console.error('Error uploading PDF:', error);
    }
  };

  const handleMultimodalAsk = async () => {
    if (!multimodalQuestion.trim() || !imageUrl.trim()) return;
    
    try {
      const response = await axios.post('http://localhost:8000/api/multimodal', {
        question: multimodalQuestion,
        image: imageUrl,
      });
      
      if (response.data && response.data.answer) {
        setMessages(prev => [...prev, 
          { role: 'user', content: `[Image: ${imageUrl}]\n${multimodalQuestion}` },
          { role: 'assistant', content: response.data.answer }
        ]);
        setMultimodalQuestion('');
        setImageUrl('');
      }
    } catch (error) {
      console.error('Error asking multimodal question:', error);
    }
  };

  const handleStudentInteract = async (action) => {
    try {
      const response = await axios.post('http://localhost:8000/api/interact', {
        sender_id: 'student_1',
        receiver_id: selectedAgent,
        action: action,
        content: message,
      });
      
      if (response.data && response.data.message) {
        setMessages(prev => [...prev, { role: 'system', content: response.data.message }]);
      }
    } catch (error) {
      console.error('Error in student interaction:', error);
    }
  };

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

  const saveApiKeys = (newKeys) => {
    setApiKeys(newKeys);
    localStorage.setItem('modelscopeApiKey', newKeys.modelscope || '');
    localStorage.setItem('fishAudioApiKey', newKeys.fish_audio || '');
    localStorage.setItem('chunkrApiKey', newKeys.chunkr || '');
    localStorage.setItem('modelName', newKeys.model_name);
  };

  const getStatusStyle = (status) => {
    switch (status) {
      case 'online':
        return 'bg-green-500';
      case 'busy':
        return 'bg-yellow-500';
      case 'offline':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <Routes>
      <Route 
        path="/" 
        element={
          <div className={`min-h-screen ${isDarkMode ? 'dark bg-gray-900' : 'bg-gray-100'}`}>
            <div className='absolute top-4 right-4'>
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
            <h1 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-8 pt-16">
              Intelligent Education System
            </h1>

            <div className="max-w-4xl mx-auto bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
              <div className="grid grid-cols-3 gap-4 p-4 border-b border-gray-200 dark:border-gray-700">
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

              <ChatLayout
                messages={messages}
                onSendMessage={handleSendMessage}
                onSendFile={handleSendFile}
                agents={agents}
                topics={topics}
                selectedAgent={selectedAgent}
                setSelectedAgent={setSelectedAgent}
                currentTopic={currentTopic}
                setCurrentTopic={setCurrentTopic}
                message={message}
                setMessage={setMessage}
                action={action}
                setAction={setAction}
                pdfFile={pdfFile}
                setPdfFile={setPdfFile}
                imageUrl={imageUrl}
                setImageUrl={setImageUrl}
                multimodalQuestion={multimodalQuestion}
                setMultimodalQuestion={setMultimodalQuestion}
                handleAskQuestion={handleAskQuestion}
                handlePdfUpload={handlePdfUpload}
                handleImageUrlChange={(event) => setImageUrl(event.target.value)}
                handleMultimodalAsk={handleMultimodalAsk}
                handleInterrupt={() => console.log('Interrupt')}
                handleStudentInteract={handleStudentInteract}
              />
            </div>

            <SettingsPage
              show={showSettings}
              onClose={() => setShowSettings(false)}
              apiKeys={apiKeys}
              onSave={(newKeys) => {
                saveApiKeys(newKeys);
                setShowSettings(false);
              }}
            />
          </div>
        } 
      />
      <Route path="/404" element={<NotFound />} />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  );
}

export default App;