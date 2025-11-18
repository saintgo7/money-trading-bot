import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import { showMessage } from 'react-native-flash-message';

interface UserProfile {
  id: number;
  email: string;
  username: string;
  created_at: string;
  subscription_tier: string;
}

interface UserStats {
  total_bots: number;
  active_bots: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  total_pnl: number;
  win_rate: number;
  avg_profit_per_trade: number;
  total_capital: number;
  roi: number;
}

const ProfileScreen = () => {
  const { theme } = useTheme();
  const { user } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchProfileData();
  }, []);

  const fetchProfileData = async () => {
    try {
      const [profileRes, statsRes] = await Promise.all([
        api.get('/users/me'),
        api.get('/bots/stats'),
      ]);
      setProfile(profileRes.data);
      setStats(statsRes.data);
    } catch (error: any) {
      showMessage({
        message: 'Failed to load profile data',
        type: 'danger',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchProfileData();
  };

  const handleEditProfile = () => {
    Alert.alert('Edit Profile', 'Profile editing feature coming soon');
  };

  const getTierBadgeColor = (tier: string) => {
    switch (tier.toLowerCase()) {
      case 'free':
        return '#6B7280';
      case 'basic':
        return '#3B82F6';
      case 'pro':
        return '#8B5CF6';
      case 'enterprise':
        return '#F59E0B';
      default:
        return theme.colors.primary;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'long',
      year: 'numeric',
    });
  };

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  if (!profile || !stats) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <Text style={[styles.errorText, { color: theme.colors.text }]}>
          Failed to load profile
        </Text>
      </View>
    );
  }

  const tierColor = getTierBadgeColor(profile.subscription_tier);

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor={theme.colors.primary}
        />
      }
    >
      {/* Profile Header */}
      <View style={[styles.header, { backgroundColor: theme.colors.surface }]}>
        <View style={[styles.avatar, { backgroundColor: theme.colors.primary }]}>
          <Text style={styles.avatarText}>
            {profile.username?.charAt(0).toUpperCase() || 'U'}
          </Text>
        </View>
        <Text style={[styles.username, { color: theme.colors.text }]}>
          {profile.username || 'User'}
        </Text>
        <Text style={[styles.email, { color: theme.colors.textSecondary }]}>
          {profile.email}
        </Text>
        <View style={[styles.tierBadge, { backgroundColor: tierColor }]}>
          <Text style={styles.tierText}>
            {profile.subscription_tier.toUpperCase()}
          </Text>
        </View>
        <Text style={[styles.memberSince, { color: theme.colors.textSecondary }]}>
          Member since {formatDate(profile.created_at)}
        </Text>
        <TouchableOpacity
          style={[styles.editButton, { borderColor: theme.colors.border }]}
          onPress={handleEditProfile}
        >
          <Text style={[styles.editButtonText, { color: theme.colors.text }]}>
            Edit Profile
          </Text>
        </TouchableOpacity>
      </View>

      {/* Trading Statistics */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          Trading Statistics
        </Text>

        <View style={styles.statsGrid}>
          <StatCard
            label="Total Bots"
            value={stats.total_bots.toString()}
            icon="🤖"
            backgroundColor={theme.colors.surface}
            textColor={theme.colors.text}
            secondaryColor={theme.colors.textSecondary}
          />
          <StatCard
            label="Active Bots"
            value={stats.active_bots.toString()}
            icon="▶️"
            backgroundColor={theme.colors.surface}
            textColor={theme.colors.text}
            secondaryColor={theme.colors.textSecondary}
          />
          <StatCard
            label="Total Trades"
            value={stats.total_trades.toString()}
            icon="📊"
            backgroundColor={theme.colors.surface}
            textColor={theme.colors.text}
            secondaryColor={theme.colors.textSecondary}
          />
          <StatCard
            label="Win Rate"
            value={`${stats.win_rate.toFixed(1)}%`}
            icon="🎯"
            backgroundColor={theme.colors.surface}
            textColor={theme.colors.text}
            secondaryColor={theme.colors.textSecondary}
          />
        </View>
      </View>

      {/* Performance Metrics */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          Performance
        </Text>

        <View style={[styles.card, { backgroundColor: theme.colors.surface }]}>
          <PerformanceRow
            label="Total P&L"
            value={`$${stats.total_pnl.toFixed(2)}`}
            isPositive={stats.total_pnl >= 0}
            textColor={theme.colors.text}
          />
          <PerformanceRow
            label="Total Capital"
            value={`$${stats.total_capital.toFixed(2)}`}
            textColor={theme.colors.text}
          />
          <PerformanceRow
            label="ROI"
            value={`${stats.roi.toFixed(2)}%`}
            isPositive={stats.roi >= 0}
            textColor={theme.colors.text}
          />
          <PerformanceRow
            label="Avg Profit/Trade"
            value={`$${stats.avg_profit_per_trade.toFixed(2)}`}
            isPositive={stats.avg_profit_per_trade >= 0}
            textColor={theme.colors.text}
            noBorder
          />
        </View>
      </View>

      {/* Trade Breakdown */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          Trade Breakdown
        </Text>

        <View style={[styles.card, { backgroundColor: theme.colors.surface }]}>
          <View style={styles.tradeBreakdown}>
            <View style={styles.tradeBreakdownItem}>
              <View style={styles.tradeBreakdownHeader}>
                <Text style={styles.tradeBreakdownIcon}>✅</Text>
                <Text style={[styles.tradeBreakdownLabel, { color: theme.colors.text }]}>
                  Winning Trades
                </Text>
              </View>
              <Text style={[styles.tradeBreakdownValue, { color: '#10B981' }]}>
                {stats.winning_trades}
              </Text>
            </View>

            <View style={[styles.divider, { backgroundColor: theme.colors.border }]} />

            <View style={styles.tradeBreakdownItem}>
              <View style={styles.tradeBreakdownHeader}>
                <Text style={styles.tradeBreakdownIcon}>❌</Text>
                <Text style={[styles.tradeBreakdownLabel, { color: theme.colors.text }]}>
                  Losing Trades
                </Text>
              </View>
              <Text style={[styles.tradeBreakdownValue, { color: '#EF4444' }]}>
                {stats.losing_trades}
              </Text>
            </View>
          </View>

          {/* Win Rate Progress Bar */}
          <View style={styles.progressContainer}>
            <Text style={[styles.progressLabel, { color: theme.colors.textSecondary }]}>
              Win Rate: {stats.win_rate.toFixed(1)}%
            </Text>
            <View style={[styles.progressBar, { backgroundColor: theme.colors.border }]}>
              <View
                style={[
                  styles.progressFill,
                  {
                    width: `${Math.min(stats.win_rate, 100)}%`,
                    backgroundColor: stats.win_rate >= 50 ? '#10B981' : '#F59E0B',
                  },
                ]}
              />
            </View>
          </View>
        </View>
      </View>

      {/* Account Actions */}
      <View style={styles.section}>
        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: theme.colors.surface }]}
          onPress={() => Alert.alert('Trade History', 'Opening trade history...')}
        >
          <Text style={[styles.actionButtonText, { color: theme.colors.text }]}>
            📜 View Trade History
          </Text>
          <Text style={styles.actionButtonIcon}>›</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: theme.colors.surface }]}
          onPress={() => Alert.alert('Export Data', 'Export data feature coming soon')}
        >
          <Text style={[styles.actionButtonText, { color: theme.colors.text }]}>
            💾 Export Trading Data
          </Text>
          <Text style={styles.actionButtonIcon}>›</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: theme.colors.surface }]}
          onPress={() => Alert.alert('Achievements', 'Achievements feature coming soon')}
        >
          <Text style={[styles.actionButtonText, { color: theme.colors.text }]}>
            🏆 Achievements
          </Text>
          <Text style={styles.actionButtonIcon}>›</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

