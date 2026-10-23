import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { SideMenu } from '../components/SideMenu';
import { HardDrive, ArrowRight, Shield } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const isTecnico = user?.role === 'tecnico';

  return (
    <div className="min-h-screen bg-[#121212] text-[#E0E0E0] font-sans antialiased flex flex-col selection:bg-zinc-800 selection:text-white">
      {/* Header do Dashboard */}
      <header className="border-b border-[#333333] bg-[#1E1E1E] px-6 py-4 flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-4">
          <SideMenu />
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#121212] border border-[#333333] flex items-center justify-center text-white shrink-0">
              <HardDrive className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-white leading-tight tracking-tight">Gestão de Patrimônio</h1>
              <p className="text-[10px] text-[#9E9E9E] font-mono uppercase tracking-wider">Dashboard de Controle</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-[#121212] border border-[#333333] rounded-lg text-xs">
            <span className="text-[#E0E0E0] font-medium font-mono">
              {user?.email ? user.email.split('@')[0] : 'Usuário'}
            </span>
            <span className="px-1.5 py-0.2 rounded bg-[#2A2A2A] text-[#9E9E9E] font-semibold uppercase text-[9px] tracking-wider font-mono">
              {user?.role}
            </span>
          </div>
        </div>
      </header>

      {/* Conteúdo Principal */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Banner de Boas-Vindas */}
        <div className="p-6 rounded-xl bg-[#1E1E1E] border border-[#333333] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 animate-fade-in">
          <div>
            <h2 className="text-lg md:text-xl font-bold text-white tracking-tight">
              Visão Geral do Sistema
            </h2>
            <p className="text-xs text-[#9E9E9E] mt-1">
              {isTecnico
                ? 'Painel central de controle de patrimônio e inventário de equipamentos corporativos.'
                : 'Acompanhamento do inventário e recursos corporativos.'}
            </p>
          </div>
          <div className="shrink-0">
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#121212] border border-[#333333] text-xs text-[#E0E0E0] font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Sistema Operacional
            </span>
          </div>
        </div>

        {/* Módulos do Sistema */}
        {isTecnico ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-in">
            {/* Card Principal: Gestão de Equipamentos */}
            <div
              onClick={() => navigate('/equipamentos')}
              data-testid="equipamentos-card"
              className="p-6 rounded-xl bg-[#1E1E1E] border border-[#333333] hover:border-gray-500 transition-colors shadow-sm flex flex-col justify-between cursor-pointer group space-y-6"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold text-[#9E9E9E] uppercase tracking-wider font-mono">
                      Módulo Principal
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white group-hover:text-gray-100 transition-colors">
                    Equipamentos
                  </h3>
                  <p className="text-xs text-[#9E9E9E] leading-relaxed">
                    Controle de inventário de equipamentos, consulta de patrimônio, registros de movimentação e históricos de intervenção técnica.
                  </p>
                </div>

                <div className="w-10 h-10 rounded-lg bg-[#121212] border border-[#333333] flex items-center justify-center text-[#E0E0E0] group-hover:text-white group-hover:border-gray-400 transition-colors shrink-0">
                  <HardDrive className="w-5 h-5" />
                </div>
              </div>

              <div className="pt-4 border-t border-[#333333] flex items-center justify-between text-xs text-[#E0E0E0] font-medium group-hover:text-white transition-colors">
                <span>Acessar Inventário</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>

            {/* Card Secundário: Segurança & Rastreabilidade */}
            <div className="p-6 rounded-xl bg-[#1E1E1E] border border-[#333333] shadow-sm flex flex-col justify-between space-y-6">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1.5">
                  <span className="text-[11px] font-bold text-[#9E9E9E] uppercase tracking-wider font-mono">
                    Auditoria Técnica
                  </span>
                  <h3 className="text-lg font-bold text-white">
                    Rastreabilidade &amp; Conformidade
                  </h3>
                  <p className="text-xs text-[#9E9E9E] leading-relaxed">
                    Preservação de registros com histórico imutável de movimentações, trocas de peças e manutenções preventivas e corretivas.
                  </p>
                </div>

                <div className="w-10 h-10 rounded-lg bg-[#121212] border border-[#333333] flex items-center justify-center text-[#E0E0E0] shrink-0">
                  <Shield className="w-5 h-5" />
                </div>
              </div>

              <div className="pt-4 border-t border-[#333333] flex items-center justify-between text-xs text-[#9E9E9E] font-mono">
                <span>Controle Ativo</span>
                <span className="text-emerald-400">Verificado</span>
              </div>
            </div>
          </div>
        ) : (
          /* Visão do Colaborador */
          <div className="p-8 rounded-xl bg-[#1E1E1E] border border-[#333333] text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-[#121212] border border-[#333333] flex items-center justify-center text-[#E0E0E0] mx-auto">
              <HardDrive className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-white">Portal de Ativos Corporativos</h3>
            <p className="text-xs text-[#9E9E9E] max-w-md mx-auto leading-relaxed">
              Você está conectado como colaborador. Consulte os recursos corporativos ou contate o suporte técnico para alterações de patrimônio.
            </p>
          </div>
        )}
      </main>
    </div>
  );
};
