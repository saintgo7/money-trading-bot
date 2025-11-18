'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { botsAPI, strategiesAPI, marketAPI } from '@/lib/api';
import { Input, Select, Button, Card } from '@/components/ui';
import DashboardLayout from '@/components/DashboardLayout';

export default function NewBot() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [exchanges, setExchanges] = useState<any[]>([]);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    exchange: 'binance',
    trading_pair: 'BTC/USDT',
    initial_capital: 10000,
    max_position_size: 10.0,
    stop_loss_percentage: 5.0,
    take_profit_percentage: 10.0,
    strategy_id: null as number | null,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [exchangesRes, strategiesRes] = await Promise.all([
        marketAPI.listExchanges(),
        strategiesAPI.list(),
      ]);
      setExchanges(exchangesRes.data.exchanges);
      setStrategies(strategiesRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await botsAPI.create(formData);
      router.push(`/dashboard/bots/${response.data.id}`);
    } catch (error: any) {
      console.error('Failed to create bot:', error);
      alert(error.response?.data?.detail || 'Failed to create bot');
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Create New Trading Bot</h1>

        <Card>
          <form onSubmit={handleSubmit} className="space-y-6">
            <Input
              label="Bot Name"
              type="text"
              required
              placeholder="My Trading Bot"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                rows={3}
                placeholder="Optional description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <Select
              label="Exchange"
              required
              options={exchanges.map((ex) => ({
                value: ex.name,
                label: ex.display_name,
              }))}
              value={formData.exchange}
              onChange={(e) => setFormData({ ...formData, exchange: e.target.value })}
            />

            <Input
              label="Trading Pair"
              type="text"
              required
              placeholder="BTC/USDT"
              value={formData.trading_pair}
              onChange={(e) => setFormData({ ...formData, trading_pair: e.target.value })}
            />

            <Input
              label="Initial Capital (USD)"
              type="number"
              required
              min="100"
              step="100"
              value={formData.initial_capital}
              onChange={(e) =>
                setFormData({ ...formData, initial_capital: parseFloat(e.target.value) })
              }
            />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label="Max Position Size (%)"
                type="number"
                required
                min="1"
                max="100"
                step="0.1"
                value={formData.max_position_size}
                onChange={(e) =>
                  setFormData({ ...formData, max_position_size: parseFloat(e.target.value) })
                }
              />

              <Input
                label="Stop Loss (%)"
                type="number"
                required
                min="0.1"
                max="50"
                step="0.1"
                value={formData.stop_loss_percentage}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    stop_loss_percentage: parseFloat(e.target.value),
                  })
                }
              />

              <Input
                label="Take Profit (%)"
                type="number"
                required
                min="0.1"
                max="100"
                step="0.1"
                value={formData.take_profit_percentage}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    take_profit_percentage: parseFloat(e.target.value),
                  })
                }
              />
            </div>

            <Select
              label="Strategy (Optional)"
              options={[
                { value: '', label: 'Default (Technical Analysis)' },
                ...strategies.map((s) => ({
                  value: s.id.toString(),
                  label: `${s.name} (${s.strategy_type})`,
                })),
              ]}
              value={formData.strategy_id?.toString() || ''}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  strategy_id: e.target.value ? parseInt(e.target.value) : null,
                })
              }
            />

            <div className="flex items-center justify-end space-x-4 pt-6">
              <Button
                type="button"
                variant="ghost"
                onClick={() => router.back()}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? 'Creating...' : 'Create Bot'}
              </Button>
            </div>
          </form>
        </Card>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="text-sm font-medium text-blue-900 mb-2">
            Tips for Creating a Bot
          </h3>
          <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
            <li>Start with a small initial capital to test your strategy</li>
            <li>Use stop-loss to limit potential losses</li>
            <li>Set realistic take-profit targets based on market volatility</li>
            <li>Monitor your bot regularly, especially in the first few days</li>
            <li>Consider using paper trading (testnet) first</li>
          </ul>
        </div>
      </div>
    </DashboardLayout>
  );
}
