'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import { api, integrationsApi, skuNichoApi } from '../../lib/api';
import { toast } from 'react-hot-toast';
import { Upload, Download, Plus, Settings, X, LogOut } from 'lucide-react';
import { ThemeToggle } from '../../components/ThemeToggle';
import { Sidebar } from '../../components/Sidebar';

interface Integration {
  id: string;
  name: string;
  type: string;
  config: Record<string, unknown>;
  active: boolean;
}

interface SkuNicho {
  sku: string;
  nicho: string;
}

export default function SettingsPage() {
  const [user, setUser] = useState(null);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [skuNichos, setSkuNichos] = useState<SkuNicho[]>([]);
  const [newSku, setNewSku] = useState('');
  const [newNicho, setNewNicho] = useState('');

  const [loading, setLoading] = useState(false);
  const [showIntegrationModal, setShowIntegrationModal] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<string>('');
  const [sessionId, setSessionId] = useState('');
  const router = useRouter();


  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/auth/login');
      return;
    }

    // Fetch integrations and SKU niches
    fetchData();
  }, [router]);

  const fetchData = async () => {
    try {
      const [integrationsRes, skuNichosRes] = await Promise.all([
        integrationsApi.getIntegrations(),
        skuNichoApi.getSkuNichos(),
      ]);
      setIntegrations(integrationsRes.data);
      setSkuNichos(skuNichosRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Erro ao carregar dados');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    router.push('/auth/login');
  };

  const handleIntegrationToggle = async (integration: Integration) => {
    try {
      await integrationsApi.updateIntegration(integration.id, {
        active: !integration.active,
      });
      setIntegrations(integrations.map(int =>
        int.id === integration.id ? { ...int, active: !int.active } : int
      ));
      toast.success('Integração atualizada com sucesso');
    } catch (error) {
      console.error('Error updating integration:', error);
      toast.error('Erro ao atualizar integração');
    }
  };

  const handleAddSkuNicho = async () => {
    if (!newSku || !newNicho) {
      toast.error('Preencha todos os campos');
      return;
    }

    try {
      await skuNichoApi.createSkuNicho({
        sku: newSku,
        nicho: newNicho,
      });
      setNewSku('');
      setNewNicho('');
      fetchData();
      toast.success('SKU/Nicho adicionado com sucesso');
    } catch (error) {
      console.error('Error adding SKU/Nicho:', error);
      toast.error('Erro ao adicionar SKU/Nicho');
    }
  };

  const handleBulkUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.xlsx')) {
      toast.error('Apenas arquivos XLSX são aceitos');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    try {
      await skuNichoApi.bulkUpload(file);
      fetchData();
      toast.success('Upload em massa realizado com sucesso');
    } catch (error) {
      console.error('Error uploading file:', error);
      toast.error('Erro no upload em massa');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const blob = await skuNichoApi.downloadTemplate();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', 'template_sku_nicho.xlsx');
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success('Template baixado com sucesso');
    } catch (error) {
      console.error('Error downloading template:', error);
      toast.error('Erro ao baixar template');
    }
  };

  const handleAddIntegration = async () => {
    if (!selectedIntegration || !sessionId.trim()) {
      toast.error('Selecione uma integração e forneça o Session ID');
      return;
    }

    try {
      if (selectedIntegration === 'arpcommerce') {
        await api.post('/integrations/arpcommerce', {
          token_value: sessionId,
        });
        toast.success('Integração ARPCommerce adicionada com sucesso');
      }
      setShowIntegrationModal(false);
      setSelectedIntegration('');
      setSessionId('');
      fetchData();
    } catch (error) {
      console.error('Error adding integration:', error);
      toast.error('Erro ao adicionar integração');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Sidebar */}
      <div className="w-64 fixed h-full">
        <Sidebar currentPage="/settings" />
      </div>

      {/* Main Content */}
      <div className="flex-1 ml-64">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Configurações
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
          {/* Theme Toggle */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                  Tema da Interface
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Escolha entre modo claro, escuro ou sistema
                </p>
              </div>
              <ThemeToggle />
            </div>
          </div>

          {/* Integrations */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 relative pb-20">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Integrações
            </h2>

            <div className="space-y-4">
              {integrations.map((integration) => (
                <div key={integration.id} className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                      {integration.name}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Tipo: {integration.type}
                    </p>
                  </div>
                  <button
                    onClick={() => handleIntegrationToggle(integration)}
                    className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                      integration.active
                        ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                    }`}
                  >
                    {integration.active ? 'Ativo' : 'Inativo'}
                  </button>
                </div>
              ))}

              {integrations.length === 0 && (
                <div className="text-center py-8">
                  <Settings className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                    Nenhuma integração configurada
                  </h3>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Configure integrações para sincronizar dados automaticamente.
                  </p>
                </div>
              )}
            </div>

            {/* Floating Action Button */}
            <button
              onClick={() => setShowIntegrationModal(true)}
              className="absolute bottom-6 right-6 bg-burgundy hover:bg-burgundy-dark dark:bg-burgundy-dark dark:hover:bg-burgundy text-white p-4 rounded-full shadow-lg transition-colors duration-200 z-50"
              title="Adicionar Integração"
            >
              <Plus className="h-6 w-6" />
            </button>
          </div>

          {/* SKU Niche Management */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Gerenciamento de SKU/Nicho
            </h2>

            {/* Individual Add */}
            <div className="mb-6">
              <h3 className="text-md font-medium text-gray-900 dark:text-white mb-3">
                Adicionar Individualmente
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <input
                  type="text"
                  placeholder="SKU"
                  value={newSku}
                  onChange={(e) => setNewSku(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-burgundy focus:border-burgundy dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
                <input
                  type="text"
                  placeholder="Nicho"
                  value={newNicho}
                  onChange={(e) => setNewNicho(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-burgundy focus:border-burgundy dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
                <button
                  onClick={handleAddSkuNicho}
                  className="px-4 py-2 text-sm font-medium text-white bg-burgundy hover:bg-burgundy-dark rounded-md transition-colors flex items-center justify-center"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Adicionar
                </button>
              </div>
            </div>

            {/* Bulk Upload */}
            <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
              <h3 className="text-md font-medium text-gray-900 dark:text-white mb-3">
                Upload em Massa
              </h3>
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleDownloadTemplate}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors flex items-center"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Baixar Modelo
                </button>
                <div className="relative">
                  <input
                    type="file"
                    accept=".xlsx"
                    onChange={handleBulkUpload}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    disabled={loading}
                  />
                  <button
                    className="px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md transition-colors flex items-center disabled:opacity-50"
                    disabled={loading}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    {loading ? 'Enviando...' : 'Upload XLSX'}
                  </button>
                </div>
              </div>
              <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                Faça upload de um arquivo XLSX com as colunas: sku, nicho
              </p>
            </div>

            {/* SKU Niche List */}
            <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
              <h3 className="text-md font-medium text-gray-900 dark:text-white mb-3">
                SKUs/Nichos Cadastrados ({skuNichos?.length || 0})
              </h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        SKU
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Nicho
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {skuNichos && skuNichos.map((item, index) => (
                      <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {item.sku}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {item.nicho}
                      </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
        </main>
      </div>

      {/* Integration Modal */}
      {showIntegrationModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Adicionar Integração
              </h3>
              <button
                onClick={() => setShowIntegrationModal(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Tipo de Integração
                </label>
                <select
                  value={selectedIntegration}
                  onChange={(e) => setSelectedIntegration(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-burgundy focus:border-burgundy dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                >
                  <option value="">Selecione uma integração</option>
                  <option value="arpcommerce">ARPCommerce</option>
                </select>
              </div>

              {selectedIntegration === 'arpcommerce' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Session ID
                  </label>
                  <input
                    type="text"
                    value={sessionId}
                    onChange={(e) => setSessionId(e.target.value)}
                    placeholder="Cole o session ID do ARPCommerce"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-burgundy focus:border-burgundy dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    O session ID pode ser encontrado nos cookies do navegador no site do ARPCommerce
                  </p>
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  onClick={() => setShowIntegrationModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleAddIntegration}
                  className="px-4 py-2 text-sm font-medium text-white bg-burgundy hover:bg-burgundy-dark rounded-md transition-colors flex items-center"
                >
                  <Plus className="h-4 w-4 mr-2 text-gray-900 dark:text-white" />
                  Adicionar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