interface StatCardProps {
  label: string;
  value: string;
  icon: string;
  backgroundColor: string;
  textColor: string;
  secondaryColor: string;
}

const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon,
  backgroundColor,
  textColor,
  secondaryColor,
}) => (
  <View style={[styles.statCard, { backgroundColor }]}>
    <Text style={styles.statIcon}>{icon}</Text>
    <Text style={[styles.statValue, { color: textColor }]}>{value}</Text>
    <Text style={[styles.statLabel, { color: secondaryColor }]}>{label}</Text>
  </View>
);

interface PerformanceRowProps {
  label: string;
  value: string;
  isPositive?: boolean;
  textColor: string;
  noBorder?: boolean;
}

const PerformanceRow: React.FC<PerformanceRowProps> = ({
  label,
  value,
  isPositive,
  textColor,
  noBorder = false,
}) => (
  <View style={[styles.performanceRow, noBorder && styles.noBorder]}>
    <Text style={[styles.performanceLabel, { color: textColor }]}>{label}</Text>
    <Text
      style={[
        styles.performanceValue,
        {
          color:
            isPositive !== undefined
              ? isPositive
                ? '#10B981'
                : '#EF4444'
              : textColor,
        },
      ]}
    >
      {value}
    </Text>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 32,
  },
  header: {
    padding: 24,
    alignItems: 'center',
    marginBottom: 24,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatarText: {
    fontSize: 32,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  username: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  email: {
    fontSize: 14,
    marginBottom: 12,
  },
  tierBadge: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 16,
    marginBottom: 8,
  },
  tierText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  memberSince: {
    fontSize: 12,
    marginBottom: 16,
  },
  editButton: {
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
  },
  editButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  statCard: {
    width: '48%',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  statIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
  },
  card: {
    borderRadius: 12,
    padding: 16,
  },
  performanceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  noBorder: {
    borderBottomWidth: 0,
  },
  performanceLabel: {
    fontSize: 16,
  },
  performanceValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  tradeBreakdown: {
    marginBottom: 16,
  },
  tradeBreakdownItem: {
    paddingVertical: 12,
  },
  tradeBreakdownHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  tradeBreakdownIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  tradeBreakdownLabel: {
    fontSize: 16,
  },
  tradeBreakdownValue: {
    fontSize: 28,
    fontWeight: '700',
  },
  divider: {
    height: 1,
    marginVertical: 8,
  },
  progressContainer: {
    marginTop: 8,
  },
  progressLabel: {
    fontSize: 14,
    marginBottom: 8,
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  actionButton: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  actionButtonIcon: {
    fontSize: 24,
    color: '#9CA3AF',
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
  },
});

export default ProfileScreen;
