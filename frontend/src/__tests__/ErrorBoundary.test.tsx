import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ErrorBoundary } from '../components/ErrorBoundary';

const ProblemChild = ({ shouldThrow = false, message = 'Test Error' }: { shouldThrow?: boolean; message?: string }) => {
  if (shouldThrow) {
    throw new Error(message);
  }
  return <div>Componente Normal</div>;
};

describe('ErrorBoundary Component', () => {
  const originalConsoleError = console.error;
  const originalLocation = window.location;

  beforeEach(() => {
    console.error = vi.fn();
    // @ts-expect-error mock window.location.reload
    delete window.location;
    window.location = { ...originalLocation, reload: vi.fn() } as any;
  });

  afterEach(() => {
    console.error = originalConsoleError;
    window.location = originalLocation as any;
  });

  it('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <ProblemChild shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Componente Normal')).toBeInTheDocument();
  });

  it('catches render error, calls componentDidCatch, and renders default fallback UI', () => {
    render(
      <ErrorBoundary>
        <ProblemChild shouldThrow={true} message="Crash detonated!" />
      </ErrorBoundary>
    );

    expect(screen.getByText('Ocorreu um erro ao carregar este módulo')).toBeInTheDocument();
    expect(screen.getByText('Crash detonated!')).toBeInTheDocument();
    expect(console.error).toHaveBeenCalled();
  });

  it('renders custom fallbackTitle when provided and handles empty error message', () => {
    render(
      <ErrorBoundary fallbackTitle="Falha Crítica no Dashboard">
        <ProblemChild shouldThrow={true} message="" />
      </ErrorBoundary>
    );

    expect(screen.getByText('Falha Crítica no Dashboard')).toBeInTheDocument();
  });

  it('handles reload button click via handleRetry', () => {
    render(
      <ErrorBoundary>
        <ProblemChild shouldThrow={true} message="Falha para reload" />
      </ErrorBoundary>
    );

    const reloadButton = screen.getByRole('button', { name: /recarregar página/i });
    expect(reloadButton).toBeInTheDocument();

    fireEvent.click(reloadButton);
    expect(window.location.reload).toHaveBeenCalledTimes(1);
  });
});
