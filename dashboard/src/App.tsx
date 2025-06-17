import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { SystemOverview } from './components/SystemOverview';
import { ActivityFeed } from './components/ActivityFeed';
import { ProjectSelector } from './components/ProjectSelector';
import { AIFeatures } from './components/AIFeatures';
import { AutomationDashboard } from './components/AutomationDashboard';
import { useRealTimeData } from './hooks/useRealTimeData';

function App() {
  const [currentProjectId, setCurrentProjectId] = useState<number>(70835889);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeSection, setActiveSection] = useState('overview');
  const { health, events, project, loading, error } = useRealTimeData(currentProjectId);

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleProjectChange = (newProjectId: number) => {
    setCurrentProjectId(newProjectId);
  };

  const sidebarItems = [
    { id: 'overview', name: 'Overview', icon: '📊', description: 'System status and metrics' },
    { id: 'automation', name: 'Automation', icon: '🤖', description: 'Autonomous GitLab operations' },
    { id: 'triage', name: 'MR Triage', icon: '🔍', description: 'AI merge request analysis' },
    { id: 'security', name: 'Security', icon: '🛡️', description: 'Vulnerability scanning' },
    { id: 'pipeline', name: 'Pipeline', icon: '⚡', description: 'Performance optimization' },
    { id: 'activity', name: 'Activity', icon: '📈', description: 'Real-time monitoring' }
  ];

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-lg shadow-lg p-8 max-w-md text-center"
        >
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">System Offline</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Reconnect
          </button>
        </motion.div>
      </div>
    );
  }

  const renderMainContent = () => {
    switch (activeSection) {
      case 'overview':
        return (
          <SystemOverview
            health={health}
            events={events}
            project={project}
            isLoading={loading}
          />
        );
      case 'automation':
        return (
          <AutomationDashboard
            projectId={currentProjectId}
            projectName={project?.name}
          />
        );
      case 'triage':
      case 'security':
      case 'pipeline':
        return (
          <AIFeatures
            projectId={currentProjectId}
            projectName={project?.name}
            activeFeature={activeSection}
          />
        );
      case 'activity':
        return (
          <ActivityFeed
            activities={[]}
            isLoading={loading}
          />
        );
      default:
        return <div>Select a section from the sidebar</div>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Left Sidebar */}
      <motion.div
        initial={{ x: -300 }}
        animate={{ x: 0 }}
        className="w-80 bg-white shadow-lg border-r border-gray-200 flex flex-col"
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">GitAIOps</h1>
              <p className="text-sm text-gray-500">AI-Powered DevOps</p>
            </div>
          </div>
          
          {/* Status */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                health?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <span className="text-gray-600">
                {health?.status === 'healthy' ? 'Online' : 'Offline'}
              </span>
            </div>
            <span className="text-gray-500 font-mono text-xs">
              {currentTime.toLocaleTimeString()}
            </span>
          </div>
        </div>

        {/* Project Selection */}
        <div className="p-4 border-b border-gray-200">
          <ProjectSelector
            currentProjectId={currentProjectId}
            onProjectChange={handleProjectChange}
            projectName={project?.name}
          />
        </div>

        {/* Navigation */}
        <div className="flex-1 p-4">
          <nav className="space-y-2">
            {sidebarItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`w-full text-left p-3 rounded-lg transition-all duration-200 group ${
                  activeSection === item.id
                    ? 'bg-blue-50 border-blue-200 border text-blue-700'
                    : 'hover:bg-gray-50 border border-transparent text-gray-700 hover:text-gray-900'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-lg">{item.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm">{item.name}</div>
                    <div className="text-xs text-gray-500 truncate">{item.description}</div>
                  </div>
                  {activeSection === item.id && (
                    <div className="w-2 h-2 bg-blue-500 rounded-full" />
                  )}
                </div>
              </button>
            ))}
          </nav>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 text-xs text-gray-500">
          <div className="flex items-center justify-between mb-2">
            <span>GitAIOps v1.0.0</span>
            <span>Gemini 2.0</span>
          </div>
          <div className="flex items-center justify-between">
            <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" 
               className="hover:text-blue-600 transition-colors">
              API Docs
            </a>
            <span>{health?.healthy_services || 0}/{health?.total_services || 6} Services</span>
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <motion.header
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="bg-white shadow-sm border-b border-gray-200 p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-gray-900">
                {sidebarItems.find(item => item.id === activeSection)?.name || 'Dashboard'}
              </h2>
              <p className="text-gray-600 text-sm mt-1">
                {project?.name ? `Project: ${project.name}` : `Project ID: ${currentProjectId}`}
              </p>
            </div>
            
            <div className="flex items-center gap-4">
              {loading && (
                <div className="flex items-center gap-2 text-blue-600">
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                  <span className="text-sm">Processing...</span>
                </div>
              )}
              
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900">
                  Real-time Updates
                </div>
                <div className="text-xs text-gray-500">
                  Last update: {new Date().toLocaleTimeString()}
                </div>
              </div>
            </div>
          </div>
        </motion.header>

        {/* Content Area */}
        <motion.main
          key={activeSection}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="flex-1 p-6 overflow-auto"
        >
          {renderMainContent()}
        </motion.main>
      </div>
    </div>
  );
}

export default App;