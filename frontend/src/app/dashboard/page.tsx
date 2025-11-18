'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { botsAPI, marketAPI } from '@/lib/api';
import { TradingBot } from '@/types';
import { formatCurrency, formatPercentage } from '@/lib/utils';
import { TrendingUp, TrendingDown, Bot, Activity } from 'lucide-react';

export default function Dashboard() {
  const router = useRouter();
  const [bots, setBots] = useState<TradingBot[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalBots: 0,
    runningBots: 0,
    totalPnL: 0,
    totalCapital: 0,
  });

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    fetchBots();
  }, []);

  const fetchBots = async () => {
    try {
      const response = await botsAPI.list();
      const botsData = response.data;
      setBots(botsData);

      // Calculate stats
      const runningBots = botsData.filter((b: TradingBot) => b.status === 'running').length;
      const totalPnL = botsData.reduce((sum: number, b: TradingBot) => sum + b.total_profit_loss, 0);
      const totalCapital = botsData.reduce((sum: number, b: TradingBot) => sum + b.current_capital, 0);

      setStats({
        totalBots: botsData.length,
        runningBots,
        totalPnL,
        totalCapital,
      });
    } catch (error) {
      console.error('Failed to fetch bots:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Money Trading Bot</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/dashboard/bots/new')}
                className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700"
              >
                New Bot
              </button>
              <button
                onClick={handleLogout}
                className="text-gray-700 hover:text-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Bots</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.totalBots}</p>
              </div>
              <Bot className="h-8 w-8 text-primary-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Running Bots</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.runningBots}</p>
              </div>
              <Activity className="h-8 w-8 text-green-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total P&L</p>
                <p className={`text-2xl font-semibold ${stats.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(stats.totalPnL)}
                </p>
              </div>
              {stats.totalPnL >= 0 ? (
                <TrendingUp className="h-8 w-8 text-green-600" />
              ) : (
                <TrendingDown className="h-8 w-8 text-red-600" />
              )}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Capital</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {formatCurrency(stats.totalCapital)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Bots List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Your Trading Bots</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {bots.length === 0 ? (
              <div className="px-6 py-12 text-center">
                <p className="text-gray-500">No bots yet. Create your first bot to get started!</p>
              </div>
            ) : (
              bots.map((bot) => (
                <div
                  key={bot.id}
                  className="px-6 py-4 hover:bg-gray-50 cursor-pointer"
                  onClick={() => router.push(`/dashboard/bots/${bot.id}`)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-lg font-medium text-gray-900">{bot.name}</h3>
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            bot.status === 'running'
                              ? 'bg-green-100 text-green-800'
                              : bot.status === 'error'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {bot.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        {bot.exchange} • {bot.trading_pair}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {formatCurrency(bot.current_capital)}
                      </p>
                      <p
                        className={`text-sm ${
                          bot.total_profit_loss >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {formatCurrency(bot.total_profit_loss)}
                      </p>
                      <p className="text-xs text-gray-500">
                        Win Rate: {bot.win_rate.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
