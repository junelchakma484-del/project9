import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  CogIcon,
  BellIcon,
  CameraIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import { api } from '../services/api';

function Settings() {
  const [activeTab, setActiveTab] = useState('general');
  const [isLoading, setIsLoading] = useState(false);

  const { data: settings, isLoading: settingsLoading } = useQuery(
    'settings',
    () => api.get('/api/settings'),
    {
      refetchInterval: false,
    }
  );

  const handleSaveSettings = async (newSettings) => {
    setIsLoading(true);
    try {
      await api.put('/api/settings', newSettings);
      toast.success('Settings saved successfully');
    } catch (error) {
      toast.error('Failed to save settings');
    } finally {
      setIsLoading(false);
    }
  };

  const tabs = [
    { id: 'general', name: 'General', icon: CogIcon },
    { id: 'cameras', name: 'Cameras', icon: CameraIcon },
    { id: 'alerts', name: 'Alerts', icon: BellIcon },
    { id: 'security', name: 'Security', icon: ShieldCheckIcon },
  ];

  if (settingsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Configure system settings and preferences</p>
      </div>

      <div className="bg-white shadow rounded-lg">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
              >
                <tab.icon className="h-4 w-4 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'general' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">General Settings</h3>
              
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    System Name
                  </label>
                  <input
                    type="text"
                    defaultValue="Face Mask Detection System"
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Time Zone
                  </label>
                  <select className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm">
                    <option>UTC</option>
                    <option>America/New_York</option>
                    <option>Europe/London</option>
                    <option>Asia/Tokyo</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Language
                  </label>
                  <select className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm">
                    <option>English</option>
                    <option>Spanish</option>
                    <option>French</option>
                    <option>German</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Auto Refresh Interval (seconds)
                  </label>
                  <input
                    type="number"
                    defaultValue={30}
                    min={5}
                    max={300}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'cameras' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">Camera Settings</h3>
              
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Default Frame Rate
                  </label>
                  <input
                    type="number"
                    defaultValue={30}
                    min={1}
                    max={60}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Processing Interval (seconds)
                  </label>
                  <input
                    type="number"
                    defaultValue={0.1}
                    min={0.01}
                    max={1}
                    step={0.01}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Confidence Threshold
                  </label>
                  <input
                    type="number"
                    defaultValue={0.8}
                    min={0.1}
                    max={1}
                    step={0.1}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Max Workers
                  </label>
                  <input
                    type="number"
                    defaultValue={4}
                    min={1}
                    max={16}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div className="flex items-center">
                <input
                  id="auto-start-cameras"
                  type="checkbox"
                  defaultChecked
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="auto-start-cameras" className="ml-2 block text-sm text-gray-900">
                  Auto-start cameras on system startup
                </label>
              </div>
            </div>
          )}

          {activeTab === 'alerts' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">Alert Settings</h3>
              
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Alert Cooldown (seconds)
                  </label>
                  <input
                    type="number"
                    defaultValue={300}
                    min={60}
                    max={3600}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Violation Threshold
                  </label>
                  <input
                    type="number"
                    defaultValue={3}
                    min={1}
                    max={10}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-900">Notification Channels</h4>
                
                <div className="flex items-center">
                  <input
                    id="telegram-enabled"
                    type="checkbox"
                    defaultChecked
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="telegram-enabled" className="ml-2 block text-sm text-gray-900">
                    Enable Telegram notifications
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    id="email-enabled"
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="email-enabled" className="ml-2 block text-sm text-gray-900">
                    Enable email notifications
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    id="mqtt-enabled"
                    type="checkbox"
                    defaultChecked
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="mqtt-enabled" className="ml-2 block text-sm text-gray-900">
                    Enable MQTT notifications
                  </label>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">Security Settings</h3>
              
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Session Timeout (minutes)
                  </label>
                  <input
                    type="number"
                    defaultValue={30}
                    min={5}
                    max={480}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Max Login Attempts
                  </label>
                  <input
                    type="number"
                    defaultValue={5}
                    min={3}
                    max={10}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-900">Access Control</h4>
                
                <div className="flex items-center">
                  <input
                    id="require-authentication"
                    type="checkbox"
                    defaultChecked
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="require-authentication" className="ml-2 block text-sm text-gray-900">
                    Require authentication for API access
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    id="enable-audit-log"
                    type="checkbox"
                    defaultChecked
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="enable-audit-log" className="ml-2 block text-sm text-gray-900">
                    Enable audit logging
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    id="encrypt-data"
                    type="checkbox"
                    defaultChecked
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="encrypt-data" className="ml-2 block text-sm text-gray-900">
                    Encrypt sensitive data
                  </label>
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={() => handleSaveSettings({})}
              disabled={isLoading}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;
