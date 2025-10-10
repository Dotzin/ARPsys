'use client';

import { useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { ordersApi } from '../../lib/api';
import { toast } from 'react-hot-toast';
import { Download, Search, LogOut, ChevronLeft, ChevronRight } from 'lucide-react';
import { ThemeToggle } from '../../components/ThemeToggle';
import { Sidebar } from '../../components/Sidebar';

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

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [filteredOrders, setFilteredOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(50);
  const [searchTerm, setSearchTerm] = useState('');

  const router = useRouter();

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/auth/login');
      return;
    }

    fetchOrders();
  }, [router]);

  // Reset to first page when search term or items per page changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, itemsPerPage]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const response = await ordersApi.getOrders();
      setOrders(response.pedidos || []);
      setFilteredOrders(response.pedidos || []);
      setCurrentPage(1);
    } catch (error) {
      console.error('Error fetching orders:', error);
      toast.error('Erro ao carregar pedidos');
    } finally {
      setLoading(false);
    }
  };

  const handleFilter = async () => {
    if (!dataInicio || !dataFim) {
      toast.error('Selecione data início e fim');
      return;
    }

    setLoading(true);
    try {
      const response = await ordersApi.getOrdersByPeriod(dataInicio, dataFim);
      setFilteredOrders(response.pedidos || []);
      setCurrentPage(1);
    } catch (error) {
      console.error('Error filtering orders:', error);
      toast.error('Erro ao filtrar pedidos');
    } finally {
      setLoading(false);
    }
  };

  const handleClearFilter = () => {
    setDataInicio('');
    setDataFim('');
    setFilteredOrders(orders);
    setCurrentPage(1);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    router.push('/auth/login');
  };

  // Search and filter logic
  const searchedAndFilteredOrders = useMemo(() => {
    let result = filteredOrders;

    // Apply search filter
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      result = result.filter(order =>
        order.order_id?.toLowerCase().includes(searchLower) ||
        order.sku?.toLowerCase().includes(searchLower) ||
        order.title?.toLowerCase().includes(searchLower) ||
        order.nicho?.toLowerCase().includes(searchLower) ||
        order.status?.toLowerCase().includes(searchLower)
      );
    }

    return result;
  }, [filteredOrders, searchTerm]);

  // Pagination logic
  const totalPages = Math.ceil(searchedAndFilteredOrders.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentOrders = searchedAndFilteredOrders.slice(startIndex, endIndex);

  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  const goToPreviousPage = () => {
    goToPage(currentPage - 1);
  };

  const goToNextPage = () => {
    goToPage(currentPage + 1);
  };

  const handleItemsPerPageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setItemsPerPage(Number(e.target.value));
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Sidebar */}
      <div className="w-64 fixed h-full">
        <Sidebar currentPage="/orders" />
      </div>

      {/* Main Content */}
      <div className="flex-1 ml-64">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Pedidos
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
            {/* Filter */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Filtrar Pedidos
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
                    onClick={handleFilter}
                    className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors flex items-center justify-center"
                    disabled={loading}
                  >
                    <Search className="h-4 w-4 mr-2" />
                    Filtrar
                  </button>
                </div>

                <div className="flex items-end">
                  <button
                    onClick={handleClearFilter}
                    className="w-full px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
                  >
                    Limpar Filtro
                  </button>
                </div>
              </div>
            </div>

            {/* Search and Items per Page */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
                <div className="flex-1 max-w-md">
                  <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Pesquisar Pedidos
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Search className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      type="text"
                      id="search"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      placeholder="Buscar por ID, SKU, título, nicho ou status..."
                      className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <label htmlFor="items-per-page" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Itens por página:
                  </label>
                  <select
                    id="items-per-page"
                    value={itemsPerPage}
                    onChange={handleItemsPerPageChange}
                    className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Orders Table */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                  Pedidos ({searchedAndFilteredOrders.length})
                  {searchTerm && <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">(filtrado)</span>}
                </h2>
                {searchedAndFilteredOrders.length > 0 && (
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Página {currentPage} de {totalPages}
                  </div>
                )}
              </div>

              {loading ? (
                <div className="text-center py-8">
                  <div className="text-gray-500 dark:text-gray-400">Carregando...</div>
                </div>
              ) : searchedAndFilteredOrders.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-500 dark:text-gray-400">
                    {searchTerm ? 'Nenhum pedido encontrado para a busca' : 'Nenhum pedido encontrado'}
                  </div>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                      <thead className="bg-gray-50 dark:bg-gray-700">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            ID Pedido
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            SKU
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Título
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Quantidade
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Valor Total
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Lucro Líquido
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Nicho
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Data Pagamento
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {currentOrders.map((order, index) => (
                          <tr key={order.id || index}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {order.order_id}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {order.sku}
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-900 dark:text-white max-w-xs truncate" title={order.title}>
                              {order.title}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {order.quantity}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              R$ {order.total_value?.toFixed(2)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              R$ {order.profit?.toFixed(2)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {order.status}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {order.nicho || 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {order.payment_date ? new Date(order.payment_date).toLocaleDateString('pt-BR') : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="flex items-center justify-between px-6 py-3 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
                      <div className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                        Mostrando {startIndex + 1} a {Math.min(endIndex, searchedAndFilteredOrders.length)} de {searchedAndFilteredOrders.length} resultados
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={goToPreviousPage}
                          disabled={currentPage === 1}
                          className="px-3 py-1 text-sm font-medium text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <ChevronLeft className="h-4 w-4" />
                        </button>

                        {/* Page numbers */}
                        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                          let pageNum;
                          if (totalPages <= 5) {
                            pageNum = i + 1;
                          } else if (currentPage <= 3) {
                            pageNum = i + 1;
                          } else if (currentPage >= totalPages - 2) {
                            pageNum = totalPages - 4 + i;
                          } else {
                            pageNum = currentPage - 2 + i;
                          }

                          return (
                            <button
                              key={pageNum}
                              onClick={() => goToPage(pageNum)}
                              className={`px-3 py-1 text-sm font-medium rounded-md ${
                                currentPage === pageNum
                                  ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900 border border-blue-300 dark:border-blue-600'
                                  : 'text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                              }`}
                            >
                              {pageNum}
                            </button>
                          );
                        })}

                        <button
                          onClick={goToNextPage}
                          disabled={currentPage === totalPages}
                          className="px-3 py-1 text-sm font-medium text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
