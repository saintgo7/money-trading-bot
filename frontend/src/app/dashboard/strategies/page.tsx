'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { strategiesAPI } from '@/lib/api';
import { Strategy } from '@/types';
import { Button, Card, Badge } from '@/components/ui';
import DashboardLayout from '@/components/DashboardLayout';

export default function Strategies() {
  const router = useRouter();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [publicStrategies, setPublicStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      const [userStrategies, pubStrategies] = await Promise.all([
        strategiesAPI.list(),
        strategiesAPI.listPublic(),
      ]);
      setStrategies(userStrategies.data);
      setPublicStrategies(pubStrategies.data);
    } catch (error) {
      console.error('Failed to fetch strategies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this strategy?')) return;

    try {
      await strategiesAPI.delete(id);
      fetchStrategies();
    } catch (error) {
      console.error('Failed to delete strategy:', error);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Trading Strategies</h1>
          <Button onClick={() => router.push('/dashboard/strategies/new')}>
            Create Strategy
          </Button>
        </div>

        {/* Your Strategies */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Strategies</h2>
          {strategies.length === 0 ? (
            <Card>
              <p className="text-gray-500 text-center py-8">
                No strategies yet. Create your first strategy!
              </p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {strategies.map((strategy) => (
                <Card key={strategy.id}>
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {strategy.name}
                      </h3>
                      <Badge variant="info">{strategy.strategy_type}</Badge>
                    </div>

                    {strategy.description && (
                      <p className="text-sm text-gray-600">{strategy.description}</p>
                    )}

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {strategy.win_rate && (
                        <div>
                          <p className="text-gray-500">Win Rate</p>
                          <p className="font-medium">{strategy.win_rate.toFixed(1)}%</p>
                        </div>
                      )}
                      {strategy.sharpe_ratio && (
                        <div>
                          <p className="text-gray-500">Sharpe Ratio</p>
                          <p className="font-medium">{strategy.sharpe_ratio.toFixed(2)}</p>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center space-x-2 pt-3">
                      <Button
                        size="sm"
                        onClick={() => router.push(`/dashboard/strategies/${strategy.id}`)}
                      >
                        View
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => router.push(`/dashboard/strategies/${strategy.id}/edit`)}
                      >
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => handleDelete(strategy.id)}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Public Strategies */}
        {publicStrategies.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Public Strategies
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {publicStrategies.map((strategy) => (
                <Card key={strategy.id}>
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {strategy.name}
                      </h3>
                      <Badge variant="success">Public</Badge>
                    </div>

                    {strategy.description && (
                      <p className="text-sm text-gray-600">{strategy.description}</p>
                    )}

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {strategy.win_rate && (
                        <div>
                          <p className="text-gray-500">Win Rate</p>
                          <p className="font-medium">{strategy.win_rate.toFixed(1)}%</p>
                        </div>
                      )}
                      {strategy.sharpe_ratio && (
                        <div>
                          <p className="text-gray-500">Sharpe Ratio</p>
                          <p className="font-medium">{strategy.sharpe_ratio.toFixed(2)}</p>
                        </div>
                      )}
                    </div>

                    <Button
                      size="sm"
                      onClick={() => router.push(`/dashboard/strategies/${strategy.id}`)}
                    >
                      View Details
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
