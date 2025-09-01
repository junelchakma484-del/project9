import React, { useState, useEffect } from 'react';
import { VideoCameraIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

function CameraFeed({ camera }) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    // Simulate camera feed loading
    if (camera.is_active) {
      const timer = setTimeout(() => {
        setIsLoading(false);
      }, 1000);
      return () => clearTimeout(timer);
    } else {
      setIsLoading(false);
      setHasError(true);
    }
  }, [camera.is_active]);

  if (isLoading) {
    return (
      <div className="bg-gray-200 rounded-lg h-32 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (hasError || !camera.is_active) {
    return (
      <div className="bg-gray-200 rounded-lg h-32 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
          <p className="text-sm text-gray-500">Camera Offline</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-200 rounded-lg h-32 flex items-center justify-center relative">
      <div className="text-center">
        <VideoCameraIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
        <p className="text-sm text-gray-500">Live Feed</p>
        <p className="text-xs text-gray-400 mt-1">{camera.type.toUpperCase()}</p>
      </div>
      
      {/* Status indicator */}
      <div className="absolute top-2 right-2">
        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
      </div>
    </div>
  );
}

export default CameraFeed;
