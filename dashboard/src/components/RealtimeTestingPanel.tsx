import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp: string;
}

interface RealtimeTestingPanelProps {
  showPopup?: boolean;
  onTogglePopup?: (show: boolean) => void;
}

const RealtimeTestingPanel: React.FC<RealtimeTestingPanelProps> = ({ showPopup, onTogglePopup }) => {
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  useEffect(() => {
    // Connect to testing WebSocket server
    const connectWebSocket = () => {
      try {
        ws.current = new WebSocket('ws://localhost:8765');

        ws.current.onopen = () => {
          setIsConnected(true);
          console.log('Connected to testing WebSocket');
        };

        ws.current.onmessage = (event) => {
          const message = JSON.parse(event.data);
          setMessages((prev) => [...prev, message]);
        };

        ws.current.onclose = () => {
          setIsConnected(false);
          console.log('Disconnected from testing WebSocket');
          // Attempt to reconnect after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };

        ws.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          setIsConnected(false);
        };
      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
      }
    };

    connectWebSocket();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = () => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN && inputMessage.trim()) {
      const message = {
        type: 'test',
        data: inputMessage,
        timestamp: new Date().toISOString()
      };
      ws.current.send(JSON.stringify(message));
      setInputMessage('');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-lg p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Real-time Testing Panel</h3>
        <div className={`px-3 py-1 rounded-full text-sm ${
          isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </div>

      <div className="space-y-4">
        <div className="bg-gray-100 rounded-lg p-4 h-64 overflow-y-auto">
          <div className="space-y-2">
            {messages.map((msg, index) => (
              <div key={index} className="text-sm">
                <span className="text-gray-500">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                <span className="ml-2 font-medium text-blue-600">[{msg.type}]</span>
                {msg.data && (
                  <span className="ml-2 text-gray-700">
                    {typeof msg.data === 'string' ? msg.data : JSON.stringify(msg.data)}
                  </span>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type a test message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={!isConnected}
          />
          <button
            onClick={sendMessage}
            disabled={!isConnected}
            className={`px-6 py-2 rounded-lg font-medium ${
              isConnected
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            Send
          </button>
        </div>
      </div>
    </motion.div>
  );
};

export default RealtimeTestingPanel;