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
import api from '../../services/api';
import { showMessage } from 'react-native-flash-message';

interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  data?: any;
  read: boolean;
  created_at: string;
}

const NotificationsScreen = () => {
  const { theme } = useTheme();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const response = await api.get('/notifications');
      setNotifications(response.data);
    } catch (error: any) {
      showMessage({
        message: 'Failed to load notifications',
        description: error.response?.data?.detail || 'Network error',
        type: 'danger',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchNotifications();
  };

  const markAsRead = async (notificationId: number) => {
    try {
      await api.post(`/notifications/${notificationId}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
      );
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.post('/notifications/read-all');
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      showMessage({
        message: 'All notifications marked as read',
        type: 'success',
      });
    } catch (error: any) {
      showMessage({
        message: 'Failed to mark all as read',
        type: 'danger',
      });
    }
  };

  const deleteNotification = async (notificationId: number) => {
    try {
      await api.delete(`/notifications/${notificationId}`);
      setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
      showMessage({
        message: 'Notification deleted',
        type: 'success',
      });
    } catch (error: any) {
      showMessage({
        message: 'Failed to delete notification',
        type: 'danger',
      });
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'trade':
        return '💰';
      case 'bot_status':
        return '🤖';
      case 'alert':
        return '⚠️';
      case 'subscription':
        return '💳';
      case 'marketplace':
        return '🛒';
      default:
        return '🔔';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const renderNotification = ({ item }: { item: Notification }) => (
    <TouchableOpacity
      style={[
        styles.notificationCard,
        {
          backgroundColor: item.read
            ? theme.colors.surface
            : theme.colors.primary + '15',
          borderColor: theme.colors.border,
        },
      ]}
      onPress={() => !item.read && markAsRead(item.id)}
      onLongPress={() => deleteNotification(item.id)}
    >
      <View style={styles.notificationHeader}>
        <Text style={styles.icon}>{getNotificationIcon(item.type)}</Text>
        <View style={styles.notificationContent}>
          <View style={styles.notificationTitleRow}>
            <Text
              style={[
                styles.notificationTitle,
                { color: theme.colors.text },
                !item.read && styles.unreadTitle,
              ]}
            >
              {item.title}
            </Text>
            {!item.read && (
              <View
                style={[
                  styles.unreadDot,
                  { backgroundColor: theme.colors.primary },
                ]}
              />
            )}
          </View>
          <Text style={[styles.notificationMessage, { color: theme.colors.textSecondary }]}>
            {item.message}
          </Text>
          <Text style={[styles.notificationDate, { color: theme.colors.textSecondary }]}>
            {formatDate(item.created_at)}
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

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {notifications.length > 0 && unreadCount > 0 && (
        <View style={styles.header}>
          <Text style={[styles.headerText, { color: theme.colors.text }]}>
            {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
          </Text>
          <TouchableOpacity
            style={[styles.markAllButton, { backgroundColor: theme.colors.primary }]}
            onPress={markAllAsRead}
          >
            <Text style={styles.markAllButtonText}>Mark all as read</Text>
          </TouchableOpacity>
        </View>
      )}

      {notifications.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>🔔</Text>
          <Text style={[styles.emptyText, { color: theme.colors.text }]}>
            No notifications yet
          </Text>
          <Text style={[styles.emptySubtext, { color: theme.colors.textSecondary }]}>
            You'll receive notifications about trades, bot status, and alerts here
          </Text>
        </View>
      ) : (
        <FlatList
          data={notifications}
          renderItem={renderNotification}
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerText: {
    fontSize: 16,
    fontWeight: '600',
  },
  markAllButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  markAllButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  listContent: {
    padding: 16,
  },
  notificationCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
  },
  notificationHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  icon: {
    fontSize: 32,
    marginRight: 12,
  },
  notificationContent: {
    flex: 1,
  },
  notificationTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  notificationTitle: {
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
  },
  unreadTitle: {
    fontWeight: '700',
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginLeft: 8,
  },
  notificationMessage: {
    fontSize: 14,
    marginBottom: 4,
    lineHeight: 20,
  },
  notificationDate: {
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

export default NotificationsScreen;
