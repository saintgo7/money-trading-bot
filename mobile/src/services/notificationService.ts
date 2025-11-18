import messaging from '@react-native-firebase/messaging';
import notifee, { AndroidImportance, EventType } from '@notifee/react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const setupNotifications = async () => {
  // Request permission
  const authStatus = await messaging().requestPermission();
  const enabled =
    authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
    authStatus === messaging.AuthorizationStatus.PROVISIONAL;

  if (enabled) {
    console.log('Notification permission granted');

    // Get FCM token
    const fcmToken = await messaging().getToken();
    console.log('FCM Token:', fcmToken);

    // Save token
    await AsyncStorage.setItem('fcm_token', fcmToken);

    // TODO: Send token to backend
    // api.notifications.updateToken(fcmToken);
  }

  // Create notification channel for Android
  await notifee.createChannel({
    id: 'default',
    name: 'Default Channel',
    importance: AndroidImportance.HIGH,
  });

  await notifee.createChannel({
    id: 'trades',
    name: 'Trade Notifications',
    importance: AndroidImportance.HIGH,
    sound: 'trade_alert',
  });

  await notifee.createChannel({
    id: 'alerts',
    name: 'Price Alerts',
    importance: AndroidImportance.HIGH,
    sound: 'price_alert',
  });

  // Handle foreground messages
  messaging().onMessage(async (remoteMessage) => {
    console.log('Foreground message:', remoteMessage);
    await displayNotification(remoteMessage);
  });

  // Handle background messages
  messaging().setBackgroundMessageHandler(async (remoteMessage) => {
    console.log('Background message:', remoteMessage);
    await displayNotification(remoteMessage);
  });

  // Handle notification interactions
  notifee.onForegroundEvent(({ type, detail }) => {
    if (type === EventType.PRESS) {
      console.log('Notification pressed:', detail.notification);
      handleNotificationPress(detail.notification);
    }
  });

  notifee.onBackgroundEvent(async ({ type, detail }) => {
    if (type === EventType.PRESS) {
      console.log('Background notification pressed:', detail.notification);
      handleNotificationPress(detail.notification);
    }
  });
};

const displayNotification = async (message: any) => {
  const { notification, data } = message;

  if (!notification) return;

  const channelId = data?.type === 'trade' ? 'trades' : data?.type === 'alert' ? 'alerts' : 'default';

  await notifee.displayNotification({
    title: notification.title,
    body: notification.body,
    android: {
      channelId,
      importance: AndroidImportance.HIGH,
      pressAction: {
        id: 'default',
      },
      smallIcon: 'ic_notification',
      largeIcon: data?.icon,
    },
    ios: {
      sound: data?.type === 'trade' ? 'trade_alert.wav' : 'default',
      categoryId: data?.type || 'default',
    },
    data,
  });
};

const handleNotificationPress = (notification: any) => {
  const { data } = notification;

  if (!data) return;

  // Navigate based on notification type
  switch (data.type) {
    case 'trade':
      if (data.botId) {
        // Navigate to bot detail
        // navigationRef.current?.navigate('BotDetail', { botId: parseInt(data.botId) });
      }
      break;
    case 'alert':
      // Navigate to alerts
      break;
    case 'subscription':
      // Navigate to subscription page
      break;
    default:
      // Navigate to notifications
      break;
  }
};

export const scheduleLocalNotification = async (
  title: string,
  body: string,
  data?: any,
  triggerDate?: Date
) => {
  const trigger = triggerDate
    ? {
        type: 'timestamp' as const,
        timestamp: triggerDate.getTime(),
      }
    : undefined;

  await notifee.displayNotification({
    title,
    body,
    android: {
      channelId: 'default',
      importance: AndroidImportance.HIGH,
    },
    data,
  });
};

export const cancelAllNotifications = async () => {
  await notifee.cancelAllNotifications();
};

export const getInitialNotification = async () => {
  return await notifee.getInitialNotification();
};
