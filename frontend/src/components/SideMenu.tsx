import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Menu, X, LayoutDashboard, HardDrive, LogOut, Tag, FileSpreadsheet } from 'lucide-react';
import { ManageTagsModal } from './ManageTagsModal';

export const SideMenu: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isTagsModalOpen, setIsTagsModalOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const menuRef = useRef<HTMLDivElement>(null);

  const toggleMenu = () => setIsOpen(!isOpen);
  const closeMenu = () => setIsOpen(false);

  // Close menu on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        closeMenu();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node) && isOpen) {
        closeMenu();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const handleNavigate = (path: string) => {
    closeMenu();
    navigate(path);
  };

  const handleLogout = async () => {
    closeMenu();
    await logout();
    navigate('/login');
  };

  const isTecnico = user?.role === 'tecnico';
  const isDashboardActive = location.pathname === '/dashboard';
  const isEquipamentosActive = location.pathname.startsWith('/equipamentos');
  const isImportacaoActive = location.pathname === '/importar' || location.pathname === '/import';

  const userInitial = user?.email ? user.email.charAt(0).toUpperCase() : 'U';

  return (
    <>
      {/* Botão de alternância do menu */}
      <button
        onClick={toggleMenu}
        data-testid="toggle-menu-btn"
        aria-label="Toggle Menu"
        className="p-2 rounded-md bg-[#1E1E1E] hover:bg-[#333333] border border-[#333333] text-[#E0E0E0] hover:text-white transition-colors flex items-center justify-center cursor-pointer shadow-sm"
      >
        <Menu className="w-4 h-4" />
      </button>

      {/* Overlay escuro */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 transition-opacity"
          aria-hidden="true"
        />
      )}

      {/* Drawer do Menu Lateral */}
      <aside
        ref={menuRef}
        className={`fixed top-0 bottom-0 left-0 h-screen min-h-screen w-72 bg-[#1E1E1E] border-r border-[#333333] text-[#E0E0E0] shadow-2xl z-50 flex flex-col justify-between transform transition-transform duration-200 ease-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Sidebar Menu"
      >
        {/* Cabeçalho do Menu */}
        <div className="p-5 border-b border-[#333333]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[#121212] border border-[#333333] flex items-center justify-center text-white shrink-0">
                <HardDrive className="w-4 h-4" />
              </div>
              <div className="min-w-0">
                <h2 className="text-sm font-semibold text-white tracking-tight truncate">
                  Gestão de Patrimônio
                </h2>
                <p className="text-[10px] text-[#9E9E9E] font-mono uppercase tracking-wider">
                  Menu Principal
                </p>
              </div>
            </div>

            <button
              onClick={closeMenu}
              aria-label="Fechar menu"
              className="p-1 rounded-md text-[#9E9E9E] hover:text-white hover:bg-[#333333] transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Itens de Navegação */}
        <div className="flex-1 p-4 space-y-1.5 overflow-y-auto">
          <button
            onClick={() => handleNavigate('/dashboard')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer text-left ${
              isDashboardActive
                ? 'border-l-2 border-white bg-white/5 text-white font-semibold'
                : 'text-[#9E9E9E] hover:text-white hover:bg-white/5'
            }`}
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Dashboard</span>
          </button>

          {isTecnico && (
            <>
              <button
                onClick={() => handleNavigate('/equipamentos')}
                data-testid="patrimonio-menu-item"
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer text-left ${
                  isEquipamentosActive
                    ? 'border-l-2 border-white bg-white/5 text-white font-semibold'
                    : 'text-[#9E9E9E] hover:text-white hover:bg-white/5'
                }`}
              >
                <HardDrive className="w-4 h-4" />
                <span>Patrimônio</span>
              </button>

              <button
                onClick={() => handleNavigate('/importar')}
                data-testid="importar-menu-item"
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer text-left ${
                  isImportacaoActive
                    ? 'border-l-2 border-white bg-white/5 text-white font-semibold'
                    : 'text-[#9E9E9E] hover:text-white hover:bg-white/5'
                }`}
              >
                <FileSpreadsheet className="w-4 h-4" />
                <span>Importar Planilha</span>
              </button>

              <button
                onClick={() => {
                  closeMenu();
                  setIsTagsModalOpen(true);
                }}
                data-testid="manage-tags-menu-item"
                className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer text-left text-[#9E9E9E] hover:text-white hover:bg-white/5"
              >
                <Tag className="w-4 h-4" />
                <span>Gerenciar Tags</span>
              </button>
            </>
          )}
        </div>

        {/* Rodapé com Perfil do Usuário e Logout */}
        <div className="p-4 border-t border-[#333333] space-y-3">
          <div className="bg-[#121212] border border-[#333333] p-3 rounded-lg flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#2A2A2A] border border-[#333333] flex items-center justify-center font-semibold text-xs text-white">
              {userInitial}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-white truncate font-mono">
                {user?.email || 'Usuário'}
              </p>
              <span className="inline-block mt-0.5 px-1.5 py-0.2 rounded bg-[#2A2A2A] text-[#9E9E9E] font-semibold uppercase text-[9px] tracking-wider font-mono">
                {user?.role || 'colaborador'}
              </span>
            </div>
          </div>

          <button
            onClick={handleLogout}
            aria-label="Encerrar sessão"
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-[#121212] hover:bg-red-500/10 border border-[#333333] hover:border-red-500/30 text-xs text-red-400 rounded-lg transition-colors font-medium cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Encerrar sessão</span>
          </button>
        </div>
      </aside>

      {/* Modal de Gerenciamento de Tags */}
      <ManageTagsModal
        isOpen={isTagsModalOpen}
        onClose={() => setIsTagsModalOpen(false)}
      />
    </>
  );
};

