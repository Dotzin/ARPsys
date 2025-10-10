import { useRouter } from 'next/navigation';
import { BarChart3, FileText, Home, Settings, Package } from 'lucide-react';

interface SidebarProps {
  currentPage: string;
}

export function Sidebar({ currentPage }: SidebarProps) {
  const router = useRouter();

  const menuItems = [
    { name: 'Dashboard', path: '/dashboard', icon: Home },
    { name: 'Pedidos', path: '/orders', icon: Package },
    { name: 'Relatórios', path: '/reports', icon: FileText },
    { name: 'Relatório Diário', path: '/daily', icon: BarChart3 },
    { name: 'Configurações', path: '/settings', icon: Settings },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 shadow-lg h-full">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">ARPsys</h1>
      </div>
      <nav className="px-4">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.path;
            return (
              <li key={item.path}>
                <button
                  onClick={() => router.push(item.path)}
                  className={`w-full flex items-center px-4 py-3 text-left rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  {item.name}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}
