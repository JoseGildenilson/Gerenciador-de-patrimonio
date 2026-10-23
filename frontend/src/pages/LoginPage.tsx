import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { HardDrive } from 'lucide-react';
import { LoginForm } from '../components/LoginForm';
import { useAuth } from '../hooks/useAuth';

export const LoginPage: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, loading, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center text-zinc-400">
        <div className="flex flex-col items-center gap-3">
          <div className="w-6 h-6 border-2 border-zinc-700 border-t-zinc-200 rounded-full animate-spin" />
          <p className="text-xs font-medium text-zinc-500">Iniciando sistema...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col justify-center items-center p-4 selection:bg-zinc-800 selection:text-zinc-100">
      <div className="w-full max-w-sm z-10 animate-fade-in-scale my-auto">
        {/* Header da Marca */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-200 mb-3 shadow-card-subtle">
            <HardDrive className="w-5 h-5" />
          </div>
          <h1 className="text-lg font-bold text-zinc-100 tracking-tight">
            Gestão de Patrimônio
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            Controle de inventário e suporte técnico
          </p>
        </div>

        {/* Card do Formulário de Login */}
        <div className="bg-zinc-900/90 border border-zinc-800/90 rounded-2xl p-6 shadow-card-elevated">
          <LoginForm onSuccess={() => navigate('/dashboard', { replace: true })} />
        </div>

        {/* Footer Informativo */}
        <p className="text-center text-[11px] text-zinc-500 mt-6 tracking-wide">
          Acesso restrito a técnicos e colaboradores autorizados.
        </p>
      </div>
    </div>
  );
};
