import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useNavigation } from '@react-navigation/native';

import { useTheme } from '../../contexts/ThemeContext';
import { api } from '../../services/api';

const { width } = Dimensions.get('window');

const DashboardScreen = () => {
  const { theme } = useTheme();
  const navigation = useNavigation<any>();

  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    total_bots: 0,
    running_bots: 0,
    total_pnl: 0,
    total_capital: 0,
    today_trades: 0,
    win_rate: 0,
  });

  const [recentBots, setRecentBots] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [statsRes, botsRes] = await Promise.all([
        api.bots.getStats(),
        api.bots.getAll(),
      ]);

      setStats(statsRes.data);
      setRecentBots(botsRes.data.slice(0, 5));
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        data: [120, 185, 150, 220, 195, 240, 280],
      },
    ],
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      refreshControl={
        <RefreshControl refreshing={loading} onRefresh={fetchDashboardData} />
      }
    >
      {/* Header Stats */}
      <View style={styles.statsGrid}>
        <View style={[styles.statCard, { backgroundColor: theme.colors.card }]}>
          <Icon name="robot" size={32} color={theme.colors.primary} />
          <Text style={[styles.statValue, { color: theme.colors.text }]}>
            {stats.running_bots}/{stats.total_bots}
          </Text>
          <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
            Active Bots
          </Text>
        </View>

        <View style={[styles.statCard, { backgroundColor: theme.colors.card }]}>
          <Icon
            name="trending-up"
            size={32}
            color={stats.total_pnl >= 0 ? theme.colors.success : theme.colors.error}
          />
          <Text
            style={[
              styles.statValue,
              {
                color: stats.total_pnl >= 0 ? theme.colors.success : theme.colors.error,
              },
            ]}
          >
            ${stats.total_pnl.toFixed(2)}
          </Text>
          <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
            Total P&L
          </Text>
        </View>
      </View>

      <View style={styles.statsGrid}>
        <View style={[styles.statCard, { backgroundColor: theme.colors.card }]}>
          <Icon name="chart-line" size={32} color={theme.colors.info} />
          <Text style={[styles.statValue, { color: theme.colors.text }]}>
            {stats.win_rate.toFixed(1)}%
          </Text>
          <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
            Win Rate
          </Text>
        </View>

        <View style={[styles.statCard, { backgroundColor: theme.colors.card }]}>
          <Icon name="swap-horizontal" size={32} color={theme.colors.warning} />
          <Text style={[styles.statValue, { color: theme.colors.text }]}>
            {stats.today_trades}
          </Text>
          <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
            Today's Trades
          </Text>
        </View>
      </View>

      {/* Performance Chart */}
      <View style={[styles.chartCard, { backgroundColor: theme.colors.card }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          Weekly Performance
        </Text>
        <LineChart
          data={chartData}
          width={width - 48}
          height={220}
          chartConfig={{
            backgroundColor: theme.colors.card,
            backgroundGradientFrom: theme.colors.card,
            backgroundGradientTo: theme.colors.card,
            decimalPlaces: 0,
            color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
            labelColor: (opacity = 1) =>
              theme.dark
                ? `rgba(249, 250, 251, ${opacity})`
                : `rgba(17, 24, 39, ${opacity})`,
            style: {
              borderRadius: 16,
            },
            propsForDots: {
              r: '6',
              strokeWidth: '2',
              stroke: theme.colors.primary,
            },
          }}
          bezier
          style={styles.chart}
        />
      </View>

      {/* Recent Bots */}
      <View style={[styles.section, { backgroundColor: theme.colors.card }]}>
        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Active Bots
          </Text>
          <TouchableOpacity onPress={() => navigation.navigate('Bots')}>
            <Text style={[styles.seeAllText, { color: theme.colors.primary }]}>
              See All
            </Text>
          </TouchableOpacity>
        </View>

        {recentBots.map((bot: any) => (
          <TouchableOpacity
            key={bot.id}
            style={[styles.botItem, { borderBottomColor: theme.colors.border }]}
            onPress={() => navigation.navigate('BotDetail', { botId: bot.id })}
          >
            <View style={styles.botInfo}>
              <View
                style={[
                  styles.statusDot,
                  {
                    backgroundColor:
                      bot.status === 'running' ? theme.colors.success : theme.colors.textSecondary,
                  },
                ]}
              />
              <View style={styles.botDetails}>
                <Text style={[styles.botName, { color: theme.colors.text }]}>
                  {bot.name}
                </Text>
                <Text style={[styles.botSymbol, { color: theme.colors.textSecondary }]}>
                  {bot.symbol} • {bot.exchange}
                </Text>
              </View>
            </View>
            <View style={styles.botStats}>
              <Text
                style={[
                  styles.botPnl,
                  { color: bot.pnl >= 0 ? theme.colors.success : theme.colors.error },
                ]}
              >
                {bot.pnl >= 0 ? '+' : ''}${bot.pnl.toFixed(2)}
              </Text>
              <Text style={[styles.botPercent, { color: theme.colors.textSecondary }]}>
                {bot.pnl_percent >= 0 ? '+' : ''}
                {bot.pnl_percent.toFixed(2)}%
              </Text>
            </View>
          </TouchableOpacity>
        ))}
      </View>

      {/* Quick Actions */}
      <View style={styles.actionsGrid}>
        <TouchableOpacity
          style={[styles.actionCard, { backgroundColor: theme.colors.primary }]}
          onPress={() => navigation.navigate('CreateBot')}
        >
          <Icon name="plus-circle" size={32} color="#FFFFFF" />
          <Text style={styles.actionText}>New Bot</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionCard, { backgroundColor: theme.colors.info }]}
          onPress={() => navigation.navigate('Marketplace')}
        >
          <Icon name="store" size={32} color="#FFFFFF" />
          <Text style={styles.actionText}>Marketplace</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  statsGrid: {
    flexDirection: 'row',
    padding: 12,
    gap: 12,
  },
  statCard: {
    flex: 1,
    padding: 20,
    borderRadius: 16,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    marginTop: 4,
  },
  chartCard: {
    margin: 12,
    padding: 16,
    borderRadius: 16,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  section: {
    margin: 12,
    padding: 16,
    borderRadius: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  seeAllText: {
    fontSize: 14,
    fontWeight: '600',
  },
  botItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  botInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 12,
  },
  botDetails: {
    flex: 1,
  },
  botName: {
    fontSize: 16,
    fontWeight: '600',
  },
  botSymbol: {
    fontSize: 12,
    marginTop: 2,
  },
  botStats: {
    alignItems: 'flex-end',
  },
  botPnl: {
    fontSize: 16,
    fontWeight: '600',
  },
  botPercent: {
    fontSize: 12,
    marginTop: 2,
  },
  actionsGrid: {
    flexDirection: 'row',
    padding: 12,
    gap: 12,
    marginBottom: 24,
  },
  actionCard: {
    flex: 1,
    padding: 20,
    borderRadius: 16,
    alignItems: 'center',
  },
  actionText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    marginTop: 8,
  },
});

export default DashboardScreen;
