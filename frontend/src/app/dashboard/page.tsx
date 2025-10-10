'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { reportsApi } from '../../lib/api';
import { toast } from 'react-hot-toast';
import { ThemeToggle } from '../../components/ThemeToggle';
import { Sidebar } from '../../components/Sidebar';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { DollarSign, TrendingUp, ShoppingCart, Package, Calculator, Percent, LogOut, Clock, Star, Trophy } from 'lucide-react';

interface ReportData {
  status: string;
  dados?: any;
  erro?: string;
}

interface DailyReport {
  dia: string;
  status: string;
  kpis_diarios: {
    lucro_liquido: number;
    faturamento: number;
    total_pedidos: number;
    total_unidades: number;
  };
  analise_por_nicho_dia: Array<{
    nicho: string;
    lucro_liquido: number;
    faturamento: number;
    total_pedidos: number;
  }>;
  por_hora: Array<{
    hour: number;
    lucro_liquido: number;
    faturamento: number;
    total_pedidos: number;
  }>;
  ultima_venda: any;
  melhor_produto: any;
  melhor_anuncio: any;
}

export default function DashboardPage() {
  const [user, setUser] = useState(null);
  const [dailyReport, setDailyReport] = useState<DailyReport | null>(null);
  const [lastMonthReport, setLastMonthReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const loadDailyReport = async () => {
    try {
      const response = await reportsApi.getDailyReport();
      if (response.status === 'sucesso') {
        setDailyReport(response);
      } else {
        toast.error(response.erro || 'Erro ao carregar relatório diário');
      }
    } catch (error) {
      console.error('Error loading daily report:', error);
      toast.error('Erro ao carregar relatório diário');
    } finally {
      setLoading(false);
    }
  };

  const loadLastMonthReport = async () => {
    try {
      const today = new Date();
      const last30DaysStart = new Date(today);
      last30DaysStart.setDate(today.getDate() - 30);

      const dataInicio = last30DaysStart.toISOString().split('T')[0];
      const dataFim = today.toISOString().split('T')[0];

      const response = await reportsApi.getFlexReport({
        data_inicio: dataInicio,
        data_fim: dataFim,
      });

      if (response.status === 'sucesso') {
        setLastMonthReport(response);
      } else {
        console.error('Erro ao carregar relatório dos últimos 30 dias:', response.erro);
      }
    } catch (error) {
      console.error('Error loading last 30 days report:', error);
    }
  };

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/auth/login');
      return;
    }

    // Load today's report
    loadDailyReport();
    loadLastMonthReport();

    // Connect to WebSocket for live updates
    const ws = new WebSocket(`ws://localhost:8000/ws/relatorio_diario?token=${token}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.tipo === 'relatorio_diario') {
          setDailyReport(data.dados);
        }
      } catch (e) {
        console.error('Error parsing WS message:', e);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return () => {
      ws.close();
    };
  }, [router]);



  const handleLogout = () => {
    localStorage.removeItem('access_token');
    router.push('/auth/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Sidebar */}
      <div className="w-64 fixed h-full">
        <Sidebar currentPage="/dashboard" />
      </div>

      {/* Main Content */}
      <div className="flex-1 ml-64">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Dashboard
            </h1>

            <div className="flex items-center space-x-4">
              <ThemeToggle />

              <button
                onClick={handleLogout}
                className="flex items-center px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </header>

        <main className="p-6">
        {loading ? (
          <div className="text-center py-12">
            <div className="text-gray-500 dark:text-gray-400">Carregando dashboard...</div>
          </div>
        ) : dailyReport && (dailyReport.status === 'sucesso' || dailyReport.status === 'sem_dados') ? (
          <div className="space-y-6">
            {/* KPIs Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-6">
              <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center space-x-4">
                <DollarSign className="h-8 w-8 text-gray-400 dark:text-gray-500" />
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Faturamento Hoje</h3>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white">R$ {(dailyReport.kpis_diarios?.faturamento || 0).toFixed(2)}</p>
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center space-x-4">
                <TrendingUp className="h-8 w-8 text-green-500 dark:text-green-400" />
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Lucro Líquido Hoje</h3>
                  <p className="text-3xl font-bold text-green-600 dark:text-green-400">R$ {(dailyReport.kpis_diarios?.lucro_liquido || 0).toFixed(2)}</p>
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center space-x-4">
                <ShoppingCart className="h-8 w-8 text-gray-400 dark:text-gray-500" />
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Pedidos Hoje</h3>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white">{dailyReport.kpis_diarios?.total_pedidos || 0}</p>
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center space-x-4">
                <Package className="h-8 w-8 text-gray-400 dark:text-gray-500" />
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Unidades Hoje</h3>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white">{dailyReport.kpis_diarios?.total_unidades || 0}</p>
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center space-x-4">
                <Calculator className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Ticket Médio</h3>
                  <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">R$ {((dailyReport.kpis_diarios?.faturamento || 0) / (dailyReport.kpis_diarios?.total_pedidos || 1)).toFixed(2)}</p>
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center space-x-4">
                <Percent className="h-8 w-8 text-purple-600 dark:text-purple-400" />
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Margem de Lucro</h3>
                  <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">{((dailyReport.kpis_diarios?.lucro_liquido || 0) / (dailyReport.kpis_diarios?.faturamento || 1) * 100).toFixed(1)}%</p>
                </div>
              </div>
            </div>

            {/* Last Month KPIs */}
            {lastMonthReport && lastMonthReport.status === 'sucesso' && (
              <div className="space-y-4">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Últimos 30 Dias</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-6">
                  <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center space-x-4">
                    <DollarSign className="h-8 w-8 text-gray-400 dark:text-gray-500" />
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Faturamento Últimos 30 Dias</h3>
                      <p className="text-3xl font-bold text-gray-900 dark:text-white">R$ {(lastMonthReport.dados?.kpis_gerais?.faturamento_total || 0).toFixed(2)}</p>
                    </div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center space-x-4">
                    <TrendingUp className="h-8 w-8 text-green-500 dark:text-green-400" />
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Lucro Líquido Últimos 30 Dias</h3>
                      <p className="text-3xl font-bold text-green-600 dark:text-green-400">R$ {(lastMonthReport.dados?.kpis_gerais?.lucro_liquido_total || 0).toFixed(2)}</p>
                    </div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center space-x-4">
                    <ShoppingCart className="h-8 w-8 text-gray-400 dark:text-gray-500" />
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Pedidos Último Mês</h3>
                      <p className="text-3xl font-bold text-gray-900 dark:text-white">{lastMonthReport.dados?.kpis_gerais?.total_pedidos || 0}</p>
                    </div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center space-x-4">
                    <Package className="h-8 w-8 text-gray-400 dark:text-gray-500" />
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Unidades Último Mês</h3>
                      <p className="text-3xl font-bold text-gray-900 dark:text-white">{lastMonthReport.dados?.kpis_gerais?.total_unidades || 0}</p>
                    </div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center space-x-4">
                    <Calculator className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Ticket Médio Último Mês</h3>
                      <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">R$ {(lastMonthReport.dados?.kpis_gerais?.ticket_medio?.pedido || 0).toFixed(2)}</p>
                    </div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center space-x-4">
                    <Percent className="h-8 w-8 text-purple-600 dark:text-purple-400" />
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Margem de Lucro Último Mês</h3>
                      <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">{(lastMonthReport.dados?.kpis_gerais?.indices?.rentabilidade_media || 0).toFixed(1)}%</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Charts and Details */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Niche Analysis */}
              <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Análise por Nicho (Hoje)</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={dailyReport.analise_por_nicho_dia}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="nicho" />
                    <YAxis />
                    <Tooltip formatter={(value) => `R$ ${Number(value).toFixed(2)}`} />
                    <Bar dataKey="faturamento" fill="#8884d8" name="Faturamento" />
                    <Bar dataKey="lucro_liquido" fill="#82ca9d" name="Lucro Líquido" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Hourly Sales */}
              <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Vendas por Hora (Hoje)</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={dailyReport.por_hora || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" />
                    <YAxis />
                    <Tooltip formatter={(value) => `R$ ${Number(value).toFixed(2)}`} />
                    <Line type="monotone" dataKey="faturamento" stroke="#8884d8" name="Faturamento" />
                    <Line type="monotone" dataKey="lucro_liquido" stroke="#82ca9d" name="Lucro Líquido" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Recent Info */}
              <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-6">Informações Recentes</h3>
                <div className="space-y-6">
                  {dailyReport.ultima_venda && (
                    <div className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      <Clock className="h-6 w-6 text-blue-500 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Última Venda</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                          {dailyReport.ultima_venda.title}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          R$ {dailyReport.ultima_venda.total_value?.toFixed(2)} • Lucro: R$ {dailyReport.ultima_venda.profit?.toFixed(2)} • {new Date(dailyReport.ultima_venda.payment_date).toLocaleString('pt-BR')}
                        </p>
                      </div>
                    </div>
                  )}
                  {dailyReport.melhor_produto && (
                    <div className="flex items-start space-x-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <Star className="h-6 w-6 text-green-500 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Melhor Produto Hoje</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                          SKU: {dailyReport.melhor_produto.sku}
                        </p>
                        <p className="text-xs text-green-600 dark:text-green-400 mt-1 font-medium">
                          Lucro: R$ {dailyReport.melhor_produto.profit?.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  )}
                  {dailyReport.melhor_anuncio && (
                    <div className="flex items-start space-x-3 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                      <Trophy className="h-6 w-6 text-purple-500 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Melhor Anúncio Hoje</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                          {dailyReport.melhor_anuncio.ad}
                        </p>
                        <p className="text-xs text-purple-600 dark:text-purple-400 mt-1 font-medium">
                          Lucro: R$ {dailyReport.melhor_anuncio.profit?.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Last Month Charts */}
            {lastMonthReport && lastMonthReport.status === 'sucesso' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Niche Analysis Last Month */}
                <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Análise por Nicho (Último Mês)</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={lastMonthReport.dados?.relatorios?.por_nicho || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="nicho" />
                      <YAxis />
                      <Tooltip formatter={(value) => `R$ ${Number(value).toFixed(2)}`} />
                      <Bar dataKey="faturamento_total" fill="#8884d8" name="Faturamento" />
                      <Bar dataKey="lucro_liquido" fill="#82ca9d" name="Lucro Líquido" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Last Month Summary */}
                <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-6">Resumo Último Mês</h3>
                  <div className="space-y-6">
                    <div className="flex items-start space-x-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <Package className="h-6 w-6 text-blue-500 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Principais Nichos</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                          {lastMonthReport.dados?.relatorios?.por_nicho?.slice(0, 3).map((n: any) => `${n.nicho} (R$ ${n.faturamento_total?.toFixed(2)})`).join(', ') || 'N/A'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <TrendingUp className="h-6 w-6 text-green-500 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Média Diária</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                          Faturamento: R$ {(lastMonthReport.dados?.kpis_gerais?.faturamento_total / 30).toFixed(2)} / dia
                        </p>
                        <p className="text-xs text-green-600 dark:text-green-400 mt-1 font-medium">
                          Lucro: R$ {(lastMonthReport.dados?.kpis_gerais?.lucro_liquido_total / 30).toFixed(2)} / dia
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                      <Star className="h-6 w-6 text-yellow-500 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Top Produto</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                          SKU: {lastMonthReport.dados?.rankings?.top_skus?.[0]?.sku || 'N/A'}
                        </p>
                        <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-1 font-medium">
                          Lucro: R$ {lastMonthReport.dados?.rankings?.top_skus?.[0]?.profit?.toFixed(2) || '0'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                      <Trophy className="h-6 w-6 text-purple-500 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Top Anúncio</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                          {lastMonthReport.dados?.rankings?.top_ads?.[0]?.ad || 'N/A'}
                        </p>
                        <p className="text-xs text-purple-600 dark:text-purple-400 mt-1 font-medium">
                          Lucro: R$ {lastMonthReport.dados?.rankings?.top_ads?.[0]?.profit?.toFixed(2) || '0'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}


          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-gray-500 dark:text-gray-400">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                Nenhum dado disponível
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Verifique se há pedidos para hoje.
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
    </div>
  );
}
