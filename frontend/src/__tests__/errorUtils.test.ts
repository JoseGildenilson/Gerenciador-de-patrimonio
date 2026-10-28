import { describe, it, expect } from 'vitest';
import { formatApiError } from '../utils/errorUtils';

describe('formatApiError Utility', () => {
  it('returns fallback message when err is null or undefined', () => {
    expect(formatApiError(null)).toBe('Ocorreu um erro na requisição');
    expect(formatApiError(undefined, 'Fallback customizado')).toBe('Fallback customizado');
  });

  it('returns detail directly when detail is a non-empty string', () => {
    const error = {
      response: {
        data: {
          detail: 'Patrimônio duplicado no sistema',
        },
      },
    };
    expect(formatApiError(error)).toBe('Patrimônio duplicado no sistema');
  });

  it('handles FastAPI/Pydantic validation errors array with loc and msg', () => {
    const error = {
      response: {
        data: {
          detail: [
            { loc: ['body', 'patrimony_number'], msg: 'Campo obrigatório' },
            { loc: ['body', 'serial_number'], msg: 'Serial já em uso' },
            { loc: ['body'], msg: 'Payload inválido' },
            'Erro em formato de texto puro',
            { loc: null, msg: 'Sem localização' },
          ],
        },
      },
    };

    const formatted = formatApiError(error);
    expect(formatted).toContain('patrimony_number: Campo obrigatório');
    expect(formatted).toContain('serial_number: Serial já em uso');
    expect(formatted).toContain('Payload inválido');
    expect(formatted).toContain('Erro em formato de texto puro');
    expect(formatted).toContain('Sem localização');
  });

  it('handles array detail containing non-object items and empty array', () => {
    const errorWithPrimitives = {
      response: {
        data: {
          detail: [123, null, false],
        },
      },
    };
    expect(formatApiError(errorWithPrimitives)).toBe('123; null; false');

    const errorEmpty = {
      response: {
        data: {
          detail: [],
        },
      },
    };
    expect(formatApiError(errorEmpty)).toBe('[]');
  });

  it('handles detail as an object with message property', () => {
    const error = {
      response: {
        data: {
          detail: {
            message: 'Erro interno formatado em objeto',
          },
        },
      },
    };
    expect(formatApiError(error)).toBe('Erro interno formatado em objeto');
  });

  it('handles detail as a plain object without message property by stringifying', () => {
    const error = {
      response: {
        data: {
          detail: {
            code: 'ERR_CUSTOM',
            status: 400,
          },
        },
      },
    };
    expect(formatApiError(error)).toBe(JSON.stringify({ code: 'ERR_CUSTOM', status: 400 }));
  });

  it('falls back when detail is a circular object that throws on JSON.stringify', () => {
    const circular: any = {};
    circular.self = circular;

    const error = {
      response: {
        data: {
          detail: circular,
        },
      },
    };
    expect(formatApiError(error, 'Falha ao serializar')).toBe('Falha ao serializar');
  });

  it('returns fallback message when error has no recognizable detail or response', () => {
    const genericErr = new Error('Erro padrão do JavaScript');
    expect(formatApiError(genericErr, 'Erro genérico')).toBe('Erro genérico');

    const networkErr = { request: {} };
    expect(formatApiError(networkErr)).toBe('Ocorreu um erro na requisição');
  });
});
