import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary capturou um erro não tratado:', error, errorInfo);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#121212] flex items-center justify-center p-6 text-[#E0E0E0]">
          <div className="max-w-md w-full bg-[#1E1E1E] border border-red-500/30 rounded-xl p-6 text-center shadow-xl space-y-4">
            <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 mx-auto flex items-center justify-center">
              <AlertTriangle className="w-6 h-6" />
            </div>

            <div className="space-y-1.5">
              <h2 className="text-base font-semibold text-white">
                {this.props.fallbackTitle || 'Ocorreu um erro ao carregar este módulo'}
              </h2>
              <p className="text-xs text-[#9E9E9E] leading-relaxed">
                Um erro inesperado de renderização foi interceptado. Você pode tentar recarregar a tela ou voltar ao início.
              </p>
            </div>

            {this.state.error?.message && (
              <div className="p-3 bg-[#121212] border border-[#333333] rounded-lg text-left overflow-x-auto text-[11px] font-mono text-red-300">
                {this.state.error.message}
              </div>
            )}

            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={this.handleRetry}
                className="flex items-center gap-2 px-4 py-2 bg-white text-[#121212] rounded-lg text-xs font-semibold hover:bg-gray-200 transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Recarregar Página</span>
              </button>
              <a
                href="/dashboard"
                className="px-4 py-2 bg-[#121212] border border-[#333333] text-[#E0E0E0] rounded-lg text-xs font-semibold hover:bg-[#2A2A2A] transition-colors"
              >
                Ir para o Dashboard
              </a>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
