'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { botsAPI } from '@/lib/api';
import { TradingBot } from '@/types';
import { formatCurrency, formatPercentage } from '@/lib/utils';
import { Button, Card, Badge, LoadingSpinner } from '@/components/ui';
import DashboardLayout from '@/components/DashboardLayout';
import { Bot, Play, Pause, Trash2, Edit, TrendingUp, TrendingDown } from 'lucide-react';

export default function BotsList() {
  const router = useRouter();
  const [bots, setBots] = useState<TradingBot[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'running' | 'stopped'>('all');

  useEffect(() => {
    fetchBots();
    const interval = setInterval(fetchBots, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const fetchBots = async () => {
    try {
      const response = await botsAPI.list();
      setBots(response.data);
    } catch (error) {
      console.error('Failed to fetch bots:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartStop = async (bot: TradingBot) => {
    try {
      if (bot.status === 'running') {
        await botsAPI.stop(bot.id);
      } else {
        await botsAPI.start(bot.id);
      }
      fetchBots();
    } catch (error) {
      console.error('Failed to start/stop bot:', error);
      alert('Failed to start/stop bot');
    }
  };

  const handleDelete = async (botId: number) => {
    if (!confirm('Are you sure you want to delete this bot?')) return;

    try {
      await botsAPI.delete(botId);
      fetchBots();
    } catch (error) {
      console.error('Failed to delete bot:', error);
      alert('Failed to delete bot');
    }
  };

  const filteredBots = bots.filter((bot) => {
    if (filter === 'all') return true;
    return bot.status === filter;
  });

  if (loading) {
    return (
      <DashboardLayout>
        <LoadingSpinner size="lg" />
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Trading Bots</h1>
            <p className="text-gray-500 mt-1">Manage your automated trading bots</p>
          </div>
          <Button onClick={() => router.push('/dashboard/bots/new')}>
            <Bot className="h-4 w-4 mr-2" />
            Create New Bot
          </Button>
        </div>

        {/* Filter Tabs */}
        <div className="flex space-x-4 border-b border-gray-200">
          <button
            onClick={() => setFilter('all')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              filter === 'all'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            All Bots ({bots.length})
          </button>
          <button
            onClick={() => setFilter('running')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              filter === 'running'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Running ({bots.filter((b) => b.status === 'running').length})
          </button>
          <button
            onClick={() => setFilter('stopped')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              filter === 'stopped'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Stopped ({bots.filter((b) => b.status === 'stopped').length})
          </button>
        </div>

        {/* Bots Grid */}
        {filteredBots.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <Bot className="h-16 w-16 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-500 mb-4">
                {filter === 'all'
                  ? 'No bots yet. Create your first bot to get started!'
                  : `No ${filter} bots`}
              </p>
              {filter === 'all' && (
                <Button onClick={() => router.push('/dashboard/bots/new')}>
                  Create First Bot
                </Button>
              )}
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredBots.map((bot) => (
              <Card key={bot.id} className="hover:shadow-lg transition-shadow">
                <div className="space-y-4">
                  {/* Bot Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3
                        className="text-lg font-semibold text-gray-900 cursor-pointer hover:text-primary-600"
                        onClick={() => router.push(`/dashboard/bots/${bot.id}`)}
                      >
                        {bot.name}
                      </h3>
                      <p className="text-sm text-gray-500 mt-1">
                        {bot.exchange} • {bot.trading_pair}
                      </p>
                    </div>
                    <Badge
                      variant={
                        bot.status === 'running'
                          ? 'success'
                          : bot.status === 'error'
                          ? 'danger'
                          : 'default'
                      }
                    >
                      {bot.status}
                    </Badge>
                  </div>

                  {/* Performance Metrics */}
                  <div className="grid grid-cols-2 gap-4 py-4 border-t border-b border-gray-100">
                    <div>
                      <p className="text-xs text-gray-500">Capital</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {formatCurrency(bot.current_capital)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">P&L</p>
                      <p
                        className={`text-lg font-semibold ${
                          bot.total_profit_loss >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {formatCurrency(bot.total_profit_loss)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Win Rate</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {bot.win_rate.toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Trades</p>
                      <p className="text-lg font-semibold text-gray-900">{bot.total_trades}</p>
                    </div>
                  </div>

                  {/* ROI Badge */}
                  <div className="flex items-center justify-center">
                    <div
                      className={`flex items-center space-x-1 px-3 py-1 rounded-full ${
                        bot.total_profit_loss >= 0 ? 'bg-green-50' : 'bg-red-50'
                      }`}
                    >
                      {bot.total_profit_loss >= 0 ? (
                        <TrendingUp className="h-4 w-4 text-green-600" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-600" />
                      )}
                      <span
                        className={`text-sm font-medium ${
                          bot.total_profit_loss >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {formatPercentage(
                          ((bot.current_capital - bot.initial_capital) / bot.initial_capital) *
                            100
                        )}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    <Button
                      size="sm"
                      variant={bot.status === 'running' ? 'danger' : 'primary'}
                      onClick={() => handleStartStop(bot)}
                      className="flex-1"
                    >
                      {bot.status === 'running' ? (
                        <>
                          <Pause className="h-4 w-4 mr-1" />
                          Stop
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4 mr-1" />
                          Start
                        </>
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => router.push(`/dashboard/bots/${bot.id}`)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => handleDelete(bot.id)}
                      disabled={bot.status === 'running'}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
