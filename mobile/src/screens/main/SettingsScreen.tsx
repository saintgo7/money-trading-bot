import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { showMessage } from 'react-native-flash-message';
import AsyncStorage from '@react-native-async-storage/async-storage';

const SettingsScreen = () => {
  const { theme, themeMode, setThemeMode } = useTheme();
  const { logout } = useAuth();

  // Notification settings
  const [pushNotifications, setPushNotifications] = useState(true);
  const [tradeAlerts, setTradeAlerts] = useState(true);
  const [botStatusAlerts, setBotStatusAlerts] = useState(true);
  const [priceAlerts, setPriceAlerts] = useState(true);
  const [marketingEmails, setMarketingEmails] = useState(false);

  // App settings
  const [biometricAuth, setBiometricAuth] = useState(false);
  const [autoLockEnabled, setAutoLockEnabled] = useState(false);

  const handleThemeChange = (mode: 'light' | 'dark' | 'auto') => {
    setThemeMode(mode);
    showMessage({
      message: 'Theme updated',
      description: `Switched to ${mode} mode`,
      type: 'success',
    });
  };

  const handleClearCache = async () => {
    Alert.alert(
      'Clear Cache',
      'This will clear all cached data. Are you sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              // Clear specific cache keys, preserve auth token
              const keys = await AsyncStorage.getAllKeys();
              const cacheKeys = keys.filter(
                (key) => !key.includes('auth_token') && !key.includes('theme')
              );
              await AsyncStorage.multiRemove(cacheKeys);
              showMessage({
                message: 'Cache cleared',
                type: 'success',
              });
            } catch (error) {
              showMessage({
                message: 'Failed to clear cache',
                type: 'danger',
              });
            }
          },
        },
      ]
    );
  };

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to logout?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Logout',
        style: 'destructive',
        onPress: () => {
          logout();
          showMessage({
            message: 'Logged out successfully',
            type: 'success',
          });
        },
      },
    ]);
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      'Delete Account',
      'This action cannot be undone. All your data will be permanently deleted.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            Alert.alert(
              'Confirm Deletion',
              'Type "DELETE" to confirm account deletion',
              [
                { text: 'Cancel', style: 'cancel' },
                {
                  text: 'I Understand',
                  style: 'destructive',
                  onPress: async () => {
                    // In production, this would call API to delete account
                    showMessage({
                      message: 'Account deletion requested',
                      description: 'Our team will process your request within 24 hours',
                      type: 'info',
                    });
                  },
                },
              ]
            );
          },
        },
      ]
    );
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.scrollContent}
    >
      {/* Appearance Section */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          Appearance
        </Text>

        <View style={[styles.card, { backgroundColor: theme.colors.surface }]}>
          <Text style={[styles.cardTitle, { color: theme.colors.text }]}>
            Theme
          </Text>
          <View style={styles.themeOptions}>
            <TouchableOpacity
              style={[
                styles.themeButton,
                themeMode === 'light' && {
                  backgroundColor: theme.colors.primary,
                },
                { borderColor: theme.colors.border },
              ]}
              onPress={() => handleThemeChange('light')}
            >
              <Text
                style={[
                  styles.themeButtonText,
                  {
                    color:
                      themeMode === 'light'
                        ? '#FFFFFF'
                        : theme.colors.text,
                  },
                ]}
              >
                ☀️ Light
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.themeButton,
                themeMode === 'dark' && {
                  backgroundColor: theme.colors.primary,
                },
                { borderColor: theme.colors.border },
              ]}
              onPress={() => handleThemeChange('dark')}
            >
              <Text
                style={[
                  styles.themeButtonText,
                  {
                    color:
                      themeMode === 'dark'
                        ? '#FFFFFF'
                        : theme.colors.text,
                  },
                ]}
              >
                🌙 Dark
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.themeButton,
                themeMode === 'auto' && {
                  backgroundColor: theme.colors.primary,
                },
                { borderColor: theme.colors.border },
              ]}
              onPress={() => handleThemeChange('auto')}
            >
              <Text
                style={[
                  styles.themeButtonText,
                  {
                    color:
                      themeMode === 'auto'
                        ? '#FFFFFF'
                        : theme.colors.text,
                  },
                ]}
              >
                🔄 Auto
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* Notifications Section */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          Notifications
        </Text>

        <View style={[styles.card, { backgroundColor: theme.colors.surface }]}>
          <SettingRow
            title="Push Notifications"
            description="Receive push notifications"
            value={pushNotifications}
            onValueChange={setPushNotifications}
            textColor={theme.colors.text}
            descriptionColor={theme.colors.textSecondary}
            trackColor={theme.colors.primary}
          />
          <SettingRow
            title="Trade Alerts"
            description="Get notified when trades execute"
            value={tradeAlerts}
            onValueChange={setTradeAlerts}
            textColor={theme.colors.text}
            descriptionColor={theme.colors.textSecondary}
            trackColor={theme.colors.primary}
          />
          <SettingRow
            title="Bot Status Alerts"
            description="Alerts for bot start, stop, errors"
            value={botStatusAlerts}
            onValueChange={setBotStatusAlerts}
            textColor={theme.colors.text}
            descriptionColor={theme.colors.textSecondary}
            trackColor={theme.colors.primary}
          />
          <SettingRow
            title="Price Alerts"
            description="Get notified of price movements"
            value={priceAlerts}
            onValueChange={setPriceAlerts}
            textColor={theme.colors.text}
            descriptionColor={theme.colors.textSecondary}
            trackColor={theme.colors.primary}
          />
          <SettingRow
            title="Marketing Emails"
            description="Receive product updates and tips"
            value={marketingEmails}
            onValueChange={setMarketingEmails}
            textColor={theme.colors.text}
            descriptionColor={theme.colors.textSecondary}
            trackColor={theme.colors.primary}
            noBorder
          />
        </View>
      </View>

      {/* Security Section */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          Security
        </Text>

        <View style={[styles.card, { backgroundColor: theme.colors.surface }]}>
          <SettingRow
            title="Biometric Authentication"
            description="Use fingerprint or Face ID"
            value={biometricAuth}
            onValueChange={setBiometricAuth}
            textColor={theme.colors.text}
            descriptionColor={theme.colors.textSecondary}
            trackColor={theme.colors.primary}
          />
          <SettingRow
            title="Auto-Lock"
            description="Lock app when inactive"
            value={autoLockEnabled}
            onValueChange={setAutoLockEnabled}
            textColor={theme.colors.text}
            descriptionColor={theme.colors.textSecondary}
            trackColor={theme.colors.primary}
            noBorder
          />
        </View>

        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: theme.colors.surface }]}
          onPress={() =>
            Alert.alert('Change Password', 'Password change feature coming soon')
          }
        >
          <Text style={[styles.actionButtonText, { color: theme.colors.text }]}>
            Change Password
          </Text>
          <Text style={styles.actionButtonIcon}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Data & Storage Section */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          Data & Storage
        </Text>

        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: theme.colors.surface }]}
          onPress={handleClearCache}
        >
          <View>
            <Text style={[styles.actionButtonText, { color: theme.colors.text }]}>
              Clear Cache
            </Text>
            <Text style={[styles.actionButtonDescription, { color: theme.colors.textSecondary }]}>
              Free up storage space
            </Text>
          </View>
          <Text style={styles.actionButtonIcon}>›</Text>
        </TouchableOpacity>
      </View>

      {/* About Section */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          About
        </Text>

        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: theme.colors.surface }]}
          onPress={() => Alert.alert('Version', 'AI Trading Bot v1.0.0')}
        >
          <Text style={[styles.actionButtonText, { color: theme.colors.text }]}>
            Version
          </Text>
          <Text style={[styles.versionText, { color: theme.colors.textSecondary }]}>
            1.0.0
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: theme.colors.surface }]}
          onPress={() => Alert.alert('Terms of Service', 'Opening Terms of Service...')}
        >
          <Text style={[styles.actionButtonText, { color: theme.colors.text }]}>
            Terms of Service
          </Text>
          <Text style={styles.actionButtonIcon}>›</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: theme.colors.surface }]}
          onPress={() => Alert.alert('Privacy Policy', 'Opening Privacy Policy...')}
        >
          <Text style={[styles.actionButtonText, { color: theme.colors.text }]}>
            Privacy Policy
          </Text>
          <Text style={styles.actionButtonIcon}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Account Actions Section */}
      <View style={styles.section}>
        <TouchableOpacity
          style={[styles.logoutButton, { backgroundColor: theme.colors.primary }]}
          onPress={handleLogout}
        >
          <Text style={styles.logoutButtonText}>Logout</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.deleteButton, { borderColor: '#EF4444' }]}
          onPress={handleDeleteAccount}
        >
          <Text style={[styles.deleteButtonText, { color: '#EF4444' }]}>
            Delete Account
          </Text>
        </TouchableOpacity>
      </View>

      <View style={styles.footer}>
        <Text style={[styles.footerText, { color: theme.colors.textSecondary }]}>
          AI Trading Bot Platform
        </Text>
        <Text style={[styles.footerText, { color: theme.colors.textSecondary }]}>
          © 2025 All rights reserved
        </Text>
      </View>
    </ScrollView>
  );
};

