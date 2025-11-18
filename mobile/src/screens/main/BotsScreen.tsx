import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { useNavigation } from '@react-navigation/native';
import api from '../../services/api';
import { showMessage } from 'react-native-flash-message';

interface Bot {
  id: number;
  name: string;
  exchange: string;
  symbol: string;
  strategy: string;
  status: string;
  total_pnl: number;
  capital: number;
  created_at: string;
}

const BotsScreen = () => {
  const { theme } = useTheme();
  const navigation = useNavigation();
  const [bots, setBots] = useState<Bot[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<'all' | 'running' | 'stopped'>('all');

  useEffect(() => {
    fetchBots();
  }, []);

  const fetchBots = async () => {
    try {
      const response = await api.get('/bots');
      setBots(response.data);
    } catch (error: any) {
      showMessage({
        message: 'Failed to load bots',
        type: 'danger',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchBots();
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
        return '#10B981';
      case 'stopped':
        return '#6B7280';
      case 'error':
        return '#EF4444';
      default:
        return theme.colors.textSecondary;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
        return '▶️';
      case 'stopped':
        return '⏸️';
      case 'error':
        return '⚠️';
      default:
        return '⏹️';
    }
  };

  const filteredBots = bots.filter((bot) => {
    if (filter === 'all') return true;
    return bot.status.toLowerCase() === filter;
  });

  const renderBot = ({ item }: { item: Bot }) => (
    <TouchableOpacity
      style={[styles.botCard, { backgroundColor: theme.colors.surface }]}
      onPress={() => navigation.navigate('BotDetail' as never, { botId: item.id } as never)}
    >
      <View style={styles.botHeader}>
        <View style={styles.botHeaderLeft}>
          <Text style={[styles.botName, { color: theme.colors.text }]}>
            {item.name}
          </Text>
          <Text style={[styles.botSymbol, { color: theme.colors.textSecondary }]}>
            {item.symbol} • {item.exchange}
          </Text>
        </View>
        <View
          style={[
            styles.statusBadge,
            { backgroundColor: getStatusColor(item.status) + '20' },
          ]}
        >
          <Text style={styles.statusIcon}>{getStatusIcon(item.status)}</Text>
          <Text
            style={[
              styles.statusText,
              { color: getStatusColor(item.status) },
            ]}
          >
            {item.status}
          </Text>
        </View>
      </View>

      <View style={styles.botStats}>
        <View style={styles.statItem}>
          <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
            P&L
          </Text>
          <Text
            style={[
              styles.statValue,
              {
                color: item.total_pnl >= 0 ? '#10B981' : '#EF4444',
              },
            ]}
          >
            ${item.total_pnl.toFixed(2)}
          </Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
            Capital
          </Text>
          <Text style={[styles.statValue, { color: theme.colors.text }]}>
            ${item.capital.toFixed(2)}
          </Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
            Strategy
          </Text>
          <Text style={[styles.statValue, { color: theme.colors.text }]}>
            {item.strategy}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Filter Tabs */}
      <View style={styles.filterContainer}>
        <TouchableOpacity
          style={[
            styles.filterTab,
            filter === 'all' && {
              backgroundColor: theme.colors.primary,
            },
          ]}
          onPress={() => setFilter('all')}
        >
          <Text
            style={[
              styles.filterText,
              {
                color:
                  filter === 'all'
                    ? '#FFFFFF'
                    : theme.colors.textSecondary,
              },
            ]}
          >
            All ({bots.length})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.filterTab,
            filter === 'running' && {
              backgroundColor: theme.colors.primary,
            },
          ]}
          onPress={() => setFilter('running')}
        >
          <Text
            style={[
              styles.filterText,
              {
                color:
                  filter === 'running'
                    ? '#FFFFFF'
                    : theme.colors.textSecondary,
              },
            ]}
          >
            Running (
            {bots.filter((b) => b.status.toLowerCase() === 'running').length})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.filterTab,
            filter === 'stopped' && {
              backgroundColor: theme.colors.primary,
            },
          ]}
          onPress={() => setFilter('stopped')}
        >
          <Text
            style={[
              styles.filterText,
              {
                color:
                  filter === 'stopped'
                    ? '#FFFFFF'
                    : theme.colors.textSecondary,
              },
            ]}
          >
            Stopped (
            {bots.filter((b) => b.status.toLowerCase() === 'stopped').length})
          </Text>
        </TouchableOpacity>
      </View>

      {filteredBots.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>🤖</Text>
          <Text style={[styles.emptyText, { color: theme.colors.text }]}>
            No bots yet
          </Text>
          <Text style={[styles.emptySubtext, { color: theme.colors.textSecondary }]}>
            Create your first trading bot to get started
          </Text>
          <TouchableOpacity
            style={[styles.createButton, { backgroundColor: theme.colors.primary }]}
            onPress={() => navigation.navigate('CreateBot' as never)}
          >
            <Text style={styles.createButtonText}>Create Bot</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={filteredBots}
          renderItem={renderBot}
          keyExtractor={(item) => item.id.toString()}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={theme.colors.primary}
            />
          }
          contentContainerStyle={styles.listContent}
        />
      )}

      {/* Floating Action Button */}
      {bots.length > 0 && (
        <TouchableOpacity
          style={[styles.fab, { backgroundColor: theme.colors.primary }]}
          onPress={() => navigation.navigate('CreateBot' as never)}
        >
          <Text style={styles.fabIcon}>+</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  filterContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 8,
  },
  filterTab: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  filterText: {
    fontSize: 14,
    fontWeight: '600',
  },
  listContent: {
    padding: 16,
  },
  botCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  botHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  botHeaderLeft: {
    flex: 1,
  },
  botName: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 4,
  },
  botSymbol: {
    fontSize: 14,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  statusIcon: {
    fontSize: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  botStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statItem: {
    flex: 1,
  },
  statLabel: {
    fontSize: 12,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '700',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 24,
  },
  createButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
  },
  createButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 24,
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
  },
  fabIcon: {
    color: '#FFFFFF',
    fontSize: 32,
    fontWeight: '300',
  },
});

export default BotsScreen;
