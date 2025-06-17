import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Activity {
  id: string;
  type: 'ai_analysis' | 'gitlab_event' | 'system_update' | 'user_action' | 'health_check';
  title: string;
  description: string;
  timestamp: Date;
  status: 'success' | 'warning' | 'error' | 'info';
  metadata?: Record<string, any>;
}

interface ActivityFeedProps {
  activities: Activity[];
  isLoading: boolean;
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ activities, isLoading }) => {
  const [liveActivities, setLiveActivities] = useState<Activity[]>([]);

  // Simulate real-time activities
  useEffect(() => {
    const generateActivity = (): Activity => {
      const types: Activity['type'][] = ['ai_analysis', 'gitlab_event', 'system_update', 'user_action', 'health_check'];
      const statuses: Activity['status'][] = ['success', 'warning', 'error', 'info'];
      
      const activityTemplates = {
        ai_analysis: [
          { title: 'AI Triage Analysis', description: 'Analyzing merge request #1247 for code quality issues' },
          { title: 'Smart Code Review', description: 'Generated automated review comments for PR #892' },
          { title: 'Vulnerability Scan', description: 'Detected potential security issue in authentication module' },
          { title: 'Performance Analysis', description: 'Identified optimization opportunities in database queries' },
        ],
        gitlab_event: [
          { title: 'New Merge Request', description: 'MR #1248 opened by developer@company.com' },
          { title: 'Pipeline Completed', description: 'Build pipeline finished successfully for branch feature/auth' },
          { title: 'Issue Updated', description: 'Issue #456 status changed to "In Progress"' },
          { title: 'Commit Pushed', description: 'New commits pushed to main branch' },
        ],
        system_update: [
          { title: 'Service Health Check', description: 'All 5 services responding normally' },
          { title: 'Cache Refresh', description: 'Project metadata cache updated successfully' },
          { title: 'API Rate Limit', description: 'GitLab API usage: 847/5000 requests per hour' },
          { title: 'Database Sync', description: 'Event processing queue synchronized' },
        ],
        user_action: [
          { title: 'Project Switch', description: 'Monitoring switched to project #70835889' },
          { title: 'Dashboard Access', description: 'Real-time dashboard session initiated' },
          { title: 'AI Feature Used', description: 'Triage analysis requested for current project' },
          { title: 'Settings Updated', description: 'Notification preferences modified' },
        ],
        health_check: [
          { title: 'OpenRouter Status', description: 'Claude Sonnet 4 API responding with 98ms latency' },
          { title: 'GitLab Connection', description: 'GitLab API connection stable and authenticated' },
          { title: 'Neo4j Database', description: 'Graph database connection established' },
          { title: 'Event Processing', description: '5 workers processing events at 12.3 events/sec' },
        ]
      };

      const type = types[Math.floor(Math.random() * types.length)];
      const template = activityTemplates[type][Math.floor(Math.random() * activityTemplates[type].length)];
      const status = statuses[Math.floor(Math.random() * statuses.length)];

      return {
        id: `activity_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type,
        title: template.title,
        description: template.description,
        timestamp: new Date(),
        status,
        metadata: {
          source: 'live_simulation',
          priority: Math.random() > 0.7 ? 'high' : 'normal'
        }
      };
    };

    const interval = setInterval(() => {
      const newActivity = generateActivity();
      setLiveActivities(prev => [newActivity, ...prev.slice(0, 49)]); // Keep last 50 activities
    }, 3000 + Math.random() * 4000); // Random interval between 3-7 seconds

    return () => clearInterval(interval);
  }, []);

  const getActivityIcon = (type: Activity['type']) => {
    switch (type) {
      case 'ai_analysis':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        );
      case 'gitlab_event':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
        );
      case 'system_update':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        );
      case 'user_action':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        );
      case 'health_check':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const getStatusColor = (status: Activity['status']) => {
    switch (status) {
      case 'success':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'warning':
        return 'text-amber-700 bg-amber-50 border-amber-200';
      case 'error':
        return 'text-red-700 bg-red-50 border-red-200';
      case 'info':
        return 'text-blue-700 bg-blue-50 border-blue-200';
      default:
        return 'text-slate-700 bg-slate-50 border-slate-200';
    }
  };

  const allActivities = [...liveActivities, ...activities];

  return (
    <div className="h-full flex flex-col">
      {/* Activity Stream */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-2">
        <AnimatePresence mode="popLayout">
          {allActivities.length === 0 && !isLoading ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12"
            >
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-light-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-light-primary mb-2">No Activity Yet</h3>
              <p className="text-light-muted text-sm">
                Real-time events will appear here as they happen
              </p>
            </motion.div>
          ) : (
            allActivities.map((activity, index) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, y: -20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, x: 100, scale: 0.95 }}
                transition={{ 
                  duration: 0.3,
                  delay: index < 3 ? index * 0.1 : 0,
                  type: "spring",
                  stiffness: 300,
                  damping: 30
                }}
                className={`glass-light rounded-xl p-4 border card-hover-light ${getStatusColor(activity.status)}`}
              >
                <div className="flex items-start gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${getStatusColor(activity.status)}`}>
                    {getActivityIcon(activity.type)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="font-semibold text-light-primary text-sm truncate">
                        {activity.title}
                      </h4>
                      <span className="text-xs text-light-muted mono flex-shrink-0 ml-2 font-medium">
                        {activity.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    
                    <p className="text-light-secondary text-xs leading-relaxed mb-2">
                      {activity.description}
                    </p>
                    
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${getStatusColor(activity.status)}`}>
                        {activity.status.toUpperCase()}
                      </span>
                      
                      <span className="text-xs text-light-muted capitalize font-medium">
                        {activity.type.replace('_', ' ')}
                      </span>
                      
                      {activity.metadata?.priority === 'high' && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-bold bg-orange-100 text-orange-700 border border-orange-200">
                          HIGH
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      {/* Loading Indicator */}
      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center justify-center py-4 border-t border-slate-200"
        >
          <div className="loading-dots text-blue-600 mr-3">
            <span></span><span></span><span></span>
          </div>
          <span className="text-sm text-light-secondary font-medium">Loading new events...</span>
        </motion.div>
      )}

      {/* Activity Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="mt-4 pt-4 border-t border-slate-200"
      >
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-lg font-bold text-light-primary">{allActivities.length}</div>
            <div className="text-xs text-light-muted font-medium">Total Events</div>
          </div>
          <div>
            <div className="text-lg font-bold text-green-600">
              {allActivities.filter(a => a.status === 'success').length}
            </div>
            <div className="text-xs text-light-muted font-medium">Success</div>
          </div>
          <div>
            <div className="text-lg font-bold text-amber-600">
              {allActivities.filter(a => a.status === 'warning').length}
            </div>
            <div className="text-xs text-light-muted font-medium">Warnings</div>
          </div>
          <div>
            <div className="text-lg font-bold text-red-600">
              {allActivities.filter(a => a.status === 'error').length}
            </div>
            <div className="text-xs text-light-muted font-medium">Errors</div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}; 