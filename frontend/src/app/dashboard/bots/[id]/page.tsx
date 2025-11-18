'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { botsAPI } from '@/lib/api';
import { TradingBot, Order, Trade } from '@/types';
import { formatCurrency, formatPercentage, formatDate } from '@/lib/utils';
import { Button, Card, Badge, LoadingSpinner } from '@/components/ui';
import DashboardLayout from '@/components/DashboardLayout';
import { Play, Pause, TrendingUp, TrendingDown, Activity } from 'lucide-react';

export default function BotDetail() {
  const router = useRouter();
  const params = useParams();
  const botId = parseInt(params.id as string);

  const [bot, setBot] = useState<TradingBot | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [performance, setPerformance] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (botId) {
      fetchBotData();
      const interval = setInterval(fetchBotData, 10000); // Refresh every 10s
      return () => clearInterval(interval);
    }
  }, [botId]);

  const fetchBotData = async () => {
    try {
      const [botRes, ordersRes, tradesRes, perfRes] = await Promise.all([
        botsAPI.get(botId),
        botsAPI.getOrders(botId),
        botsAPI.getTrades(botId),
        botsAPI.getPerformance(botId),
      ]);

      setBot(botRes.data);
      setOrders(ordersRes.data);
      setTrades(tradesRes.data);
      setPerformance(perfRes.data);
    } catch (error) {
      console.error('Failed to fetch bot data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartStop = async () => {
    if (!bot) return;

    try {
      if (bot.status === 'running') {
        await botsAPI.stop(botId);
      } else {
        await botsAPI.start(botId);
      }
      fetchBotData();
    } catch (error) {
      console.error('Failed to start/stop bot:', error);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <LoadingSpinner size="lg" />
      </DashboardLayout>
    );
  }

  if (!bot) {
    return (
      <DashboardLayout>
        <div className="text-center">
          <p className="text-gray-500">Bot not found</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{bot.name}</h1>
            <p className="text-gray-500 mt-1">
              {bot.exchange} • {bot.trading_pair}
            </p>
          </div>
          <div className="flex items-center space-x-4">
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
            <Button onClick={handleStartStop} variant="primary">
              {bot.status === 'running' ? (
                <>
                  <Pause className="h-4 w-4 mr-2" />
                  Stop
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Start
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Performance Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Current Capital</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {formatCurrency(bot.current_capital)}
                </p>
              </div>
              <Activity className="h-8 w-8 text-primary-600" />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total P&L</p>
                <p
                  className={`text-2xl font-semibold ${
                    bot.total_profit_loss >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {formatCurrency(bot.total_profit_loss)}
                </p>
              </div>
              {bot.total_profit_loss >= 0 ? (
                <TrendingUp className="h-8 w-8 text-green-600" />
              ) : (
                <TrendingDown className="h-8 w-8 text-red-600" />
              )}
            </div>
          </Card>

          <Card>
            <div>
              <p className="text-sm font-medium text-gray-600">Win Rate</p>
              <p className="text-2xl font-semibold text-gray-900">
                {bot.win_rate.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {bot.winning_trades}W / {bot.losing_trades}L
              </p>
            </div>
          </Card>

          <Card>
            <div>
              <p className="text-sm font-medium text-gray-600">ROI</p>
              <p
                className={`text-2xl font-semibold ${
                  performance?.roi >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {formatPercentage(performance?.roi || 0)}
              </p>
              <p className="text-xs text-gray-500 mt-1">{bot.total_trades} trades</p>
            </div>
          </Card>
        </div>

        {/* Recent Trades */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Trades</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Entry Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Entry Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Exit Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    P&L
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {trades.slice(0, 10).map((trade) => (
                  <tr key={trade.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(trade.entry_time)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(trade.entry_price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {trade.exit_price ? formatCurrency(trade.exit_price) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {trade.quantity}
                    </td>
                    <td
                      className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                        trade.profit_loss && trade.profit_loss >= 0
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}
                    >
                      {trade.profit_loss
                        ? formatCurrency(trade.profit_loss)
                        : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant={trade.is_open ? 'info' : 'success'}>
                        {trade.is_open ? 'Open' : 'Closed'}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Recent Orders */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Orders</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Side
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {orders.slice(0, 10).map((order) => (
                  <tr key={order.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(order.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant={order.side === 'buy' ? 'success' : 'danger'}>
                        {order.side.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {order.order_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {order.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {order.price ? formatCurrency(order.price) : 'Market'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge
                        variant={
                          order.status === 'filled'
                            ? 'success'
                            : order.status === 'cancelled'
                            ? 'danger'
                            : 'info'
                        }
                      >
                        {order.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}
