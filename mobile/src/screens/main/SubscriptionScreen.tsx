import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import { showMessage } from 'react-native-flash-message';

interface SubscriptionPlan {
  id: number;
  tier: string;
  name: string;
  monthly_price: number;
  yearly_price: number;
  features: {
    max_bots: number;
    max_strategies: number;
    max_exchanges: number;
    api_rate_limit: number;
    support_level: string;
    additional_features: string[];
  };
}

interface UserSubscription {
  id: number;
  tier: string;
  status: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
}

const SubscriptionScreen = () => {
  const { theme } = useTheme();
  const { user } = useAuth();
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<UserSubscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [subscribing, setSubscing] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [plansRes, subRes] = await Promise.all([
        api.get('/subscriptions/plans'),
        api.get('/subscriptions/current'),
      ]);
      setPlans(plansRes.data);
      setCurrentSubscription(subRes.data);
    } catch (error: any) {
      showMessage({
        message: 'Failed to load subscription data',
        type: 'danger',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (tier: string) => {
    Alert.alert(
      'Confirm Subscription',
      `Subscribe to ${tier.charAt(0).toUpperCase() + tier.slice(1)} plan (${billingCycle})?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Subscribe',
          onPress: async () => {
            setSubscing(true);
            try {
              await api.post('/subscriptions/subscribe', {
                tier,
                billing_cycle: billingCycle,
              });
              showMessage({
                message: 'Subscription successful!',
                description: 'Your subscription is now active',
                type: 'success',
              });
              fetchData();
            } catch (error: any) {
              showMessage({
                message: 'Subscription failed',
                description: error.response?.data?.detail || 'Please try again',
                type: 'danger',
              });
            } finally {
              setSubscing(false);
            }
          },
        },
      ]
    );
  };

  const handleCancelSubscription = () => {
    Alert.alert(
      'Cancel Subscription',
      'Are you sure you want to cancel your subscription? You will retain access until the end of your billing period.',
      [
        { text: 'Keep Subscription', style: 'cancel' },
        {
          text: 'Cancel Subscription',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.post('/subscriptions/cancel');
              showMessage({
                message: 'Subscription cancelled',
                description: 'You will have access until the end of your billing period',
                type: 'success',
              });
              fetchData();
            } catch (error: any) {
              showMessage({
                message: 'Failed to cancel subscription',
                type: 'danger',
              });
            }
          },
        },
      ]
    );
  };

  const getTierColor = (tier: string) => {
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

  const isCurrentPlan = (tier: string) => {
    return currentSubscription?.tier.toLowerCase() === tier.toLowerCase();
  };

  const renderPlanCard = (plan: SubscriptionPlan) => {
    const price = billingCycle === 'monthly' ? plan.monthly_price : plan.yearly_price;
    const monthlySavings =
      billingCycle === 'yearly' ? plan.monthly_price - plan.yearly_price / 12 : 0;
    const isCurrent = isCurrentPlan(plan.tier);
    const tierColor = getTierColor(plan.tier);

    return (
      <View
        key={plan.id}
        style={[
          styles.planCard,
          {
            backgroundColor: theme.colors.surface,
            borderColor: isCurrent ? tierColor : theme.colors.border,
            borderWidth: isCurrent ? 2 : 1,
          },
        ]}
      >
        {isCurrent && (
          <View style={[styles.currentBadge, { backgroundColor: tierColor }]}>
            <Text style={styles.currentBadgeText}>Current Plan</Text>
          </View>
        )}

        <View style={styles.planHeader}>
          <Text style={[styles.planName, { color: tierColor }]}>{plan.name}</Text>
          {plan.tier.toLowerCase() === 'pro' && (
            <View style={[styles.popularBadge, { backgroundColor: tierColor }]}>
              <Text style={styles.popularText}>POPULAR</Text>
            </View>
          )}
        </View>

        <View style={styles.priceContainer}>
          <Text style={[styles.price, { color: theme.colors.text }]}>
            ${price.toFixed(0)}
          </Text>
          <Text style={[styles.pricePeriod, { color: theme.colors.textSecondary }]}>
            /{billingCycle === 'monthly' ? 'month' : 'year'}
          </Text>
        </View>

        {billingCycle === 'yearly' && monthlySavings > 0 && (
          <Text style={[styles.savings, { color: '#10B981' }]}>
            Save ${monthlySavings.toFixed(0)}/month
          </Text>
        )}

        <View style={styles.featuresContainer}>
          <Feature
            text={`${plan.features.max_bots} active bots`}
            color={theme.colors.text}
          />
          <Feature
            text={`${plan.features.max_strategies} strategies`}
            color={theme.colors.text}
          />
          <Feature
            text={`${plan.features.max_exchanges} exchanges`}
            color={theme.colors.text}
          />
          <Feature
            text={`${plan.features.api_rate_limit.toLocaleString()} API calls/min`}
            color={theme.colors.text}
          />
          <Feature
            text={`${plan.features.support_level} support`}
            color={theme.colors.text}
          />
          {plan.features.additional_features.map((feature, index) => (
            <Feature key={index} text={feature} color={theme.colors.text} />
          ))}
        </View>

        {!isCurrent && (
          <TouchableOpacity
            style={[
              styles.subscribeButton,
              {
                backgroundColor: plan.tier === 'free' ? theme.colors.border : tierColor,
              },
            ]}
            onPress={() => handleSubscribe(plan.tier)}
            disabled={subscribing || plan.tier === 'free'}
          >
            <Text
              style={[
                styles.subscribeButtonText,
                { color: plan.tier === 'free' ? theme.colors.textSecondary : '#FFFFFF' },
              ]}
            >
              {plan.tier === 'free' ? 'Free Plan' : 'Subscribe'}
            </Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.scrollContent}
    >
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.colors.text }]}>
          Choose Your Plan
        </Text>
        <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
          Upgrade anytime. Cancel anytime. No hidden fees.
        </Text>
      </View>

      {/* Billing Cycle Toggle */}
      <View style={styles.billingToggle}>
        <TouchableOpacity
          style={[
            styles.toggleButton,
            billingCycle === 'monthly' && {
              backgroundColor: theme.colors.primary,
            },
          ]}
          onPress={() => setBillingCycle('monthly')}
        >
          <Text
            style={[
              styles.toggleText,
              {
                color:
                  billingCycle === 'monthly'
                    ? '#FFFFFF'
                    : theme.colors.textSecondary,
              },
            ]}
          >
            Monthly
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.toggleButton,
            billingCycle === 'yearly' && {
              backgroundColor: theme.colors.primary,
            },
          ]}
          onPress={() => setBillingCycle('yearly')}
        >
          <Text
            style={[
              styles.toggleText,
              {
                color:
                  billingCycle === 'yearly'
                    ? '#FFFFFF'
                    : theme.colors.textSecondary,
              },
            ]}
          >
            Yearly (Save 17%)
          </Text>
        </TouchableOpacity>
      </View>

      {/* Subscription Plans */}
      {plans.map((plan) => renderPlanCard(plan))}

      {/* Current Subscription Info */}
      {currentSubscription && currentSubscription.tier !== 'free' && (
        <View
          style={[
            styles.currentSubInfo,
            { backgroundColor: theme.colors.surface, borderColor: theme.colors.border },
          ]}
        >
          <Text style={[styles.currentSubTitle, { color: theme.colors.text }]}>
            Current Subscription
          </Text>
          <Text style={[styles.currentSubDetail, { color: theme.colors.textSecondary }]}>
            Status: {currentSubscription.status}
          </Text>
          <Text style={[styles.currentSubDetail, { color: theme.colors.textSecondary }]}>
            Renews: {new Date(currentSubscription.current_period_end).toLocaleDateString()}
          </Text>
          {!currentSubscription.cancel_at_period_end && (
            <TouchableOpacity
              style={[styles.cancelButton, { borderColor: '#EF4444' }]}
              onPress={handleCancelSubscription}
            >
              <Text style={[styles.cancelButtonText, { color: '#EF4444' }]}>
                Cancel Subscription
              </Text>
            </TouchableOpacity>
          )}
          {currentSubscription.cancel_at_period_end && (
            <Text style={[styles.cancelledText, { color: '#EF4444' }]}>
              Subscription will end on{' '}
              {new Date(currentSubscription.current_period_end).toLocaleDateString()}
            </Text>
          )}
        </View>
      )}
    </ScrollView>
  );
};

const Feature: React.FC<{ text: string; color: string }> = ({ text, color }) => (
  <View style={styles.featureRow}>
    <Text style={styles.checkmark}>✓</Text>
    <Text style={[styles.featureText, { color }]}>{text}</Text>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  header: {
    marginBottom: 24,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
  },
  billingToggle: {
    flexDirection: 'row',
    marginBottom: 24,
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    padding: 4,
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  toggleText: {
    fontSize: 16,
    fontWeight: '600',
  },
  planCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    position: 'relative',
  },
  currentBadge: {
    position: 'absolute',
    top: -8,
    right: 16,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  currentBadgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  planHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  planName: {
    fontSize: 24,
    fontWeight: '700',
  },
  popularBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  popularText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
  },
  priceContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 4,
  },
  price: {
    fontSize: 40,
    fontWeight: '700',
  },
  pricePeriod: {
    fontSize: 16,
    marginLeft: 4,
  },
  savings: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 16,
  },
  featuresContainer: {
    marginBottom: 20,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  checkmark: {
    fontSize: 16,
    marginRight: 8,
    color: '#10B981',
  },
  featureText: {
    fontSize: 14,
  },
  subscribeButton: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  subscribeButtonText: {
    fontSize: 16,
    fontWeight: '700',
  },
  currentSubInfo: {
    borderRadius: 16,
    padding: 20,
    marginTop: 8,
    borderWidth: 1,
  },
  currentSubTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 12,
  },
  currentSubDetail: {
    fontSize: 14,
    marginBottom: 4,
  },
  cancelButton: {
    marginTop: 16,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  cancelledText: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 12,
  },
});

export default SubscriptionScreen;
