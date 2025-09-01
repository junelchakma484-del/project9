import React from 'react';
import { useQuery } from 'react-query';
import {
  PlayIcon,
  PauseIcon,
  ArrowPathIcon,
  VideoCameraIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import { api } from '../services/api';

function Cameras() {
  const { data: cameras, isLoading, refetch } = useQuery(
    'cameras',
    () => api.get('/api/cameras'),
    {
      refetchInterval: 10000,
    }
  );

  const handleCameraControl = async (cameraId, action) => {
    try {
      await api.post(`/api/cameras/${cameraId}/control`, { action });
      toast.success(`Camera ${action}ed successfully`);
      refetch();
    } catch (error) {
      toast.error(`Failed to ${action} camera`);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cameras</h1>
          <p className="text-gray-600">Manage camera streams and settings</p>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          <ArrowPathIcon className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {cameras?.data?.map((camera) => (
          <div key={camera.id} className="bg-white shadow rounded-lg overflow-hidden">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <VideoCameraIcon className="h-6 w-6 text-gray-400 mr-2" />
                  <h3 className="text-lg font-medium text-gray-900">{camera.name}</h3>
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  camera.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {camera.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Type</p>
                  <p className="text-sm font-medium text-gray-900">{camera.type.toUpperCase()}</p>
                </div>

                <div>
                  <p className="text-sm text-gray-500">Location</p>
                  <p className="text-sm font-medium text-gray-900">{camera.location}</p>
                </div>

                {camera.type === 'ip' && (
                  <div>
                    <p className="text-sm text-gray-500">URL</p>
                    <p className="text-sm font-medium text-gray-900 truncate">{camera.url}</p>
                  </div>
                )}

                {camera.type === 'rpi' && (
                  <div>
                    <p className="text-sm text-gray-500">Device ID</p>
                    <p className="text-sm font-medium text-gray-900">{camera.device_id}</p>
                  </div>
                )}

                <div className="flex space-x-2 pt-4">
                  <button
                    onClick={() => handleCameraControl(camera.id, 'start')}
                    disabled={camera.is_active}
                    className={`flex-1 inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md ${
                      camera.is_active
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-green-600 text-white hover:bg-green-700'
                    }`}
                  >
                    <PlayIcon className="h-4 w-4 mr-1" />
                    Start
                  </button>
                  <button
                    onClick={() => handleCameraControl(camera.id, 'stop')}
                    disabled={!camera.is_active}
                    className={`flex-1 inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md ${
                      !camera.is_active
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-red-600 text-white hover:bg-red-700'
                    }`}
                  >
                    <PauseIcon className="h-4 w-4 mr-1" />
                    Stop
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {cameras?.data?.length === 0 && (
        <div className="text-center py-12">
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No cameras found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by adding cameras to your configuration.
          </p>
        </div>
      )}
    </div>
  );
}

export default Cameras;
