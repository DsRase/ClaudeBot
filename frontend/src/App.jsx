import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:8000/api/chat';
const MODELS_URL = 'http://localhost:8000/api/models';
const STORAGE_KEY = 'claudebot_messages';
const USER_ID_KEY = 'claudebot_user_id';
const MODEL_KEY = 'claudebot_selected_model';

function getUserId() {
  let userId = localStorage.getItem(USER_ID_KEY);
  if (!userId) {
    userId = 'user_' + Math.random().toString(36).substring(7);
    localStorage.setItem(USER_ID_KEY, userId);
  }
  return userId;
}

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('');
  const [availableModels, setAvailableModels] = useState([]);
  const [showModels, setShowModels] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const userId = getUserId();

  useEffect(() => {
    axios.get(MODELS_URL).then(res => {
      setAvailableModels(res.data.available);
      const saved = localStorage.getItem(MODEL_KEY);
      if (saved && (saved === 'adaptive' || res.data.available.includes(saved))) {
        setSelectedModel(saved);
      } else {
        setSelectedModel('adaptive');
        localStorage.setItem(MODEL_KEY, 'adaptive');
      }
    }).catch(err => {
      console.error('Ошибка загрузки моделей:', err);
    });
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed);
        }
      } catch (e) {
        // ignore
      }
    }
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } else if (messages.length === 0) {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    const textarea = inputRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 180) + 'px';
    }
  }, [input]);

  const clearHistory = () => {
    setMessages([]);
    localStorage.removeItem(STORAGE_KEY);
    inputRef.current?.focus();
  };

  const changeModel = (model) => {
    setSelectedModel(model);
    localStorage.setItem(MODEL_KEY, model);
    setShowModels(false);
  };

  const MAX_MESSAGE_LENGTH = 10000;

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    if (text.length > MAX_MESSAGE_LENGTH) {
      alert(`Максимальная длина сообщения ${MAX_MESSAGE_LENGTH} символов`);
      return;
    }

    const newMessages = [...messages, { role: 'user', content: text }];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }

    try {
      const modelToSend = selectedModel === 'adaptive' ? null : selectedModel;
      
      const response = await axios.post(API_URL, {
        message: text,
        user_id: userId,
        thread_id: userId,
        model: modelToSend
      });
      
      const finalMessages = [...newMessages, { role: 'assistant', content: response.data.response }];
      setMessages(finalMessages);
    } catch {
      const errorMessages = [...newMessages, { role: 'assistant', content: 'Ошибка соединения' }];
      setMessages(errorMessages);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getShortName = (fullName) => {
    if (fullName === 'adaptive') return 'Auto';
    return fullName.replace('claude-', '').replace('gpt-', '').replace('gemini-', '');
  };

  return (
    <div className='chat-app'>
      <header className='chat-header'>
        <div className='header-info'>
          <h1>ClaudeBot</h1>
          <div className='model-selector'>
            <button className='model-btn' onClick={() => setShowModels(!showModels)} disabled={loading}>
              {selectedModel ? getShortName(selectedModel) : 'Выбрать модель'} ▼
            </button>
            {showModels && (
              <div className='model-dropdown'>
                <div 
                  className={`model-option ${selectedModel === 'adaptive' ? 'active' : ''}`}
                  onClick={() => changeModel('adaptive')}
                >
                  <span className='model-name'>Adaptive</span>
                </div>
                {availableModels.map(model => (
                  <div 
                    key={model}
                    className={`model-option ${selectedModel === model ? 'active' : ''}`}
                    onClick={() => changeModel(model)}
                  >
                    <span className='model-name'>{model}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        <button className='clear-btn' onClick={clearHistory}>Очистить</button>
      </header>

      <main className='messages'>
        {messages.length === 0 ? (
          <div className='welcome'>
            <h2>Начни диалог</h2>
            <p>Напиши сообщение ниже</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <div className='avatar'>
                <img 
                  src={message.role === 'user' ? '/user.png' : '/bot.png'} 
                  alt={message.role === 'user' ? 'Пользователь' : 'Бот'} 
                  className='avatar-img' 
                />
              </div>
              <div className='content'>{message.content}</div>
            </div>
          ))
        )}

        {loading && (
          <div className='message assistant'>
            <div className="pulse-circle"></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      <footer className='input-area'>
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder='Напишите сообщение...'
          rows={1}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          {loading ? '...' : 'Отправить'}
        </button>
      </footer>
    </div>
  );
}

export default App;