import { describe, it, expect, vi, beforeEach } from 'vitest';
import { authApi, api } from '../api/authApi';

vi.mock('../api/authApi', async () => {
  const actual = await vi.importActual('../api/authApi');
  return {
    ...actual,
  };
});

describe('Módulo de API authApi', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('Executa os métodos HTTP corretamente no cliente Axios', async () => {
    vi.spyOn(api, 'post').mockImplementation((url) => {
      if (url === '/login') return Promise.resolve({ data: { access_token: 'tok' } }) as any;
      if (url === '/refresh') return Promise.resolve({ data: { access_token: 'tok_ref' } }) as any;
      if (url === '/logout') return Promise.resolve({ data: { message: 'ok' } }) as any;
      return Promise.reject(new Error('Unknown'));
    });

    vi.spyOn(api, 'get').mockResolvedValue({ data: { id: 1, email: 'a@b.com' } });

    const loginRes = await authApi.login({ email: 'a@b.com', password: '123' });
    expect(loginRes.access_token).toBe('tok');

    const refreshRes = await authApi.refresh();
    expect(refreshRes.access_token).toBe('tok_ref');

    const logoutRes = await authApi.logout();
    expect(logoutRes.message).toBe('ok');

    const meRes = await authApi.getMe();
    expect(meRes.email).toBe('a@b.com');
  });
});