interface SettingRowProps {
  title: string;
  description: string;
  value: boolean;
  onValueChange: (value: boolean) => void;
  textColor: string;
  descriptionColor: string;
  trackColor: string;
  noBorder?: boolean;
}

const SettingRow: React.FC<SettingRowProps> = ({
  title,
  description,
  value,
  onValueChange,
  textColor,
  descriptionColor,
  trackColor,
  noBorder = false,
}) => (
  <View style={[styles.settingRow, noBorder && styles.noBorder]}>
    <View style={styles.settingRowContent}>
      <Text style={[styles.settingTitle, { color: textColor }]}>{title}</Text>
      <Text style={[styles.settingDescription, { color: descriptionColor }]}>
        {description}
      </Text>
    </View>
    <Switch
      value={value}
      onValueChange={onValueChange}
      trackColor={{ false: '#D1D5DB', true: trackColor }}
    />
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 12,
  },
  card: {
    borderRadius: 12,
    padding: 16,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  themeOptions: {
    flexDirection: 'row',
    gap: 8,
  },
  themeButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
  },
  themeButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  settingRow: {
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
  settingRowContent: {
    flex: 1,
    marginRight: 16,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  settingDescription: {
    fontSize: 14,
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
  actionButtonDescription: {
    fontSize: 14,
    marginTop: 2,
  },
  actionButtonIcon: {
    fontSize: 24,
    color: '#9CA3AF',
  },
  versionText: {
    fontSize: 16,
  },
  logoutButton: {
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 12,
  },
  logoutButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  deleteButton: {
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1,
  },
  deleteButtonText: {
    fontSize: 16,
    fontWeight: '700',
  },
  footer: {
    marginTop: 32,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    marginBottom: 4,
  },
});

export default SettingsScreen;
