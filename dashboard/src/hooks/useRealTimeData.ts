import { useState, useEffect, useCallback } from 'react';

export interface SystemHealth {
  status: string;
  timestamp: string;
  service: string;
  services: Record<string, {
    status: string;
    last_check: string;
    error_count: number;
    dependencies: string[];
  }>;
  healthy_services: number;
  total_services: number;
}

export interface EventStats {
  running: boolean;
  worker_count: number;
  total_queue_size: number;
  queue_sizes: Record<string, number>;
  total_processed: number;
  total_failed: number;
  events_by_type: Record<string, number>;
  avg_processing_time: number;
  processor_stats: Record<string, Record<string, number>>;
  recent_events: any[];
}

export interface GitLabProject {
  id: number;
  name: string;
  path: string;
  description: string;
  web_url: string;
  last_activity_at: string;
}

const API_BASE = 'http://localhost:8000';

export const useRealTimeData = (projectId: number = 70835889) => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [events, setEvents] = useState<EventStats | null>(null);
  const [project, setProject] = useState<GitLabProject | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [healthRes, eventsRes, projectRes] = await Promise.all([
        fetch(`${API_BASE}/health/`),
        fetch(`${API_BASE}/api/v1/metrics/events`),
        fetch(`${API_BASE}/api/v1/gitlab/projects/${projectId}`)
      ]);

      if (healthRes.ok) {
        const healthData = await healthRes.json();
        setHealth(healthData);
      }

      if (eventsRes.ok) {
        const eventsData = await eventsRes.json();
        setEvents(eventsData);
      }

      if (projectRes.ok) {
        const projectData = await projectRes.json();
        setProject(projectData);
      } else {
        // If project fetch fails, set error but don't break other data
        console.warn(`Failed to fetch project ${projectId}:`, projectRes.status);
        setProject(null);
      }

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000); // Update every 2 seconds
    return () => clearInterval(interval);
  }, [fetchData]);

  return {
    health,
    events,
    project,
    loading,
    error,
    refetch: fetchData
  };
}; 