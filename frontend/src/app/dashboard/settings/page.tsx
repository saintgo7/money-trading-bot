'use client';

import { useState } from 'react';
import { Card, Input, Button } from '@/components/ui';
import DashboardLayout from '@/components/DashboardLayout';
import { Save, Key, Bell, Shield } from 'lucide-react';

export default function Settings() {
  const [activeTab, setActiveTab] = useState<'profile' | 'api' | 'notifications' | 'security'>('profile');
  const [saving, setSaving] = useState(false);

  const tabs = [
    { id: 'profile', label: 'Profile', icon: Save },
    { id: 'api', label: 'API Keys', icon: Key },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
  ];

  const handleSave = async () => {
    setSaving(true);
    // TODO: Implement save functionality
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setSaving(false);
    alert('Settings saved successfully!');
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <Card className="p-2">
              <nav className="space-y-1">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md transition-colors ${
                        activeTab === tab.id
                          ? 'bg-primary-50 text-primary-600'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <Icon className="h-5 w-5" />
                      <span className="font-medium">{tab.label}</span>
                    </button>
                  );
                })}
              </nav>
            </Card>
          </div>

          {/* Content */}
          <div className="lg:col-span-3">
            <Card>
              {activeTab === 'profile' && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-gray-900">Profile Settings</h2>

                  <Input label="Full Name" placeholder="John Doe" />
                  <Input label="Email" type="email" placeholder="john@example.com" />
                  <Input label="Username" placeholder="johndoe" />

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Subscription Tier
                    </label>
                    <div className="flex items-center space-x-2">
                      <span className="px-3 py-2 bg-gray-100 rounded-md text-gray-700">
                        Free
                      </span>
                      <Button size="sm" variant="primary">
                        Upgrade to Pro
                      </Button>
                    </div>
                  </div>

                  <Button onClick={handleSave} disabled={saving}>
                    {saving ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              )}

              {activeTab === 'api' && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-gray-900">API Keys</h2>

                  <div className="space-y-4">
                    <div className="p-4 bg-blue-50 rounded-md">
                      <p className="text-sm text-blue-900">
                        <strong>Important:</strong> Your API keys are stored securely and encrypted. Never share them with anyone.
                      </p>
                    </div>

                    <div className="space-y-4">
                      <h3 className="font-medium text-gray-900">Binance</h3>
                      <Input label="API Key" type="password" placeholder="Enter Binance API Key" />
                      <Input label="API Secret" type="password" placeholder="Enter Binance API Secret" />
                      <label className="flex items-center space-x-2">
                        <input type="checkbox" className="rounded" />
                        <span className="text-sm text-gray-700">Use Testnet</span>
                      </label>
                    </div>

                    <div className="space-y-4 pt-4 border-t">
                      <h3 className="font-medium text-gray-900">Upbit</h3>
                      <Input label="Access Key" type="password" placeholder="Enter Upbit Access Key" />
                      <Input label="Secret Key" type="password" placeholder="Enter Upbit Secret Key" />
                    </div>

                    <div className="space-y-4 pt-4 border-t">
                      <h3 className="font-medium text-gray-900">KIS (한국투자증권)</h3>
                      <Input label="App Key" type="password" placeholder="Enter KIS App Key" />
                      <Input label="App Secret" type="password" placeholder="Enter KIS App Secret" />
                      <Input label="Account Number" placeholder="Enter Account Number" />
                    </div>
                  </div>

                  <Button onClick={handleSave} disabled={saving}>
                    {saving ? 'Saving...' : 'Save API Keys'}
                  </Button>
                </div>
              )}

              {activeTab === 'notifications' && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-gray-900">Notification Settings</h2>

                  <div className="space-y-4">
                    <label className="flex items-center justify-between p-4 border rounded-md">
                      <div>
                        <p className="font-medium text-gray-900">Trade Executed</p>
                        <p className="text-sm text-gray-500">Get notified when a trade is executed</p>
                      </div>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </label>

                    <label className="flex items-center justify-between p-4 border rounded-md">
                      <div>
                        <p className="font-medium text-gray-900">Bot Started/Stopped</p>
                        <p className="text-sm text-gray-500">Get notified when bot status changes</p>
                      </div>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </label>

                    <label className="flex items-center justify-between p-4 border rounded-md">
                      <div>
                        <p className="font-medium text-gray-900">Daily Performance Report</p>
                        <p className="text-sm text-gray-500">Receive daily performance summary</p>
                      </div>
                      <input type="checkbox" className="rounded" />
                    </label>

                    <label className="flex items-center justify-between p-4 border rounded-md">
                      <div>
                        <p className="font-medium text-gray-900">Stop Loss Triggered</p>
                        <p className="text-sm text-gray-500">Get notified when stop loss is triggered</p>
                      </div>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </label>

                    <label className="flex items-center justify-between p-4 border rounded-md">
                      <div>
                        <p className="font-medium text-gray-900">Take Profit Reached</p>
                        <p className="text-sm text-gray-500">Get notified when take profit is reached</p>
                      </div>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </label>
                  </div>

                  <Button onClick={handleSave} disabled={saving}>
                    {saving ? 'Saving...' : 'Save Preferences'}
                  </Button>
                </div>
              )}

              {activeTab === 'security' && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-gray-900">Security Settings</h2>

                  <div className="space-y-4">
                    <h3 className="font-medium text-gray-900">Change Password</h3>
                    <Input label="Current Password" type="password" />
                    <Input label="New Password" type="password" />
                    <Input label="Confirm New Password" type="password" />
                    <Button variant="primary">Update Password</Button>
                  </div>

                  <div className="space-y-4 pt-6 border-t">
                    <h3 className="font-medium text-gray-900">Two-Factor Authentication</h3>
                    <p className="text-sm text-gray-600">
                      Add an extra layer of security to your account
                    </p>
                    <Button variant="secondary">Enable 2FA</Button>
                  </div>

                  <div className="space-y-4 pt-6 border-t">
                    <h3 className="font-medium text-gray-900">Active Sessions</h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                        <div>
                          <p className="font-medium text-gray-900">Current Session</p>
                          <p className="text-sm text-gray-500">Chrome on Windows • 192.168.1.1</p>
                        </div>
                        <span className="text-sm text-green-600">Active</span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-6 border-t">
                    <Button variant="danger">Delete Account</Button>
                    <p className="text-sm text-gray-500 mt-2">
                      Permanently delete your account and all data
                    </p>
                  </div>
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
