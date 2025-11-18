import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { showMessage } from 'react-native-flash-message';
import { useNavigation } from '@react-navigation/native';
import api from '../../services/api';

const ForgotPasswordScreen = () => {
  const { theme } = useTheme();
  const navigation = useNavigation();

  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);

  const validateEmail = () => {
    if (!email.trim()) {
      showMessage({
        message: 'Email is required',
        type: 'danger',
      });
      return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      showMessage({
        message: 'Please enter a valid email',
        type: 'danger',
      });
      return false;
    }

    return true;
  };

  const handleResetPassword = async () => {
    if (!validateEmail()) return;

    setLoading(true);
    try {
      await api.post('/auth/forgot-password', { email });
      setEmailSent(true);
      showMessage({
        message: 'Reset link sent!',
        description: 'Check your email for password reset instructions',
        type: 'success',
      });
    } catch (error: any) {
      showMessage({
        message: 'Failed to send reset link',
        description: error.response?.data?.detail || 'Please try again',
        type: 'danger',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.icon}>🔐</Text>
          <Text style={[styles.title, { color: theme.colors.text }]}>
            Forgot Password?
          </Text>
          <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
            {emailSent
              ? 'We sent you a password reset link'
              : 'Enter your email to reset your password'}
          </Text>
        </View>

        {!emailSent ? (
          <View style={styles.form}>
            <View style={styles.inputGroup}>
              <Text style={[styles.label, { color: theme.colors.text }]}>
                Email Address
              </Text>
              <TextInput
                style={[
                  styles.input,
                  {
                    backgroundColor: theme.colors.surface,
                    color: theme.colors.text,
                    borderColor: theme.colors.border,
                  },
                ]}
                placeholder="Enter your email"
                placeholderTextColor={theme.colors.textSecondary}
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
                editable={!loading}
              />
            </View>

            <TouchableOpacity
              style={[styles.resetButton, { backgroundColor: theme.colors.primary }]}
              onPress={handleResetPassword}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.resetButtonText}>Send Reset Link</Text>
              )}
            </TouchableOpacity>
          </View>
        ) : (
          <View style={[styles.successCard, { backgroundColor: theme.colors.surface }]}>
            <Text style={styles.successIcon}>✅</Text>
            <Text style={[styles.successText, { color: theme.colors.text }]}>
              Check your email
            </Text>
            <Text style={[styles.successDescription, { color: theme.colors.textSecondary }]}>
              We sent password reset instructions to:
            </Text>
            <Text style={[styles.emailText, { color: theme.colors.primary }]}>
              {email}
            </Text>
            <TouchableOpacity
              style={[styles.resendButton, { borderColor: theme.colors.border }]}
              onPress={handleResetPassword}
              disabled={loading}
            >
              <Text style={[styles.resendButtonText, { color: theme.colors.text }]}>
                Resend Email
              </Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.footer}>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Text style={[styles.backLink, { color: theme.colors.primary }]}>
              ← Back to Sign In
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  icon: {
    fontSize: 64,
    marginBottom: 16,
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
  form: {
    width: '100%',
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  input: {
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    borderWidth: 1,
  },
  resetButton: {
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 12,
  },
  resetButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  successCard: {
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
  },
  successIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  successText: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 8,
  },
  successDescription: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 8,
  },
  emailText: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 24,
  },
  resendButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
  },
  resendButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  footer: {
    alignItems: 'center',
    marginTop: 32,
  },
  backLink: {
    fontSize: 16,
    fontWeight: '600',
  },
});

export default ForgotPasswordScreen;
