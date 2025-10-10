import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  authApi,
  reportsApi,
  ordersApi,
  skuNichoApi,
  integrationsApi,
  LoginData,
  RegisterData,
  ReportData,
  OrderData,
  SkuNichoData,
  IntegrationData,
} from './api';

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
}

// Auth hooks
export const useLogin = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: LoginData) => authApi.login(data),
    onSuccess: (data: { access_token: string }) => {
      localStorage.setItem('access_token', data.access_token);
      queryClient.invalidateQueries();
      toast.success('Login realizado com sucesso!');
    },
    onError: (error: ApiError) => {
      toast.error(error.response?.data?.detail || 'Erro no login');
    },
  });
};

export const useRegister = () => {
  return useMutation({
    mutationFn: (data: RegisterData) => authApi.register(data),
    onSuccess: () => {
      toast.success('Registro realizado com sucesso!');
    },
    onError: (error: ApiError) => {
      toast.error(error.response?.data?.detail || 'Erro no registro');
    },
  });
};

// Reports hooks
export const useReports = (params: ReportData, enabled = false) => {
  return useQuery({
    queryKey: ['reports', params],
    queryFn: () => reportsApi.getFlexReport(params),
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useDailyReport = () => {
  return useQuery({
    queryKey: ['daily-report'],
    queryFn: () => reportsApi.getDailyReport(),
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
  });
};

// Orders hooks
export const useOrders = () => {
  return useQuery({
    queryKey: ['orders'],
    queryFn: () => ordersApi.getOrders(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const useOrdersByPeriod = (dataInicio: string, dataFim: string, enabled = false) => {
  return useQuery({
    queryKey: ['orders', dataInicio, dataFim],
    queryFn: () => ordersApi.getOrdersByPeriod(dataInicio, dataFim),
    enabled,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

// SKU Niche hooks
export const useSkuNichos = () => {
  return useQuery({
    queryKey: ['sku-nichos'],
    queryFn: () => skuNichoApi.getSkuNichos(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useCreateSkuNicho = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SkuNichoData) => skuNichoApi.createSkuNicho(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sku-nichos'] });
      toast.success('SKU/Nicho criado com sucesso!');
    },
    onError: (error: ApiError) => {
      toast.error(error.response?.data?.detail || 'Erro ao criar SKU/Nicho');
    },
  });
};

// Integrations hooks
export const useIntegrations = () => {
  return useQuery({
    queryKey: ['integrations'],
    queryFn: () => integrationsApi.getIntegrations(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useUpdateIntegration = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<IntegrationData> }) =>
      integrationsApi.updateIntegration(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
      toast.success('Integração atualizada com sucesso!');
    },
    onError: (error: ApiError) => {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar integração');
    },
  });
};
