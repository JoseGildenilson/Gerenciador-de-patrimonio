import React, { useState } from 'react';
import { Mail, Lock, Eye, EyeOff, Loader2, LogIn } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { AlertBanner } from './AlertBanner';

interface LoginFormProps {
  onSuccess?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const { login, error, rateLimitBlocked, clearError } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});

  const validate = (): boolean => {
    const errors: { email?: string; password?: string } = {};

    if (!email.trim()) {
      errors.email = 'Email é obrigatório.';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      errors.email = 'Por favor, insira um formato de email válido.';
    }

    if (!password) {
      errors.password = 'Senha é obrigatória.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    setIsSubmitting(true);
    try {
      await login({ email, password });
      if (onSuccess) {
        onSuccess();
      }
    } catch {
      // Erros genéricos de 401 e 429 são gerenciados pelo AuthContext
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      {error && (
        <AlertBanner
          message={error}
          isRateLimit={rateLimitBlocked}
          onClose={clearError}
        />
      )}

      {/* Campo Email */}
      <div className="space-y-1.5">
        <label htmlFor="email" className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
          Endereço de Email
        </label>
        <div className="relative group">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500 group-focus-within:text-zinc-300 transition-colors">
            <Mail className="w-4 h-4" />
          </div>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: undefined });
            }}
            disabled={isSubmitting}
            placeholder="tecnico@empresa.com"
            className={`w-full pl-9 pr-3 py-2 bg-zinc-950 border rounded-xl text-xs text-zinc-100 placeholder-zinc-500 outline-none transition-all ${
              fieldErrors.email
                ? 'border-red-500/70 focus:border-red-500'
                : 'border-zinc-800 focus:border-zinc-500'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          />
        </div>
        {fieldErrors.email && (
          <p className="text-[11px] text-red-400 font-medium pl-0.5">{fieldErrors.email}</p>
        )}
      </div>

      {/* Campo Senha */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label htmlFor="password" className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
            Senha
          </label>
        </div>
        <div className="relative group">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500 group-focus-within:text-zinc-300 transition-colors">
            <Lock className="w-4 h-4" />
          </div>
          <input
            id="password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: undefined });
            }}
            disabled={isSubmitting}
            placeholder="••••••••••••"
            className={`w-full pl-9 pr-10 py-2 bg-zinc-950 border rounded-xl text-xs text-zinc-100 placeholder-zinc-500 outline-none transition-all ${
              fieldErrors.password
                ? 'border-red-500/70 focus:border-red-500'
                : 'border-zinc-800 focus:border-zinc-500'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            disabled={isSubmitting}
            aria-label={showPassword ? 'Ocultar senha' : 'Exibir senha'}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-zinc-500 hover:text-zinc-300 focus:outline-none transition-colors cursor-pointer"
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
        {fieldErrors.password && (
          <p className="text-[11px] text-red-400 font-medium pl-0.5">{fieldErrors.password}</p>
        )}
      </div>

      {/* Botão de Envio (Entrar) - Visual Sólido de Alto Contraste */}
      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full py-2.5 px-4 bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold rounded-xl transition-all duration-150 active:scale-[0.99] focus:outline-none focus:ring-2 focus:ring-zinc-400/50 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center gap-2 mt-2 cursor-pointer shadow-sm"
      >
        {isSubmitting ? (
          <>
            <Loader2 className="w-3.5 h-3.5 animate-spin text-zinc-900" />
            <span>Validando credenciais...</span>
          </>
        ) : (
          <>
            <LogIn className="w-3.5 h-3.5" />
            <span>Entrar no Sistema</span>
          </>
        )}
      </button>
    </form>
  );
};
