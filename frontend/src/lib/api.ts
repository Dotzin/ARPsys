import axios from 'axios';
import { toast } from 'react-hot-toast';

const API_BASE_URL = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  console.log('API Request:', config.method?.toUpperCase(), config.url);
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/auth/login';
    } else if (error.response?.status >= 500) {
      toast.error('Erro interno do servidor. Tente novamente.');
    } else if (error.response?.data?.detail) {
      toast.error(error.response.data.detail);
    } else {
      toast.error('Ocorreu um erro inesperado.');
    }
    return Promise.reject(error);
  }
);

export interface LoginData {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name: string;
}

export interface ReportData {
  data_inicio: string;
  data_fim: string;
}

export interface OrderData {
  order_number: string;
  cart_number: string;
  sku: string;
  titulo: string;
  quantidade: number;
  valor_total: number;
  lucro_liquido: number;
  nicho: string;
}

export interface SkuNichoData {
  sku: string;
  nicho: string;
  titulo: string;
}

export interface IntegrationData {
  id: string;
  name: string;
  type: string;
  config: Record<string, unknown>;
  active: boolean;
}

// Auth API
export const authApi = {
  login: async (data: LoginData) => {
    const response = await api.post('/auth/login', data, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      transformRequest: [(data) => {
        const params = new URLSearchParams();
        Object.entries(data).forEach(([key, value]) => params.append(key, String(value)));
        return params;
      }],
    });
    return response.data;
  },

  register: async (data: RegisterData) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
  },
};

// Reports API
export const reportsApi = {
  getReport: async (params: ReportData) => {
    const response = await api.get('/relatorio', { params });
    return response.data;
  },

  getDailyReport: async () => {
    const response = await api.get('/relatorio/daily');
    return response.data;
  },
};

// Orders API
export const ordersApi = {
  getOrders: async (params?: { page?: number; size?: number }) => {
    const response = await api.get('/orders', { params });
    return response.data;
  },

  createOrder: async (data: OrderData) => {
    const response = await api.post('/orders', data);
    return response.data;
  },
};

// SKU Niche API
export const skuNichoApi = {
  getSkuNichos: async () => {
    const response = await api.get('/sku-nicho');
    return response.data;
  },

  createSkuNicho: async (data: SkuNichoData) => {
    const response = await api.post('/sku-nicho', data);
    return response.data;
  },
};

// Integrations API
export const integrationsApi = {
  getIntegrations: async () => {
    const response = await api.get('/integrations');
    return response.data;
  },

  updateIntegration: async (id: string, data: Partial<IntegrationData>) => {
    const response = await api.put(`/integrations/${id}`, data);
    return response.data;
  },
};
