import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { useNavigation } from '@react-navigation/native';
import api from '../../services/api';
import { showMessage } from 'react-native-flash-message';

interface Strategy {
  id: number;
  name: string;
  description: string;
  category: string;
  price: number;
  rating: number;
  downloads: number;
  author_name: string;
}

const MarketplaceScreen = () => {
  const { theme } = useTheme();
  const navigation = useNavigation();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<'all' | 'free' | 'paid' | 'trending'>('all');

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      const response = await api.get('/marketplace/search');
      setStrategies(response.data);
    } catch (error: any) {
      showMessage({
        message: 'Failed to load strategies',
        type: 'danger',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchStrategies();
  };

  const filteredStrategies = strategies.filter((strategy) => {
    // Search filter
    const matchesSearch =
      strategy.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      strategy.description.toLowerCase().includes(searchQuery.toLowerCase());

    // Category filter
    let matchesFilter = true;
    if (filter === 'free') matchesFilter = strategy.price === 0;
    if (filter === 'paid') matchesFilter = strategy.price > 0;
    if (filter === 'trending') matchesFilter = strategy.downloads > 100;

    return matchesSearch && matchesFilter;
  });

  const renderStrategy = ({ item }: { item: Strategy }) => (
    <TouchableOpacity
      style={[styles.strategyCard, { backgroundColor: theme.colors.surface }]}
      onPress={() =>
        navigation.navigate('StrategyDetail' as never, { strategyId: item.id } as never)
      }
    >
      <View style={styles.strategyHeader}>
        <View style={styles.strategyHeaderLeft}>
          <Text style={[styles.strategyName, { color: theme.colors.text }]}>
            {item.name}
          </Text>
          <Text style={[styles.authorName, { color: theme.colors.textSecondary }]}>
            by {item.author_name}
          </Text>
        </View>
        <View style={styles.strategyHeaderRight}>
          {item.price === 0 ? (
            <Text style={[styles.freeTag, { color: '#10B981' }]}>FREE</Text>
          ) : (
            <Text style={[styles.price, { color: theme.colors.primary }]}>
              ${item.price.toFixed(2)}
            </Text>
          )}
        </View>
      </View>

      <Text style={[styles.description, { color: theme.colors.textSecondary }]} numberOfLines={2}>
        {item.description}
      </Text>

      <View style={[styles.categoryBadge, { backgroundColor: theme.colors.background }]}>
        <Text style={[styles.categoryText, { color: theme.colors.text }]}>
          {item.category}
        </Text>
      </View>

      <View style={styles.strategyFooter}>
        <View style={styles.ratingContainer}>
          <Text style={styles.starIcon}>⭐</Text>
          <Text style={[styles.rating, { color: theme.colors.text }]}>
            {item.rating.toFixed(1)}
          </Text>
        </View>
        <Text style={[styles.downloads, { color: theme.colors.textSecondary }]}>
          {item.downloads} downloads
        </Text>
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
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <TextInput
          style={[
            styles.searchInput,
            {
              backgroundColor: theme.colors.surface,
              color: theme.colors.text,
            },
          ]}
          placeholder="Search strategies..."
          placeholderTextColor={theme.colors.textSecondary}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      {/* Filter Tabs */}
      <View style={styles.filterContainer}>
        <TouchableOpacity
          style={[
            styles.filterTab,
            filter === 'all' && { backgroundColor: theme.colors.primary },
          ]}
          onPress={() => setFilter('all')}
        >
          <Text
            style={[
              styles.filterText,
              { color: filter === 'all' ? '#FFFFFF' : theme.colors.textSecondary },
            ]}
          >
            All
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.filterTab,
            filter === 'trending' && { backgroundColor: theme.colors.primary },
          ]}
          onPress={() => setFilter('trending')}
        >
          <Text
            style={[
              styles.filterText,
              { color: filter === 'trending' ? '#FFFFFF' : theme.colors.textSecondary },
            ]}
          >
            🔥 Trending
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.filterTab,
            filter === 'free' && { backgroundColor: theme.colors.primary },
          ]}
          onPress={() => setFilter('free')}
        >
          <Text
            style={[
              styles.filterText,
              { color: filter === 'free' ? '#FFFFFF' : theme.colors.textSecondary },
            ]}
          >
            Free
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.filterTab,
            filter === 'paid' && { backgroundColor: theme.colors.primary },
          ]}
          onPress={() => setFilter('paid')}
        >
          <Text
            style={[
              styles.filterText,
              { color: filter === 'paid' ? '#FFFFFF' : theme.colors.textSecondary },
            ]}
          >
            Paid
          </Text>
        </TouchableOpacity>
      </View>

      {filteredStrategies.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>🛒</Text>
          <Text style={[styles.emptyText, { color: theme.colors.text }]}>
            No strategies found
          </Text>
          <Text style={[styles.emptySubtext, { color: theme.colors.textSecondary }]}>
            Try adjusting your search or filters
          </Text>
        </View>
      ) : (
        <FlatList
          data={filteredStrategies}
          renderItem={renderStrategy}
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
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  searchContainer: {
    padding: 16,
  },
  searchInput: {
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
  },
  filterContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingBottom: 16,
    gap: 8,
  },
  filterTab: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  filterText: {
    fontSize: 14,
    fontWeight: '600',
  },
  listContent: {
    padding: 16,
  },
  strategyCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  strategyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  strategyHeaderLeft: {
    flex: 1,
  },
  strategyName: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 4,
  },
  authorName: {
    fontSize: 14,
  },
  strategyHeaderRight: {
    marginLeft: 12,
  },
  freeTag: {
    fontSize: 14,
    fontWeight: '700',
  },
  price: {
    fontSize: 18,
    fontWeight: '700',
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  categoryBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    marginBottom: 12,
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '600',
  },
  strategyFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  starIcon: {
    fontSize: 16,
  },
  rating: {
    fontSize: 14,
    fontWeight: '600',
  },
  downloads: {
    fontSize: 12,
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
  },
});

export default MarketplaceScreen;
