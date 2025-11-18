import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = __DEV__
  ? 'http://localhost:8000/api/v1'
  : 'https://api.trading-bot.com/api/v1';

class ApiService {
  private client: AxiosInstance;
  private authToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          await AsyncStorage.removeItem('auth_token');
          await AsyncStorage.removeItem('user_data');
          this.authToken = null;
        }
        return Promise.reject(error);
      }
    );
  }

  setAuthToken(token: string | null) {
    this.authToken = token;
  }

  // Generic request methods
  async get<T = any>(url: string, config?: AxiosRequestConfig) {
    return this.client.get<T>(url, config);
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
    return this.client.post<T>(url, data, config);
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
    return this.client.put<T>(url, data, config);
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
    return this.client.patch<T>(url, data, config);
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig) {
    return this.client.delete<T>(url, config);
  }

  // Auth endpoints
  auth = {
    login: (email: string, password: string) => {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      return this.post('/auth/login', formData.toString(), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
    },
    register: (data: { email: string; username: string; password: string }) =>
      this.post('/auth/register', data),
    getMe: () => this.get('/auth/me'),
  };

  // Bots endpoints
  bots = {
    getAll: () => this.get('/bots'),
    getById: (id: number) => this.get(`/bots/${id}`),
    create: (data: any) => this.post('/bots', data),
    update: (id: number, data: any) => this.put(`/bots/${id}`, data),
    delete: (id: number) => this.delete(`/bots/${id}`),
    start: (id: number) => this.post(`/bots/${id}/start`),
    stop: (id: number) => this.post(`/bots/${id}/stop`),
    getStats: () => this.get('/bots/stats'),
    getTrades: (id: number, params?: any) => this.get(`/bots/${id}/trades`, { params }),
    getOrders: (id: number, params?: any) => this.get(`/bots/${id}/orders`, { params }),
  };

  // Strategies endpoints
  strategies = {
    getAll: () => this.get('/strategies'),
    getById: (id: number) => this.get(`/strategies/${id}`),
    create: (data: any) => this.post('/strategies', data),
    update: (id: number, data: any) => this.put(`/strategies/${id}`, data),
    delete: (id: number) => this.delete(`/strategies/${id}`),
    backtest: (id: number, params: any) => this.post(`/strategies/${id}/backtest`, params),
  };

  // Marketplace endpoints
  marketplace = {
    search: (params?: any) => this.get('/marketplace/search', { params }),
    getStrategy: (id: number) => this.get(`/marketplace/strategies/${id}`),
    getFeatured: (params?: any) => this.get('/marketplace/featured', { params }),
    getTrending: (params?: any) => this.get('/marketplace/trending', { params }),
    purchase: (id: number, paymentMethodId?: string) =>
      this.post(`/marketplace/strategies/${id}/purchase`, { payment_method_id: paymentMethodId }),
    getMyPurchases: () => this.get('/marketplace/purchases'),
    getMyStrategies: () => this.get('/marketplace/my-strategies'),
    publish: (data: any) => this.post('/marketplace/publish', data),
    addReview: (id: number, data: any) => this.post(`/marketplace/strategies/${id}/review`, data),
    getReviews: (id: number, params?: any) =>
      this.get(`/marketplace/strategies/${id}/reviews`, { params }),
    getStats: () => this.get('/marketplace/stats'),
    getEarnings: () => this.get('/marketplace/earnings'),
  };

  // Subscription endpoints
  subscriptions = {
    getPlans: () => this.get('/subscriptions/plans'),
    getCurrent: () => this.get('/subscriptions/current'),
    subscribe: (data: any) => this.post('/subscriptions/subscribe', data),
    cancel: (immediate: boolean = false) =>
      this.post(`/subscriptions/cancel?immediate=${immediate}`),
    upgrade: (tier: string) => this.post('/subscriptions/upgrade', { new_tier: tier }),
    downgrade: (tier: string) => this.post('/subscriptions/downgrade', { new_tier: tier }),
    getPayments: (params?: any) => this.get('/subscriptions/payments', { params }),
    getUsage: () => this.get('/subscriptions/usage'),
    createPaymentIntent: (data: any) => this.post('/subscriptions/payment-intent', data),
  };

  // Exchanges endpoints
  exchanges = {
    getAll: () => this.get('/exchanges'),
    getCredentials: () => this.get('/exchanges/credentials'),
    addCredential: (data: any) => this.post('/exchanges/credentials', data),
    updateCredential: (id: number, data: any) => this.put(`/exchanges/credentials/${id}`, data),
    deleteCredential: (id: number) => this.delete(`/exchanges/credentials/${id}`),
    testConnection: (id: number) => this.post(`/exchanges/credentials/${id}/test`),
  };

  // Notifications endpoints
  notifications = {
    getAll: (params?: any) => this.get('/notifications', { params }),
    markAsRead: (id: number) => this.put(`/notifications/${id}/read`),
    markAllAsRead: () => this.post('/notifications/read-all'),
    deleteAll: () => this.delete('/notifications'),
  };
}

export const api = new ApiService();
