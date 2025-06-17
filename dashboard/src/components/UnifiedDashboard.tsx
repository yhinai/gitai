import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import RealtimeTestingPanel from './RealtimeTestingPanel';

interface SystemComponent {
  name: string;
  status: 'healthy' | 'warning' | 'error' | 'offline';
  last_check: string;
  metrics: Record<string, any>;
  endpoint?: string;
  version?: string;
  uptime?: number;
}

interface DashboardState {
  timestamp: string;
  components: Record<string, SystemComponent>;
  active_workflows: any[];
  recent_events: any[];
  performance_metrics: Record<string, any>;
  security_alerts: any[];
  test_results: Record<string, any>;
  ai_operations: Record<string, any>;
  user_sessions: number;
  system_load: Record<string, any>;
}

const UnifiedDashboard: React.FC = () => {
  const [dashboardState, setDashboardState] = useState<DashboardState | null>(null);
  const [connected, setConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [showTestingPopup, setShowTestingPopup] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Connect to unified dashboard WebSocket
  const connectToUnifiedDashboard = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionStatus('connecting');
    
    try {
      const ws = new WebSocket('ws://localhost:8767');
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('Connected to Unified Dashboard');
        setConnected(true);
        setConnectionStatus('connected');
        
        // Send ping to establish connection
        ws.send(JSON.stringify({ type: 'ping' }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'initial_state' || data.type === 'dashboard_update') {
            setDashboardState(data.state);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('Disconnected from Unified Dashboard');
        setConnected(false);
        setConnectionStatus('disconnected');
        
        // Attempt to reconnect after 3 seconds
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        reconnectTimeoutRef.current = setTimeout(connectToUnifiedDashboard, 3000);
      };

      ws.onerror = (error) => {
        console.error('Unified Dashboard WebSocket error:', error);
        setConnectionStatus('disconnected');
      };

    } catch (error) {
      console.error('Failed to connect to Unified Dashboard:', error);
      setConnectionStatus('disconnected');
    }
  };

  useEffect(() => {
    connectToUnifiedDashboard();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-400 bg-green-400/20';
      case 'warning': return 'text-yellow-400 bg-yellow-400/20';
      case 'error': return 'text-red-400 bg-red-400/20';
      case 'offline': return 'text-gray-400 bg-gray-400/20';
      default: return 'text-gray-400 bg-gray-400/20';
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const triggerAction = (action: string, parameters: any = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'trigger_action',
        action,
        parameters
      }));
    }
  };

  if (!connected || !dashboardState) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="mb-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto"></div>
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">
            {connectionStatus === 'connecting' ? 'Connecting to' : 'Reconnecting to'} Unified Dashboard
          </h2>
          <p className="text-gray-400">
            Establishing real-time connection...
          </p>
        </motion.div>
      </div>
    );
  }

  const healthScore = dashboardState.performance_metrics?.health_score || 0;
  const systemMetrics = dashboardState.performance_metrics?.system || {};
  const appMetrics = dashboardState.performance_metrics?.application || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">
                🚀 GitAIOps Unified Dashboard
              </h1>
              <p className="text-gray-400">
                Real-time system monitoring and AI operations control center
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor('healthy')}`}>
                ● Connected
              </div>
              <div className="text-right">
                <div className="text-white font-semibold">{dashboardState.user_sessions} Users</div>
                <div className="text-gray-400 text-sm">Active Sessions</div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* System Health Overview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8"
        >
          <div className="backdrop-blur-md bg-white/10 rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">System Health</h3>
              <div className="text-2xl">🏥</div>
            </div>
            <div className="text-3xl font-bold text-green-400 mb-2">
              {Math.round(healthScore * 100)}%
            </div>
            <div className="text-gray-400 text-sm">Overall Health Score</div>
          </div>

          <div className="backdrop-blur-md bg-white/10 rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">CPU Usage</h3>
              <div className="text-2xl">⚡</div>
            </div>
            <div className="text-3xl font-bold text-blue-400 mb-2">
              {Math.round(systemMetrics.cpu_percent || 0)}%
            </div>
            <div className="text-gray-400 text-sm">System Load</div>
          </div>

          <div className="backdrop-blur-md bg-white/10 rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Memory</h3>
              <div className="text-2xl">🧠</div>
            </div>
            <div className="text-3xl font-bold text-purple-400 mb-2">
              {Math.round(systemMetrics.memory_percent || 0)}%
            </div>
            <div className="text-gray-400 text-sm">RAM Usage</div>
          </div>

          <div className="backdrop-blur-md bg-white/10 rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Components</h3>
              <div className="text-2xl">🔧</div>
            </div>
            <div className="text-3xl font-bold text-cyan-400 mb-2">
              {appMetrics.components_healthy || 0}/{appMetrics.total_components || 0}
            </div>
            <div className="text-gray-400 text-sm">Healthy Services</div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* System Components */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="backdrop-blur-md bg-white/10 rounded-xl p-6 border border-white/20"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white">System Components</h2>
              <button
                onClick={() => triggerAction('run_health_check')}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm font-medium transition-colors"
              >
                Refresh Health
              </button>
            </div>
            
            <div className="space-y-3">
              {Object.entries(dashboardState.components).map(([name, component]) => (
                <div key={name} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${
                      component.status === 'healthy' ? 'bg-green-400' :
                      component.status === 'warning' ? 'bg-yellow-400' :
                      component.status === 'error' ? 'bg-red-400' : 'bg-gray-400'
                    }`}></div>
                    <div>
                      <div className="text-white font-medium capitalize">
                        {name.replace('_', ' ')}
                      </div>
                      <div className="text-gray-400 text-sm">
                        Last check: {new Date(component.last_check).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(component.status)}`}>
                    {component.status.toUpperCase()}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Recent Events */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="backdrop-blur-md bg-white/10 rounded-xl p-6 border border-white/20"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white">Recent Events</h2>
              <div className="text-gray-400 text-sm">
                {dashboardState.recent_events.length} events
              </div>
            </div>
            
            <div className="space-y-3 max-h-80 overflow-y-auto">
              <AnimatePresence>
                {dashboardState.recent_events.slice(0, 10).map((event, index) => (
                  <motion.div
                    key={event.id || index}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="p-3 bg-white/5 rounded-lg"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="text-white text-sm font-medium mb-1">
                          {event.message}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-400">
                          <span className="capitalize">{event.source}</span>
                          <span>•</span>
                          <span>{new Date(event.timestamp).toLocaleTimeString()}</span>
                        </div>
                      </div>
                      <div className={`px-2 py-1 rounded text-xs font-medium ${
                        event.priority === 'high' ? 'text-red-400 bg-red-400/20' :
                        event.priority === 'medium' ? 'text-yellow-400 bg-yellow-400/20' :
                        'text-blue-400 bg-blue-400/20'
                      }`}>
                        {event.priority?.toUpperCase() || 'INFO'}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </motion.div>

          {/* Real-time Testing Panel */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="backdrop-blur-md bg-white/10 rounded-xl border border-white/20 overflow-hidden"
          >
            <RealtimeTestingPanel 
              showPopup={showTestingPopup}
              onTogglePopup={setShowTestingPopup}
            />
          </motion.div>
        </div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 backdrop-blur-md bg-white/10 rounded-xl p-6 border border-white/20"
        >
          <h2 className="text-xl font-bold text-white mb-6">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <button
              onClick={() => triggerAction('trigger_ai_analysis', { type: 'security' })}
              className="p-4 bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 rounded-lg text-white transition-colors"
            >
              <div className="text-2xl mb-2">🛡️</div>
              <div className="font-medium">Security Scan</div>
            </button>
            
            <button
              onClick={() => triggerAction('trigger_ai_analysis', { type: 'performance' })}
              className="p-4 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 rounded-lg text-white transition-colors"
            >
              <div className="text-2xl mb-2">⚡</div>
              <div className="font-medium">Performance Analysis</div>
            </button>
            
            <button
              onClick={() => triggerAction('run_health_check')}
              className="p-4 bg-green-600/20 hover:bg-green-600/30 border border-green-500/30 rounded-lg text-white transition-colors"
            >
              <div className="text-2xl mb-2">🏥</div>
              <div className="font-medium">Health Check</div>
            </button>
            
            <button
              onClick={() => triggerAction('export_metrics')}
              className="p-4 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 rounded-lg text-white transition-colors"
            >
              <div className="text-2xl mb-2">📊</div>
              <div className="font-medium">Export Metrics</div>
            </button>
            
            <button
              onClick={() => setShowTestingPopup(!showTestingPopup)}
              className="p-4 bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/30 rounded-lg text-white transition-colors"
            >
              <div className="text-2xl mb-2">🧪</div>
              <div className="font-medium">Testing Popup</div>
            </button>
          </div>
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-8 text-center text-gray-400 text-sm"
        >
          <p>
            Last updated: {new Date(dashboardState.timestamp).toLocaleString()}
            • Uptime: {formatUptime(appMetrics.uptime || 0)}
            • Health Score: {Math.round(healthScore * 100)}%
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default UnifiedDashboard;