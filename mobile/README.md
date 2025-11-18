# Trading Bot Mobile App

React Native mobile application for AI-powered cryptocurrency trading platform.

## Features

- 📱 **Cross-Platform**: iOS and Android support
- 🤖 **Bot Management**: Create, monitor, and control trading bots
- 📊 **Real-time Dashboard**: Live performance metrics and charts
- 🏪 **Strategy Marketplace**: Buy and sell trading strategies
- 💳 **Subscription Management**: Manage premium features
- 🔔 **Push Notifications**: Real-time trade alerts
- 🌓 **Dark Mode**: Beautiful light and dark themes
- 🔐 **Biometric Auth**: Fingerprint and Face ID support

---

## Screenshots

[Screenshots would go here]

---

## Prerequisites

- Node.js >= 18
- React Native CLI
- Xcode (for iOS)
- Android Studio (for Android)
- CocoaPods (for iOS)

---

## Installation

### 1. Clone and Install Dependencies

```bash
cd mobile
npm install

# iOS only
cd ios && pod install && cd ..
```

### 2. Environment Configuration

Create `.env` file:

```env
API_URL=http://localhost:8000/api/v1
WS_URL=ws://localhost:8000/ws

# Firebase (for push notifications)
FIREBASE_API_KEY=your_api_key
FIREBASE_PROJECT_ID=your_project_id

# Stripe (for payments)
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### 3. Run the App

#### iOS

```bash
npm run ios
# or
npx react-native run-ios
```

#### Android

```bash
npm run android
# or
npx react-native run-android
```

---

## Project Structure

```
mobile/
├── src/
│   ├── components/         # Reusable components
│   │   ├── BotCard.tsx
│   │   ├── StrategyCard.tsx
│   │   ├── PriceChart.tsx
│   │   └── ...
│   ├── contexts/           # React contexts
│   │   ├── AuthContext.tsx
│   │   ├── ThemeContext.tsx
│   │   └── WebSocketContext.tsx
│   ├── navigation/         # Navigation setup
│   │   └── AppNavigator.tsx
│   ├── screens/            # App screens
│   │   ├── auth/
│   │   │   ├── LoginScreen.tsx
│   │   │   ├── RegisterScreen.tsx
│   │   │   └── ForgotPasswordScreen.tsx
│   │   └── main/
│   │       ├── DashboardScreen.tsx
│   │       ├── BotsScreen.tsx
│   │       ├── BotDetailScreen.tsx
│   │       ├── CreateBotScreen.tsx
│   │       ├── MarketplaceScreen.tsx
│   │       ├── StrategyDetailScreen.tsx
│   │       ├── ProfileScreen.tsx
│   │       ├── SettingsScreen.tsx
│   │       ├── SubscriptionScreen.tsx
│   │       └── NotificationsScreen.tsx
│   ├── services/           # API and services
│   │   ├── api.ts
│   │   ├── notificationService.ts
│   │   └── websocket.ts
│   ├── hooks/              # Custom hooks
│   │   ├── useWebSocket.ts
│   │   ├── useBots.ts
│   │   └── useSubscription.ts
│   ├── utils/              # Utility functions
│   │   ├── formatting.ts
│   │   ├── validation.ts
│   │   └── storage.ts
│   └── types/              # TypeScript types
│       └── index.ts
├── android/                # Android native code
├── ios/                    # iOS native code
├── App.tsx                 # App entry point
├── package.json
└── tsconfig.json
```

---

## Key Technologies

### Core

- **React Native** 0.72+ - Mobile framework
- **TypeScript** - Type safety
- **React Navigation** - Navigation library
- **Axios** - HTTP client
- **Socket.IO** - WebSocket real-time updates

### UI Components

- **React Native Chart Kit** - Charts and graphs
- **React Native SVG** - Vector graphics
- **React Native Vector Icons** - Icon library
- **React Native Linear Gradient** - Gradient backgrounds
- **React Native Modal** - Modal dialogs

### State Management

- **React Context API** - Global state
- **AsyncStorage** - Local persistence
- **MMKV** - Fast key-value storage

### Push Notifications

- **@notifee/react-native** - Local notifications
- **@react-native-firebase/messaging** - FCM push notifications

### Authentication & Security

- **React Native Biometrics** - Fingerprint/Face ID
- **AsyncStorage** - Secure token storage

### Forms & Validation

- **React Hook Form** - Form management
- **Zod** - Schema validation

---

## Features Overview

### 1. **Dashboard**

Real-time overview of trading performance:

- Active bots count
- Total P&L
- Win rate statistics
- Weekly performance chart
- Recent bot activity

### 2. **Bot Management**

Complete bot lifecycle management:

- Create new trading bots
- Configure strategies and parameters
- Start/stop bots
- Monitor real-time performance
- View trade history
- Adjust settings

### 3. **Strategy Marketplace**

Discover and purchase strategies:

- Browse featured strategies
- Search and filter
- View detailed performance metrics
- Purchase strategies
- Rate and review
- Track earnings (for sellers)

### 4. **Subscription Management**

Premium tier management:

- View current plan
- Upgrade/downgrade
- Payment history
- Usage metrics
- Billing information

### 5. **Real-time Updates**

WebSocket integration for live data:

- Bot status changes
- New trades executed
- P&L updates
- Price alerts
- System notifications

### 6. **Push Notifications**

Timely alerts for important events:

- Trade execution notifications
- Stop-loss/take-profit triggers
- Bot status changes
- Subscription updates
- Price alerts

---

## Development

### Running in Development

```bash
# Start Metro bundler
npm start

