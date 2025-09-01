import React from 'react';
import { format } from 'date-fns';

function AlertList({ alerts = [] }) {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getAlertIcon = (type) => {
    switch (type) {
      case 'violation':
        return '🚨';
      case 'system':
        return '🔧';
      case 'camera':
        return '📹';
      default:
        return '📢';
    }
  };

  if (alerts.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No alerts at the moment</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <div key={alert.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
          <div className="flex-shrink-0 text-lg">
            {getAlertIcon(alert.alert_type)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-gray-900 truncate">
                {alert.alert_type.charAt(0).toUpperCase() + alert.alert_type.slice(1)} Alert
              </p>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                {alert.severity}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-1 line-clamp-2">
              {alert.message}
            </p>
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-gray-500">
                {format(new Date(alert.timestamp), 'MMM dd, HH:mm')}
              </p>
              {alert.camera_id && (
                <p className="text-xs text-gray-500">
                  Camera: {alert.camera_id}
                </p>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default AlertList;
