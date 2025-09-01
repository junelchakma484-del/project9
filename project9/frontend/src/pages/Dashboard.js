import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { io } from 'socket.io-client';
import {
  VideoCameraIcon,
  UserGroupIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  PlayIcon,
  PauseIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import { api } from '../services/api';
import CameraFeed from '../components/CameraFeed';
import StatCard from '../components/StatCard';
import AlertList from '../components/AlertList';

function Dashboard() {
  const [socket, setSocket] = useState(null);
  const [systemStatus, setSystemStatus] = useState({});
  const [recentDetections, setRecentDetections] = useState([]);
  const [recentAlerts, setRecentAlerts] = useState([]);

  // Fetch system status
  const { data: status, isLoading: statusLoading, refetch: refetchStatus } = useQuery(
    'systemStatus',
    () => api.get('/api/status'),
    {
      refetchInterval: 5000, // Refresh every 5 seconds
    }
  );

  // Fetch cameras
  const { data: cameras, isLoading: camerasLoading } = useQuery(
    'cameras',
    () => api.get('/api/cameras'),
    {
      refetchInterval: 10000, // Refresh every 10 seconds
    }
  );

  // Fetch recent detections
  const { data: detections } = useQuery(
    'recentDetections',
    () => api.get('/api/detections?per_page=10'),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  // Fetch recent alerts
  const { data: alerts } = useQuery(
    'recentAlerts',
    () => api.get('/api/alerts?per_page=5'),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  // Socket connection
  useEffect(() => {
    const newSocket = io('http://localhost:5000');
    setSocket(newSocket);

    newSocket.on('connect', () => {
      console.log('Connected to server');
      toast.success('Connected to Face Mask Detection System');
    });

    newSocket.on('disconnect', () => {
      console.log('Disconnected from server');
      toast.error('Disconnected from server');
    });

    newSocket.on('detection_update', (data) => {
      setRecentDetections(prev => [data, ...prev.slice(0, 9)]);
    });

    newSocket.on('alert', (data) => {
      setRecentAlerts(prev => [data, ...prev.slice(0, 4)]);
      toast.error(`New Alert: ${data.message}`, { duration: 5000 });
    });

    newSocket.on('camera_status', (data) => {
      // Update camera status
      console.log('Camera status update:', data);
    });

    return () => {
      newSocket.close();
    };
  }, []);

  // Update data when API responses change
  useEffect(() => {
    if (detections) {
      setRecentDetections(detections.data || []);
    }
  }, [detections]);

  useEffect(() => {
    if (alerts) {
      setRecentAlerts(alerts.data || []);
    }
  }, [alerts]);

  useEffect(() => {
    if (status) {
      setSystemStatus(status.data || {});
    }
  }, [status]);

  const handleCameraControl = async (cameraId, action) => {
    try {
      await api.post(`/api/cameras/${cameraId}/control`, { action });
      toast.success(`Camera ${action}ed successfully`);
      refetchStatus();
    } catch (error) {
      toast.error(`Failed to ${action} camera`);
    }
  };

  const stats = [
    {
      name: 'Active Cameras',
      value: status?.data?.cameras?.active || 0,
      total: status?.data?.cameras?.total || 0,
      icon: VideoCameraIcon,
      color: 'bg-blue-500',
    },
    {
      name: 'Total Detections Today',
      value: status?.data?.detections?.total_today || 0,
      icon: UserGroupIcon,
      color: 'bg-green-500',
    },
    {
      name: 'Violations Today',
      value: status?.data?.detections?.violations_today || 0,
      icon: ExclamationTriangleIcon,
      color: 'bg-red-500',
    },
    {
      name: 'System Status',
      value: status?.data?.status === 'running' ? 'Online' : 'Offline',
      icon: ShieldCheckIcon,
      color: status?.data?.status === 'running' ? 'bg-green-500' : 'bg-red-500',
    },
  ];

  if (statusLoading || camerasLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Real-time face mask detection monitoring</p>
        </div>
        <button
          onClick={() => refetchStatus()}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          <ArrowPathIcon className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <StatCard key={stat.name} {...stat} />
        ))}
      </div>

      {/* Camera Feeds */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Live Camera Feeds
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {cameras?.data?.map((camera) => (
              <div key={camera.id} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-gray-900">{camera.name}</h4>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleCameraControl(camera.id, 'start')}
                      className="p-1 text-green-600 hover:text-green-800"
                      title="Start Camera"
                    >
                      <PlayIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleCameraControl(camera.id, 'stop')}
                      className="p-1 text-red-600 hover:text-red-800"
                      title="Stop Camera"
                    >
                      <PauseIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                <CameraFeed camera={camera} />
                <div className="mt-2 text-xs text-gray-500">
                  {camera.location} • {camera.is_active ? 'Active' : 'Inactive'}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Recent Detections */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent Detections
            </h3>
            <div className="space-y-3">
              {recentDetections.slice(0, 5).map((detection) => (
                <div key={detection.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Camera {detection.camera_id}
                    </p>
                    <p className="text-xs text-gray-500">
                      {detection.faces_detected} faces, {detection.masks_detected} masks
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">
                      {new Date(detection.timestamp).toLocaleTimeString()}
                    </p>
                    {detection.no_mask_count > 0 && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        {detection.no_mask_count} violations
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent Alerts
            </h3>
            <AlertList alerts={recentAlerts} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
