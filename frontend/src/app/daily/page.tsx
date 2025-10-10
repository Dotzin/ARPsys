'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'react-hot-toast';
import { ThemeToggle } from '../../components/ThemeToggle';
import { Sidebar } from '../../components/Sidebar';
import { LogOut, DollarSign, TrendingUp, ShoppingCart, Package, Calculator, Percent, Search } from 'lucide-react';
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

export default function DailyPage() {
  const [report, setReport] = useState<ReportData | null>(null);
  const [connected, setConnected] = useState(false);
  const [searchDiario, setSearchDiario] = useState('');
  const [searchNicho, setSearchNicho] = useState('');
  const [searchSku, setSearchSku] = useState('');
  const [searchTopSkus, setSearchTopSkus] = useState('');
  const [searchTopAds, setSearchTopAds] = useState('');
  const router = useRouter();

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/auth/login');
      return;
    }

    // Connect to WebSocket
    connectWebSocket(token);
  }, [router]);

  const connectWebSocket = (token: string) => {
    const ws = new WebSocket(`ws://localhost:8000/ws/relatorio_diario?token=${token}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      toast.success('Conectado ao relatório em tempo real');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);

        if (data.tipo === 'relatorio_diario_inicial' || data.tipo === 'relatorio_diario') {
          const reportData = data.dados;
          if (reportData.status === 'sucesso') {
            const transformed = {
              status: reportData.status,
              kpis_gerais: {
                faturamento_total: reportData.kpis_diarios?.faturamento || 0,
                lucro_liquido_total: reportData.kpis_diarios?.lucro_liquido || 0,
                total_pedidos: reportData.kpis_diarios?.total_pedidos || 0,
                total_unidades: reportData.kpis_diarios?.total_unidades || 0,
                ticket_medio: reportData.kpis_diarios?.ticket_medio || { pedido: 0, unidade: 0 },
                custos: reportData.kpis_diarios?.custos || { custo_total: 0, frete_total: 0, impostos_total: 0 },
                indices: { rentabilidade_media: 0, profitabilidade_media: 0 },
                skus_sem_nicho: []
              },
              relatorios: {
                diario: [{
                  data: reportData.dia,
                  resumo: {
                    faturamento: reportData.kpis_diarios?.faturamento || 0,
                    lucro_bruto: 0,
                    lucro_liquido: reportData.kpis_diarios?.lucro_liquido || 0,
                    total_pedidos: reportData.kpis_diarios?.total_pedidos || 0,
                    total_unidades: reportData.kpis_diarios?.total_unidades || 0,
                    ticket_medio: { pedido: 0, unidade: 0 }
                  },
                  nichos: (reportData.analise_por_nicho_dia || []).map((n: any) => ({
                    nicho: n.nicho,
                    faturamento: n.faturamento,
                    lucro_bruto: n.lucro_bruto,
                    profit: n.lucro_liquido,
                    total_pedidos: n.total_pedidos,
                    total_unidades: n.total_unidades
                  }))
                }],
                por_nicho: (reportData.analise_por_nicho_dia || []).map((n: any) => ({
                  nicho: n.nicho,
                  lucro_liquido: n.lucro_liquido,
                  lucro_bruto: n.lucro_bruto,
                  total_pedidos: n.total_pedidos,
                  total_unidades: n.total_unidades,
                  faturamento_total: n.faturamento,
                  participacao_faturamento: 0,
                  participacao_lucro: 0,
                  media_dia_valor: 0,
                  media_dia_unidades: 0
                })),
                por_sku: (reportData.por_sku_dia || []).map((s: any) => ({
                  sku: s.sku,
                  nicho: s.nicho,
                  faturamento_total: s.faturamento_total,
                  lucro_liquido: s.lucro_liquido,
                  total_pedidos: s.total_pedidos,
                  total_unidades: s.total_unidades
                }))
              },
              rankings: {
                top_skus: (reportData.rankings_diarios?.top_skus || []).map((s: any) => ({ sku: s.sku, profit: s.lucro_liquido })),
                top_ads: (reportData.rankings_diarios?.top_ads || []).map((a: any) => ({ ad: a.ad, profit: a.lucro_liquido }))
              }
            };
            setReport(transformed);
          } else {
            setReport({ status: reportData.status, erro: reportData.erro || 'Erro ao carregar relatório' });
          }
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      toast.error('Desconectado do relatório em tempo real');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      toast.error('Erro na conexão WebSocket');
    };

    return () => {
      ws.close();
    };
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    router.push('/auth/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Sidebar */}
      <div className="w-64 fixed h-full">
        <Sidebar currentPage="/daily" />
      </div>

      {/* Main Content */}
      <div className="flex-1 ml-64">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 flex justify-between items-center">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Relatório Diário em Tempo Real
              </h1>
              <div className={`ml-4 w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            </div>

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
          {/* Status */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                  Status da Conexão
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {connected ? 'Conectado ao servidor em tempo real' : 'Desconectado - tentando reconectar...'}
                </p>
              </div>
              <div className={`w-4 h-4 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            </div>
          </div>

          {/* Report */}
          {report ? (
            report.status === 'sucesso' ? (
              <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Relatório Diário em Tempo Real
                </h2>

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
                  </Tabs.List>

                  <Tabs.Content value="kpis" className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                        <DollarSign className="h-6 w-6 text-blue-600 mb-2" />
                        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Faturamento Total</h3>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">R$ {(report.dados || report)?.kpis_gerais?.faturamento_total?.toFixed(2) || '0.00'}</p>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                        <TrendingUp className="h-6 w-6 text-green-600 mb-2" />
                        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Lucro Líquido Total</h3>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">R$ {(report.dados || report)?.kpis_gerais?.lucro_liquido_total?.toFixed(2) || '0.00'}</p>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                        <ShoppingCart className="h-6 w-6 text-purple-600 mb-2" />
                        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Pedidos</h3>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">{(report.dados || report)?.kpis_gerais?.total_pedidos || 0}</p>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                        <Package className="h-6 w-6 text-indigo-600 mb-2" />
                        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Unidades</h3>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">{(report.dados || report)?.kpis_gerais?.total_unidades || 0}</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                        <Calculator className="h-6 w-6 text-orange-600 mb-2" />
                        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Ticket Médio</h3>
                        <p className="text-lg text-gray-900 dark:text-white">Pedido: R$ {(report.dados || report)?.kpis_gerais?.ticket_medio?.pedido?.toFixed(2) || '0.00'}</p>
                        <p className="text-lg text-gray-900 dark:text-white">Unidade: R$ {(report.dados || report)?.kpis_gerais?.ticket_medio?.unidade?.toFixed(2) || '0.00'}</p>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                        <Percent className="h-6 w-6 text-red-600 mb-2" />
                        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Custos Totais</h3>
                        <p className="text-lg text-gray-900 dark:text-white">Custo: R$ {(report.dados || report)?.kpis_gerais?.custos?.custo_total?.toFixed(2) || '0.00'}</p>
                        <p className="text-lg text-gray-900 dark:text-white">Frete: R$ {(report.dados || report)?.kpis_gerais?.custos?.frete_total?.toFixed(2) || '0.00'}</p>
                        <p className="text-lg text-gray-900 dark:text-white">Impostos: R$ {(report.dados || report)?.kpis_gerais?.custos?.impostos_total?.toFixed(2) || '0.00'}</p>
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
                      const filteredDiario = ((report.dados || report)?.relatorios?.diario || []).filter((dia: RelatorioDiario) =>
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
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {dia.resumo?.faturamento?.toFixed(2) || '0.00'}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {dia.resumo?.lucro_liquido?.toFixed(2) || '0.00'}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{dia.resumo?.total_pedidos || 0}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{dia.resumo?.total_unidades || 0}</td>
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
                      const filteredNicho = ((report.dados || report)?.relatorios?.por_nicho || []).filter((nicho: PorNicho) =>
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
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {nicho.faturamento_total?.toFixed(2) || '0.00'}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {nicho.lucro_liquido?.toFixed(2) || '0.00'}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{nicho.total_pedidos || 0}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{((nicho.participacao_faturamento || 0) * 100).toFixed(2)}%</td>
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
                        const filteredSku = ((report.dados || report)?.relatorios?.por_sku || []).filter((sku: PorSKU) =>
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
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {sku.faturamento_total?.toFixed(2) || '0.00'}</td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {sku.lucro_liquido?.toFixed(2) || '0.00'}</td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{sku.total_pedidos || 0}</td>
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
                          const filteredTopSkus = ((report.dados || report)?.rankings?.top_skus || []).filter((sku: Ranking) =>
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
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{sku.sku || 'N/A'}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {sku.profit?.toFixed(2) || '0.00'}</td>
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
                          const filteredTopAds = ((report.dados || report)?.rankings?.top_ads || []).filter((ad: Ranking) =>
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
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{ad.ad || 'N/A'}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">R$ {ad.profit?.toFixed(2) || '0.00'}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          );
                        })()}
                      </div>
                    </div>
                  </Tabs.Content>
                </Tabs.Root>
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <div className="text-center py-8">
                  <div className="text-red-500 dark:text-red-400">
                    {report.status === 'sem_dados' ? 'Nenhum dado encontrado para hoje' : (report.erro || 'Erro ao carregar relatório')}
                  </div>
                </div>
              </div>
            )
          ) : (
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <div className="text-center py-8">
                <div className="text-gray-500 dark:text-gray-400">
                  Aguardando dados do relatório...
                </div>
              </div>
            </div>
          )}
        </div>
        </main>
      </div>
    </div>
  );
}
