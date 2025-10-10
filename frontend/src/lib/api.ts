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
  getFlexReport: async (params: ReportData) => {
    const response = await api.get('/relatorios/flex', { params });
    return response.data;
  },

  getDailyReport: async () => {
    const response = await api.get('/relatorios/diario');
    return response.data;
  },

  updateOrders: async (data?: { data?: string }) => {
    const response = await api.post('/atualizar_pedidos', data);
    return response.data;
  },
};

// Orders API
export const ordersApi = {
  getOrders: async () => {
    const response = await api.get('/orders');
    return response.data;
  },

  getOrdersByPeriod: async (dataInicio: string, dataFim: string) => {
    const response = await api.get('/orders/periodo', { params: { data_inicio: dataInicio, data_fim: dataFim } });
    return response.data;
  },
};

// SKU Niche API
export const skuNichoApi = {
  getSkuNichos: async () => {
    const response = await api.get('/sku_nicho/listar');
    return response.data;
  },

  createSkuNicho: async (data: SkuNichoData) => {
    const response = await api.post('/sku_nicho/inserir', data);
    return response.data;
  },

  updateSkuNicho: async (data: { sku: string; novo_nicho: string }) => {
    const response = await api.put('/sku_nicho/atualizar', data);
    return response.data;
  },

  deleteSkuNicho: async (data: { sku: string }) => {
    const response = await api.delete('/sku_nicho/deletar', { data });
    return response.data;
  },

  downloadTemplate: async () => {
    const response = await api.get('/sku_nicho/template_xlsx', { responseType: 'blob' });
    return response.data;
  },

  bulkUpload: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/sku_nicho/inserir_xlsx', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Integrations API
export const integrationsApi = {
  getIntegrations: async () => {
    const response = await api.get('/integrations/tokens');
    // Transform the response to match expected format
    const tokens = response.data;
    const integrations = [];
    if (tokens.arp_session_cookie) {
      integrations.push({
        id: 'arpcommerce',
        name: 'ARPCommerce',
        type: 'arpcommerce',
        config: { token: tokens.arp_session_cookie },
        active: true,
      });
    }
    if (tokens.auth_bearer_token) {
      integrations.push({
        id: 'bearer',
        name: 'Bearer Token',
        type: 'bearer',
        config: { token: tokens.auth_bearer_token },
        active: true,
      });
    }
    return { data: integrations };
  },

  updateIntegration: async (id: string, data: Partial<IntegrationData>) => {
    // For now, just return success since the backend doesn't have update endpoint
    return { data: { message: 'Integration updated' } };
  },
};
