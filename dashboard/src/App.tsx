import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SystemOverview } from './components/SystemOverview';
import { ActivityFeed } from './components/ActivityFeed';
import { ProjectSelector } from './components/ProjectSelector';
import { AIFeatures } from './components/AIFeatures';
import { useRealTimeData } from './hooks/useRealTimeData';

function App() {
  const [currentProjectId, setCurrentProjectId] = useState<number>(70835889);
  const [currentTime, setCurrentTime] = useState(new Date());
  const { health, events, project, loading, error } = useRealTimeData(currentProjectId);

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleProjectChange = (newProjectId: number) => {
    setCurrentProjectId(newProjectId);
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-900 via-slate-900 to-black flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.8, rotateX: -15 }}
          animate={{ opacity: 1, scale: 1, rotateX: 0 }}
          className="glass-dark rounded-2xl p-8 max-w-md text-center relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-red-500/10 to-transparent" />
          <div className="relative z-10">
            <div className="w-20 h-20 bg-gradient-to-br from-red-500 to-red-600 rounded-full flex items-center justify-center mx-auto mb-6 pulse-glow">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-dark-primary mb-3">System Offline</h2>
            <p className="text-dark-secondary mb-6 leading-relaxed">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 font-medium"
            >
              Reconnect System
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative overflow-hidden split-line">
      {/* Floating Orbs */}
      <div className="floating-orb floating-orb-1" />
      <div className="floating-orb floating-orb-2" />
      <div className="floating-orb floating-orb-3" />

      {/* Split Layout Container */}
      <div className="grid grid-cols-2 min-h-screen">
        
        {/* LEFT SIDE - DARK THEME */}
        <motion.div
          initial={{ opacity: 0, x: -100 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="dark-side relative overflow-hidden"
        >
          {/* Matrix Rain Effect */}
          <div className="matrix-rain" />
          
          {/* Dark Side Content */}
          <div className="relative z-10 h-full flex flex-col">
            {/* Dark Header */}
            <motion.header
              initial={{ opacity: 0, y: -30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="glass-dark m-6 rounded-2xl p-6 sliding-border"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center pulse-glow">
                    <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <div>
                    <h1 className="text-2xl font-bold gradient-text-dark">GitAIOps</h1>
                    <p className="text-dark-muted text-sm mono">System Control Center</p>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="flex items-center gap-3 mb-1">
                    <div className={`status-indicator-dark ${
                      health?.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
                    }`} />
                    <span className="text-dark-secondary text-sm mono font-medium">
                      {loading ? (
                        <div className="loading-dots text-blue-400">
                          <span></span><span></span><span></span>
                        </div>
                      ) : 'ONLINE'}
                    </span>
                  </div>
                  <div className="text-xs text-dark-muted mono">
                    {currentTime.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </motion.header>

            {/* Dark Content Area */}
            <div className="flex-1 px-6 pb-6 overflow-y-auto">
              <div className="space-y-6">
                {/* Project Control */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="glass-dark rounded-2xl p-6 card-hover-dark"
                >
                  <h2 className="text-xl font-semibold text-dark-primary mb-4 flex items-center gap-3">
                    <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 8.172V5L8 4z" />
                    </svg>
                    Project Control
                  </h2>
                  <ProjectSelector
                    currentProjectId={currentProjectId}
                    onProjectChange={handleProjectChange}
                    projectName={project?.name}
                  />
                </motion.div>

                {/* AI Operations */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 }}
                  className="glass-dark rounded-2xl p-6 card-hover-dark"
                >
                  <h2 className="text-xl font-semibold text-dark-primary mb-4 flex items-center gap-3">
                    <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    AI Operations
                  </h2>
                  <AIFeatures
                    projectId={currentProjectId}
                    projectName={project?.name}
                  />
                </motion.div>

                {/* System Status */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.9 }}
                  className="glass-dark rounded-2xl p-6 card-hover-dark"
                >
                  <h2 className="text-xl font-semibold text-dark-primary mb-4 flex items-center gap-3">
                    <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    System Metrics
                  </h2>
                  <SystemOverview
                    health={health}
                    events={events}
                    project={project}
                    isLoading={loading}
                  />
                </motion.div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* RIGHT SIDE - LIGHT THEME */}
        <motion.div
          initial={{ opacity: 0, x: 100 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="light-side relative overflow-hidden"
        >
          {/* Light Side Content */}
          <div className="relative z-10 h-full flex flex-col">
            {/* Light Header */}
            <motion.header
              initial={{ opacity: 0, y: -30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="glass-light m-6 rounded-2xl p-6 sliding-border"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold gradient-text-light">Real-time Activity</h2>
                  <p className="text-light-secondary text-sm">Live monitoring for Project #{currentProjectId}</p>
                </div>
                
                <div className="text-right">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-light-primary text-sm font-semibold">
                      {project?.name || 'Loading...'}
                    </span>
                    <div className={`status-indicator-light ${
                      health?.status === 'healthy' ? 'text-green-500' : 'text-red-500'
                    }`} />
                  </div>
                  <div className="text-xs text-light-muted mono">
                    Updates every 2s
                  </div>
                </div>
              </div>
            </motion.header>

            {/* Activity Feed */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="flex-1 mx-6 mb-6"
            >
              <div className="glass-light rounded-2xl p-6 h-full card-hover-light">
                <div className="h-full flex flex-col">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-semibold text-light-primary flex items-center gap-2">
                      <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      Live Event Stream
                    </h3>
                    
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                        <span className="text-xs text-light-muted mono font-medium">STREAMING</span>
                      </div>
                      
                      {loading && (
                        <div className="loading-dots text-blue-600">
                          <span></span><span></span><span></span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex-1 overflow-hidden">
                    <ActivityFeed
                      activities={[]}
                      isLoading={loading}
                    />
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>

      {/* Bottom Status Bar */}
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.2 }}
        className="absolute bottom-0 left-0 right-0 z-20"
      >
        <div className="grid grid-cols-2">
          {/* Dark Side Footer */}
          <div className="glass-dark border-t border-white/10 p-4">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-4 text-dark-secondary">
                <span className="mono font-medium">GitAIOps v1.0.0</span>
                <span>•</span>
                <span>Gemini 2.0 Flash</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                <span className="text-dark-secondary mono text-xs font-medium">SYSTEM ACTIVE</span>
              </div>
            </div>
          </div>
          
          {/* Light Side Footer */}
          <div className="glass-light border-t border-gray-200 p-4">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-4 text-light-secondary">
                <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" 
                   className="hover:text-blue-600 transition-colors font-medium">
                  API Documentation
                </a>
                <span>•</span>
                <a href="http://localhost:8000/health/" target="_blank" rel="noopener noreferrer"
                   className="hover:text-blue-600 transition-colors font-medium">
                  Health Monitor
                </a>
              </div>
              <div className="text-light-muted mono text-xs font-medium">
                {health?.healthy_services || 0}/{health?.total_services || 5} Services Online
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

export default App; 