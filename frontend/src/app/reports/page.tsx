'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { reportsApi, ordersApi } from '../../lib/api';
import { toast } from 'react-hot-toast';
import { Download, RefreshCw, DollarSign, TrendingUp, ShoppingCart, Package, Calculator, Percent, FileDown, LogOut, Search } from 'lucide-react';
import { ThemeToggle } from '../../components/ThemeToggle';
import { Sidebar } from '../../components/Sidebar';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import * as Tabs from '@radix-ui/react-tabs';

interface ReportData {
  status: string;
  dados?: any;
  erro?: string;
}

interface KPIGeral {
  faturamento_total: number;
  lucro_liquido_total: number;
  total_pedidos: number;
  total_unidades: number;
  ticket_medio: { pedido: number; unidade: number };
  custos: { custo_total: number; frete_total: number; impostos_total: number };
  indices: { rentabilidade_media: number; profitabilidade_media: number };
  skus_sem_nicho: string[];
}

interface RelatorioDiario {
  data: string;
  resumo: {
    faturamento: number;
    lucro_bruto: number;
    lucro_liquido: number;
    total_pedidos: number;
    total_unidades: number;
    ticket_medio: { pedido: number; unidade: number };
  };
  nichos: Array<{
    nicho: string;
    faturamento: number;
    lucro_bruto: number;
    profit: number;
    total_pedidos: number;
    total_unidades: number;
  }>;
}

interface PorNicho {
  nicho: string;
  lucro_liquido: number;
  lucro_bruto: number;
  total_pedidos: number;
  total_unidades: number;
  faturamento_total: number;
  participacao_faturamento: number;
  participacao_lucro: number;
  media_dia_valor: number;
  media_dia_unidades: number;
}

interface PorSKU {
  sku: string;
  nicho: string;
  lucro_liquido: number;
  lucro_bruto: number;
  total_pedidos: number;
  total_unidades: number;
  faturamento_total: number;
}

interface Ranking {
  sku?: string;
  ad?: string;
  nicho?: string;
  profit?: number;
  gross_profit?: number;
}

interface Order {
  id?: number;
  order_id: string;
  cart_id: string;
  ad: string;
  sku: string;
  title: string;
  quantity: number;
  total_value: number;
  payment_date: string;
  status: string;
  cost: number;
  gross_profit: number;
  taxes: number;
  freight: number;
  committee: number;
  fraction: number;
  profitability: number;
  rentability: number;
  store: string;
  profit: number;
  nicho: string;
  created_at?: string;
  updated_at?: string;
}

