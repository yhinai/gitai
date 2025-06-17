import React from 'react';
import { motion } from 'framer-motion';
import { 
  Server, 
  Cpu, 
  Database, 
  Zap, 
  Users, 
  GitBranch,
  Brain,
  Shield
} from 'lucide-react';
import { StatusCard } from './StatusCard';
import { SystemHealth, EventStats, GitLabProject } from '../hooks/useRealTimeData';

interface SystemOverviewProps {
  health: SystemHealth | null;
  events: EventStats | null;
  project: GitLabProject | null;
  isLoading?: boolean;
}

export const SystemOverview: React.FC<SystemOverviewProps> = ({
  health,
  events,
  project,
  isLoading = false
}) => {
  const getServiceStatus = (serviceName: string) => {
    if (!health?.services[serviceName]) return 'error';
    return health.services[serviceName].status === 'healthy' ? 'healthy' : 'error';
  };

  const getOverallStatus = () => {
    if (!health) return 'error';
    if (health.healthy_services === health.total_services) return 'healthy';
    if (health.healthy_services > health.total_services * 0.7) return 'warning';
    return 'error';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-effect rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold gradient-text">GitAIOps Platform</h1>
            <p className="text-gray-600 mt-1">Real-time AI-powered DevOps monitoring</p>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full animate-pulse ${
              getOverallStatus() === 'healthy' ? 'bg-success-500' :
              getOverallStatus() === 'warning' ? 'bg-warning-500' : 'bg-error-500'
            }`} />
            <span className="text-sm font-medium text-gray-700">
              {getOverallStatus() === 'healthy' ? 'All Systems Operational' :
               getOverallStatus() === 'warning' ? 'Some Issues Detected' : 'System Issues'}
            </span>
          </div>
        </div>
      </div>

      {/* System Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatusCard
          title="System Health"
          value={health ? `${health.healthy_services}/${health.total_services}` : '0/0'}
          subtitle="Services Online"
          icon={Server}
          status={getOverallStatus()}
          isLoading={isLoading}
        />

        <StatusCard
          title="Event Workers"
          value={events?.worker_count || 0}
          subtitle={events?.running ? 'Active' : 'Stopped'}
          icon={Cpu}
          status={events?.running ? 'healthy' : 'error'}
          isLoading={isLoading}
        />

        <StatusCard
          title="Queue Size"
          value={events?.total_queue_size || 0}
          subtitle="Pending Events"
          icon={Database}
          status={events && events.total_queue_size < 10 ? 'healthy' : 'warning'}
          isLoading={isLoading}
        />

        <StatusCard
          title="Processed"
          value={events?.total_processed || 0}
          subtitle="Total Events"
          icon={Zap}
          status="info"
          trend="up"
          isLoading={isLoading}
        />
      </div>

      {/* AI Services Status */}
      <div className="glass-effect rounded-xl p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Brain className="w-5 h-5 text-primary-600" />
          AI Services Status
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="p-4 rounded-lg bg-gradient-to-r from-primary-50 to-primary-100 border border-primary-200"
          >
            <div className="flex items-center gap-3 mb-2">
              <Brain className="w-6 h-6 text-primary-600" />
              <div>
                <h3 className="font-medium text-gray-900">Gemini 2.0 Flash</h3>
                <p className="text-sm text-gray-600">1 API Key Active</p>
              </div>
            </div>
            <div className={`w-2 h-2 rounded-full ${
              getServiceStatus('gemini_client') === 'healthy' ? 'bg-success-500' : 'bg-error-500'
            } animate-pulse`} />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="p-4 rounded-lg bg-gradient-to-r from-success-50 to-success-100 border border-success-200"
          >
            <div className="flex items-center gap-3 mb-2">
              <GitBranch className="w-6 h-6 text-success-600" />
              <div>
                <h3 className="font-medium text-gray-900">GitLab Integration</h3>
                <p className="text-sm text-gray-600">Project {project?.id || 'N/A'}</p>
              </div>
            </div>
            <div className={`w-2 h-2 rounded-full ${
              getServiceStatus('gitlab_client') === 'healthy' ? 'bg-success-500' : 'bg-error-500'
            } animate-pulse`} />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="p-4 rounded-lg bg-gradient-to-r from-warning-50 to-warning-100 border border-warning-200"
          >
            <div className="flex items-center gap-3 mb-2">
              <Shield className="w-6 h-6 text-warning-600" />
              <div>
                <h3 className="font-medium text-gray-900">Security Scanner</h3>
                <p className="text-sm text-gray-600">Real-time Monitoring</p>
              </div>
            </div>
            <div className="w-2 h-2 rounded-full bg-success-500 animate-pulse" />
          </motion.div>
        </div>
      </div>

      {/* Project Information */}
      {project && (
        <div className="glass-effect rounded-xl p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-primary-600" />
            Connected Project
          </h2>
          
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
              <GitBranch className="w-6 h-6 text-primary-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">{project.name}</h3>
              <p className="text-gray-600 text-sm mb-2">{project.description}</p>
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span>ID: {project.id}</span>
                <span>•</span>
                <span>Last activity: {new Date(project.last_activity_at).toLocaleDateString()}</span>
              </div>
            </div>
            <a
              href={project.web_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
            >
              View Project
            </a>
          </div>
        </div>
      )}
    </div>
  );
}; 