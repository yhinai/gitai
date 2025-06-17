import React from 'react';
import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

interface StatusCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  status: 'healthy' | 'warning' | 'error' | 'info';
  trend?: 'up' | 'down' | 'stable';
  isLoading?: boolean;
}

const statusColors = {
  healthy: 'text-success-600 bg-success-50 border-success-200',
  warning: 'text-warning-600 bg-warning-50 border-warning-200',
  error: 'text-error-600 bg-error-50 border-error-200',
  info: 'text-primary-600 bg-primary-50 border-primary-200'
};

const statusIndicators = {
  healthy: 'bg-success-500',
  warning: 'bg-warning-500',
  error: 'bg-error-500',
  info: 'bg-primary-500'
};

export const StatusCard: React.FC<StatusCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  status,
  trend,
  isLoading = false
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="glass-effect rounded-xl p-6 card-hover"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <div className={`p-2 rounded-lg ${statusColors[status]}`}>
              <Icon className="w-5 h-5" />
            </div>
            <div className={`status-indicator ${statusIndicators[status]}`} />
          </div>
          
          <h3 className="text-sm font-medium text-gray-600 mb-1">{title}</h3>
          
          {isLoading ? (
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded w-20 mb-1"></div>
              <div className="h-4 bg-gray-200 rounded w-16"></div>
            </div>
          ) : (
            <>
              <div className="text-2xl font-bold text-gray-900 mb-1">
                {value}
              </div>
              {subtitle && (
                <p className="text-sm text-gray-500">{subtitle}</p>
              )}
            </>
          )}
        </div>
        
        {trend && !isLoading && (
          <div className={`text-xs px-2 py-1 rounded-full ${
            trend === 'up' ? 'text-success-600 bg-success-50' :
            trend === 'down' ? 'text-error-600 bg-error-50' :
            'text-gray-600 bg-gray-50'
          }`}>
            {trend === 'up' ? '↗' : trend === 'down' ? '↘' : '→'}
          </div>
        )}
      </div>
    </motion.div>
  );
}; 