# Run on iOS simulator
npm run ios

# Run on Android emulator
npm run android

# Run on physical device
npm run ios -- --device
npm run android -- --deviceId=<device-id>
```

### Debugging

#### React Native Debugger

```bash
# Install
brew install --cask react-native-debugger

# Run
open "rndebugger://set-debugger-loc?host=localhost&port=8081"
```

#### Flipper

Built-in debugging tool:

- Network inspector
- Layout inspector
- Logs viewer
- Redux DevTools

### Linting

```bash
npm run lint
npm run lint:fix
```

### Testing

```bash
npm test
npm run test:watch
npm run test:coverage
```

---

## Building for Production

### iOS

1. **Configure signing** in Xcode
2. **Update version** in `ios/TradingBot/Info.plist`
3. **Build**:

```bash
npm run build:ios
# or
cd ios && xcodebuild -workspace TradingBot.xcworkspace \
  -scheme TradingBot -configuration Release
```

4. **Submit to App Store** via Xcode or Transporter

### Android

1. **Generate keystore**:

```bash
keytool -genkeypair -v -storetype PKCS12 -keystore trading-bot.keystore \
  -alias trading-bot -keyalg RSA -keysize 2048 -validity 10000
```

2. **Configure signing** in `android/gradle.properties`

3. **Update version** in `android/app/build.gradle`

4. **Build APK/AAB**:

```bash
npm run build:android
# or
cd android && ./gradlew assembleRelease
cd android && ./gradlew bundleRelease  # For Play Store
```

5. **Submit to Play Store** via Google Play Console

---

## Push Notifications Setup

### iOS

1. **Enable Push Notifications** in Xcode capabilities
2. **Create APNs key** in Apple Developer Console
3. **Upload to Firebase** Console

### Android

1. **Download `google-services.json`** from Firebase
2. **Place in** `android/app/`
3. **Configure** Firebase Cloud Messaging

### Backend Integration

Send notifications from backend:

```python
# Python example
import requests

def send_push_notification(fcm_token: str, title: str, body: str, data: dict):
    headers = {
        'Authorization': f'key={FIREBASE_SERVER_KEY}',
        'Content-Type': 'application/json',
    }

    payload = {
        'to': fcm_token,
        'notification': {
            'title': title,
            'body': body,
        },
        'data': data,
    }

    requests.post('https://fcm.googleapis.com/fcm/send',
                  json=payload, headers=headers)