export default function ReportsPage() {
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [searchDiario, setSearchDiario] = useState('');
  const [searchNicho, setSearchNicho] = useState('');
  const [searchSku, setSearchSku] = useState('');
  const [searchTopSkus, setSearchTopSkus] = useState('');
  const [searchTopAds, setSearchTopAds] = useState('');
  const [updating, setUpdating] = useState(false);
  const [orders, setOrders] = useState<Order[]>([]);
  const [searchOrders, setSearchOrders] = useState('');
  const [currentPageOrders, setCurrentPageOrders] = useState(1);
  const [itemsPerPageOrders, setItemsPerPageOrders] = useState(50);

  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/auth/login');
    }
  }, [router]);

  // Reset to first page when search term or items per page changes
  useEffect(() => {
    setCurrentPageOrders(1);
  }, [searchOrders, itemsPerPageOrders]);

  const handleGenerateReport = async () => {
    if (!dataInicio || !dataFim) {
      toast.error('Selecione data início e fim');
      return;
    }

    setLoading(true);
    try {
      const response = await reportsApi.getFlexReport({
        data_inicio: dataInicio,
        data_fim: dataFim,
      });
      setReport(response);
      if (response.status === 'sucesso') {
        // Fetch orders for the period
        try {
          const ordersResponse = await ordersApi.getOrdersByPeriod(dataInicio, dataFim);
          setOrders(ordersResponse.pedidos || []);
          setCurrentPageOrders(1);
        } catch (error) {
          console.error('Error fetching orders:', error);
          setOrders([]);
        }
        toast.success('Relatório gerado com sucesso');
      } else {
        toast.error(response.erro || 'Erro ao gerar relatório');
      }
    } catch (error) {
      console.error('Error generating report:', error);
      toast.error('Erro ao gerar relatório');
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateOrders = async () => {
    setUpdating(true);
    try {
      const response = await reportsApi.updateOrders();
      toast.success(response.mensagem || 'Pedidos atualizados com sucesso');
      // Optionally refresh report if dates are set
      if (dataInicio && dataFim) {
        handleGenerateReport();
      }
    } catch (error) {
      console.error('Error updating orders:', error);
      toast.error('Erro ao atualizar pedidos');
    } finally {
      setUpdating(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    router.push('/auth/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Sidebar */}
      <div className="w-64 fixed h-full">
        <Sidebar currentPage="/reports" />
      </div>

      {/* Main Content */}
      <div className="flex-1 ml-64">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Relatórios
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
        <div className="space-y-6">
          {/* Controls */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Gerar Relatório
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label htmlFor="data-inicio" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Data Início
                </label>
                <input
                  type="date"
                  id="data-inicio"
                  value={dataInicio}
                  onChange={(e) => setDataInicio(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>

              <div>
                <label htmlFor="data-fim" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Data Fim
                </label>
                <input
                  type="date"
                  id="data-fim"
                  value={dataFim}
                  onChange={(e) => setDataFim(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>

              <div className="flex items-end">
                <button
                  onClick={handleGenerateReport}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors flex items-center justify-center"
                  disabled={loading}
                >

                  {loading ? 'Gerando...' : 'Gerar Relatório'}
                </button>
              </div>

              <div className="flex items-end">
                <button
                  onClick={handleUpdateOrders}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md transition-colors flex items-center justify-center"
                  disabled={updating}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${updating ? 'animate-spin' : ''}`} />
                  {updating ? 'Atualizando...' : 'Atualizar Pedidos'}
                </button>
              </div>
            </div>
          </div>

          {/* Report Results */}
          {report && (
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Resultados do Relatório
              </h2>

              {report.status === 'sucesso' && report.dados ? (
                <Tabs.Root defaultValue="kpis" className="w-full">
                  <Tabs.List className="flex border-b border-gray-200 dark:border-gray-700 mb-4">
                    <Tabs.Trigger value="kpis" className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white data-[state=active]:border-b-2 data-[state=active]:border-blue-500 data-[state=active]:text-blue-600 dark:data-[state=active]:text-blue-400">
                      KPIs Gerais
                    </Tabs.Trigger>
                    <Tabs.Trigger value="diario" className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white data-[state=active]:border-b-2 data-[state=active]:border-blue-500 data-[state=active]:text-blue-600 dark:data-[state=active]:text-blue-400">
                      Relatórios Diários
                    </Tabs.Trigger>
                    <Tabs.Trigger value="nicho" className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white data-[state=active]:border-b-2 data-[state=active]:border-blue-500 data-[state=active]:text-blue-600 dark:data-[state=active]:text-blue-400">
                      Por Nicho
                    </Tabs.Trigger>
                    <Tabs.Trigger value="sku" className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white data-[state=active]:border-b-2 data-[state=active]:border-blue-500 data-[state=active]:text-blue-600 dark:data-[state=active]:text-blue-400">
                      Por SKU
                    </Tabs.Trigger>
                    <Tabs.Trigger value="rankings" className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white data-[state=active]:border-b-2 data-[state=active]:border-blue-500 data-[state=active]:text-blue-600 dark:data-[state=active]:text-blue-400">
                      Rankings
                    </Tabs.Trigger>
                    <Tabs.Trigger value="skus-sem-nicho" className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white data-[state=active]:border-b-2 data-[state=active]:border-blue-500 data-[state=active]:text-blue-600 dark:data-[state=active]:text-blue-400">
                      SKUs sem Nicho
                    </Tabs.Trigger>
                    <Tabs.Trigger value="pedidos" className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white data-[state=active]:border-b-2 data-[state=active]:border-blue-500 data-[state=active]:text-blue-600 dark:data-[state=active]:text-blue-400">
                      Pedidos
                    </Tabs.Trigger>
                  </Tabs.List>

                  <Tabs.Content value="kpis" className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                        <DollarSign className="h-6 w-6 text-blue-600 mb-2" />
                        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Faturamento Total</h3>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">R$ {report.dados.kpis_gerais.faturamento_total.toFixed(2)}</p>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                        <TrendingUp className="h-6 w-6 text-green-600 mb-2" />
                        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Lucro Líquido Total</h3>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">R$ {report.dados.kpis_gerais.lucro_liquido_total.toFixed(2)}</p>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                        <ShoppingCart className="h-6 w-6 text-purple-600 mb-2" />
                        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Pedidos</h3>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">{report.dados.kpis_gerais.total_pedidos}</p>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                        <Package className="h-6 w-6 text-indigo-600 mb-2" />
                        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Unidades</h3>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">{report.dados.kpis_gerais.total_unidades}</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                        <Calculator className="h-6 w-6 text-orange-600 mb-2" />
                        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Ticket Médio</h3>
                        <p className="text-lg text-gray-900 dark:text-white">Pedido: R$ {report.dados.kpis_gerais.ticket_medio.pedido.toFixed(2)}</p>
                        <p className="text-lg text-gray-900 dark:text-white">Unidade: R$ {report.dados.kpis_gerais.ticket_medio.unidade.toFixed(2)}</p>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                        <Percent className="h-6 w-6 text-red-600 mb-2" />
                        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Custos Totais</h3>
                        <p className="text-lg text-gray-900 dark:text-white">Custo: R$ {report.dados.kpis_gerais.custos.custo_total.toFixed(2)}</p>
                        <p className="text-lg text-gray-900 dark:text-white">Frete: R$ {report.dados.kpis_gerais.custos.frete_total.toFixed(2)}</p>
                        <p className="text-lg text-gray-900 dark:text-white">Impostos: R$ {report.dados.kpis_gerais.custos.impostos_total.toFixed(2)}</p>
                      </div>
                    </div>
                  </Tabs.Content>



                  <Tabs.Content value="diario" className="space-y-4">
                    <div className="mb-4">
                      <div className="relative max-w-md">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <input
                          type="text"
                          placeholder="Buscar por data..."
                          value={searchDiario}
                          onChange={(e) => setSearchDiario(e.target.value)}
                          className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
                        />
                      </div>
                    </div>
                    {(() => {
                      const filteredDiario = report.dados.relatorios.diario.filter(dia =>
                        dia.data.toLowerCase().includes(searchDiario.toLowerCase())
                      );
                      return (
                        <>
                          <ResponsiveContainer width="100%" height={400}>
                            <LineChart data={filteredDiario}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="data" />
                        <YAxis />
                        <Tooltip formatter={(value) => `R$ ${Number(value).toFixed(2)}`} />
                        <Legend />
                        <Line type="monotone" dataKey="resumo.faturamento" stroke="#8884d8" name="Faturamento" />
                        <Line type="monotone" dataKey="resumo.lucro_liquido" stroke="#82ca9d" name="Lucro Líquido" />
                      </LineChart>
                    </ResponsiveContainer>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-700">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Data</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Faturamento</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Lucro Líquido</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Pedidos</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Unidades</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                {filteredDiario.map((dia: RelatorioDiario, index: number) => (
                            <tr key={index}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{dia.data}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {dia.resumo.faturamento.toFixed(2)}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {dia.resumo.lucro_liquido.toFixed(2)}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{dia.resumo.total_pedidos}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{dia.resumo.total_unidades}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                        </>
                      );
                    })()}
                  </Tabs.Content>

                  <Tabs.Content value="nicho" className="space-y-4">
                    <div className="mb-4">
                      <div className="relative max-w-md">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <input
                          type="text"
                          placeholder="Buscar por nicho..."
                          value={searchNicho}
                          onChange={(e) => setSearchNicho(e.target.value)}
                          className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
                        />
                      </div>
                    </div>
                    {(() => {
                      const filteredNicho = report.dados.relatorios.por_nicho.filter(nicho =>
                        nicho.nicho?.toLowerCase().includes(searchNicho.toLowerCase())
                      );
                      return (
                        <>
                          <ResponsiveContainer width="100%" height={400}>
                            <BarChart data={filteredNicho}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="nicho" />
                        <YAxis />
                        <Tooltip formatter={(value) => `R$ ${Number(value).toFixed(2)}`} />
                        <Legend />
                        <Bar dataKey="faturamento_total" fill="#8884d8" name="Faturamento" />
                        <Bar dataKey="lucro_liquido" fill="#82ca9d" name="Lucro Líquido" />
                      </BarChart>
                    </ResponsiveContainer>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-700">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Nicho</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Faturamento</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Lucro Líquido</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Pedidos</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Participação Faturamento</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                          {filteredNicho.map((nicho: PorNicho, index: number) => (
                            <tr key={index}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{nicho.nicho || 'Sem Nicho'}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {nicho.faturamento_total.toFixed(2)}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {nicho.lucro_liquido.toFixed(2)}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{nicho.total_pedidos}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{(nicho.participacao_faturamento * 100).toFixed(2)}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                        </>
                      );
                    })()}
                  </Tabs.Content>

                  <Tabs.Content value="sku" className="space-y-4">
                    <div className="mb-4">
                      <div className="relative max-w-md">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <input
                          type="text"
                          placeholder="Buscar por SKU ou nicho..."
                          value={searchSku}
                          onChange={(e) => setSearchSku(e.target.value)}
                          className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
                        />
                      </div>
                    </div>
                    <div className="overflow-x-auto">
                      {(() => {
                        const filteredSku = report.dados.relatorios.por_sku.filter(sku =>
                          sku.sku.toLowerCase().includes(searchSku.toLowerCase()) || sku.nicho?.toLowerCase().includes(searchSku.toLowerCase())
                        );
                        return (
                          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                            <thead className="bg-gray-50 dark:bg-gray-700">
                              <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">SKU</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Nicho</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Faturamento</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Lucro Líquido</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Pedidos</th>
                              </tr>
                            </thead>
                            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                              {filteredSku.map((sku: PorSKU, index: number) => (
                                <tr key={index}>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{sku.sku}</td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{sku.nicho || 'Sem Nicho'}</td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {sku.faturamento_total.toFixed(2)}</td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {sku.lucro_liquido.toFixed(2)}</td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{sku.total_pedidos}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        );
                      })()}
                    </div>
                  </Tabs.Content>

                  <Tabs.Content value="rankings" className="space-y-4">
                    <div>
                      <div className="mb-4">
                        <div className="relative max-w-md">
                          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                          <input
                            type="text"
                            placeholder="Buscar por SKU..."
                            value={searchTopSkus}
                            onChange={(e) => setSearchTopSkus(e.target.value)}
                            className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
                          />
                        </div>
                      </div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Top SKUs</h3>
                      <div className="overflow-x-auto">
                        {(() => {
                          const filteredTopSkus = report.dados.rankings.top_skus.filter(sku =>
                            sku.sku?.toLowerCase().includes(searchTopSkus.toLowerCase())
                          );
                          return (
                            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                              <thead className="bg-gray-50 dark:bg-gray-700">
                                <tr>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">SKU</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Lucro Líquido</th>
                                </tr>
                              </thead>
                              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                {filteredTopSkus.slice(0, 10).map((sku: Ranking, index: number) => (
                                  <tr key={index}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{sku.sku}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {sku.profit?.toFixed(2)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          );
                        })()}
                      </div>
                    </div>
                    <div>
                      <div className="mb-4">
                        <div className="relative max-w-md">
                          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                          <input
                            type="text"
                            placeholder="Buscar por anúncio..."
                            value={searchTopAds}
                            onChange={(e) => setSearchTopAds(e.target.value)}
                            className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
                          />
                        </div>
                      </div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Top Anúncios</h3>
                      <div className="overflow-x-auto">
                        {(() => {
                          const filteredTopAds = report.dados.rankings.top_ads.filter(ad =>
                            ad.ad?.toLowerCase().includes(searchTopAds.toLowerCase())
                          );
                          return (
                            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                              <thead className="bg-gray-50 dark:bg-gray-700">
                                <tr>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Anúncio</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Lucro Líquido</th>
                                </tr>
                              </thead>
                              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                {filteredTopAds.slice(0, 10).map((ad: Ranking, index: number) => (
                                  <tr key={index}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{ad.ad}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {ad.profit?.toFixed(2)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          );
                        })()}
                      </div>
                    </div>
                  </Tabs.Content>

                  <Tabs.Content value="skus-sem-nicho" className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">SKUs sem Nicho</h3>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-700">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">SKU</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                          {report.dados.kpis_gerais.skus_sem_nicho.map((sku: string, index: number) => (
                            <tr key={index}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{sku}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Tabs.Content>

                  <Tabs.Content value="pedidos" className="space-y-4">
                    <div className="mb-4">
                      <div className="relative max-w-md">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <input
                          type="text"
                          placeholder="Buscar por SKU, título ou ID do pedido..."
                          value={searchOrders}
                          onChange={(e) => setSearchOrders(e.target.value)}
                          className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
                        />
                      </div>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-700">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">ID Pedido</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">SKU</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Título</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Quantidade</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Valor Total</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Lucro Líquido</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Nicho</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                          {(() => {
                            const filteredOrders = orders.filter(order =>
                              order.sku?.toLowerCase().includes(searchOrders.toLowerCase()) ||
                              order.title?.toLowerCase().includes(searchOrders.toLowerCase()) ||
                              order.order_id?.toLowerCase().includes(searchOrders.toLowerCase())
                            );
                            const totalPagesOrders = Math.ceil(filteredOrders.length / itemsPerPageOrders);
                            const startIndexOrders = (currentPageOrders - 1) * itemsPerPageOrders;
                            const endIndexOrders = startIndexOrders + itemsPerPageOrders;
                            const paginatedOrders = filteredOrders.slice(startIndexOrders, endIndexOrders);

                            return paginatedOrders.map((order, index) => (
                              <tr key={index}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{order.order_id}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{order.sku}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{order.title}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{order.quantity}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {order.total_value?.toFixed(2)}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {order.profit?.toFixed(2)}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{order.nicho}</td>
                              </tr>
                            ));
                          })()}
                        </tbody>
                      </table>
                    </div>
                    {(() => {
                      const filteredOrders = orders.filter(order =>
                        order.sku?.toLowerCase().includes(searchOrders.toLowerCase()) ||
                        order.title?.toLowerCase().includes(searchOrders.toLowerCase()) ||
                        order.order_id?.toLowerCase().includes(searchOrders.toLowerCase())
                      );
                      const totalPagesOrders = Math.ceil(filteredOrders.length / itemsPerPageOrders);

                      const goToPageOrders = (page: number) => {
                        setCurrentPageOrders(page);
                      };

                      const goToNextPageOrders = () => {
                        if (currentPageOrders < totalPagesOrders) {
                          setCurrentPageOrders(currentPageOrders + 1);
                        }
                      };

                      const goToPrevPageOrders = () => {
                        if (currentPageOrders > 1) {
                          setCurrentPageOrders(currentPageOrders - 1);
                        }
                      };

                      return (
                        <div className="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 sm:px-6">
                          <div className="flex items-center">
                            <label htmlFor="itemsPerPageOrders" className="mr-2 text-sm text-gray-700 dark:text-gray-300">Itens por página:</label>
                            <select
                              id="itemsPerPageOrders"
                              value={itemsPerPageOrders}
                              onChange={(e) => setItemsPerPageOrders(Number(e.target.value))}
                              className="border border-gray-300 dark:border-gray-600 rounded-md px-2 py-1 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            >
                              <option value={10}>10</option>
                              <option value={25}>25</option>
                              <option value={50}>50</option>
                              <option value={100}>100</option>
                            </select>
                          </div>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={goToPrevPageOrders}
                              disabled={currentPageOrders === 1}
                              className="px-3 py-1 text-sm font-medium text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              Anterior
                            </button>

                            {/* Page numbers */}
                            {Array.from({ length: Math.min(5, totalPagesOrders) }, (_, i) => {
                              let pageNum;
                              if (totalPagesOrders <= 5) {
                                pageNum = i + 1;
                              } else if (currentPageOrders <= 3) {
                                pageNum = i + 1;
                              } else if (currentPageOrders >= totalPagesOrders - 2) {
                                pageNum = totalPagesOrders - 4 + i;
                              } else {
                                pageNum = currentPageOrders - 2 + i;
                              }

                              return (
                                <button
                                  key={pageNum}
                                  onClick={() => goToPageOrders(pageNum)}
                                  className={`px-3 py-1 text-sm font-medium rounded-md ${
                                    currentPageOrders === pageNum
                                      ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900 border border-blue-300 dark:border-blue-600'
                                      : 'text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                                  }`}
                                >
                                  {pageNum}
                                </button>
                              );
                            })}

                            <button
                              onClick={goToNextPageOrders}
                              disabled={currentPageOrders === totalPagesOrders}
                              className="px-3 py-1 text-sm font-medium text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              Próximo
                            </button>
                          </div>
                        </div>
                      );
                    })()}
                  </Tabs.Content>
                </Tabs.Root>
              ) : (
                <div className="text-center py-8">
                  <div className="text-red-500 dark:text-red-400">
                    {report.erro || 'Erro ao gerar relatório'}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        </main>
      </div>
    </div>
  );
}