```

---

## Performance Optimization

### 1. **Image Optimization**

- Use WebP format
- Implement lazy loading
- Cache images

### 2. **Bundle Size**

```bash
# Analyze bundle
npx react-native-bundle-visualizer
```

### 3. **Memory Management**

- Unsubscribe from listeners
- Clean up intervals/timeouts
- Use PureComponent/React.memo

### 4. **List Performance**

- Use `FlatList` instead of `ScrollView`
- Implement `getItemLayout`
- Use `removeClippedSubviews`

---

## Troubleshooting

### Common Issues

#### iOS Build Fails

```bash
# Clean and rebuild
cd ios
rm -rf Pods Podfile.lock
pod deintegrate
pod install
cd ..
```

#### Android Build Fails

```bash
# Clean Gradle
cd android
./gradlew clean
./gradlew --stop
cd ..
```

#### Metro Bundler Issues

```bash
# Reset cache
npm start -- --reset-cache

# or
watchman watch-del-all
rm -rf node_modules
npm install
```

#### WebSocket Connection Fails

- Check API URL in `.env`
- Verify backend is running
- Check firewall settings
- Use correct protocol (ws:// vs wss://)

---

## API Integration

### Authentication

```typescript
import { api } from './services/api';

// Login
const { data } = await api.auth.login(email, password);
const token = data.access_token;

// Set token for future requests
api.setAuthToken(token);

// Fetch user data
const user = await api.auth.getMe();
```

### WebSocket

```typescript
import { io } from 'socket.io-client';

const socket = io('ws://localhost:8000', {
  auth: {
    token: authToken,
  },
});

// Listen to bot updates
socket.on('bot_update', (data) => {
  console.log('Bot updated:', data);
});

// Listen to trade events
socket.on('trade_executed', (data) => {
  console.log('Trade executed:', data);
});
```

---

## App Store Submission

### Requirements

#### iOS App Store

- Developer account ($99/year)
- App Store screenshots (6.5", 5.5")
- App icon (1024x1024)
- Privacy policy URL
- App description and keywords

#### Google Play Store

- Developer account ($25 one-time)
- Feature graphic (1024x500)
- App icon (512x512)
- Screenshots (min 2)
- Privacy policy URL
- Content rating questionnaire

### Review Guidelines

- Follow platform design guidelines
- No misleading functionality
- Proper error handling
- Clear pricing information
- Working demo/test account

---

## Monitoring & Analytics

### Recommended Tools

- **Firebase Analytics** - User behavior
- **Sentry** - Error tracking
- **Mixpanel** - Product analytics
- **AppCenter** - Crash reporting

### Setup Example

```typescript
import analytics from '@react-native-firebase/analytics';

// Log events
await analytics().logEvent('bot_created', {
  bot_id: botId,
  strategy: strategyName,
});

// Track screens
await analytics().logScreenView({
  screen_name: 'Dashboard',
  screen_class: 'DashboardScreen',
});
```

---

## Security Best Practices

1. **Never store sensitive data** in AsyncStorage without encryption
2. **Validate all user input** on client and server
3. **Use HTTPS** for all API calls
4. **Implement certificate pinning** for production
5. **Obfuscate code** before release
6. **Enable ProGuard** (Android)
7. **Use Keychain** (iOS) for sensitive data

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## License

MIT License - see LICENSE file for details

---

## Support

- **Email**: support@trading-bot.com
- **Discord**: https://discord.gg/trading-bot
- **Documentation**: https://docs.trading-bot.com/mobile

---

## Changelog

### v1.0.0 (2025-01-18)

- ✨ Initial release
- 🤖 Bot management
- 📊 Real-time dashboard
- 🏪 Strategy marketplace
- 💳 Subscription system
- 🔔 Push notifications
- 🌓 Dark mode support
