export type UserRole = 'administrador' | 'tecnico' | 'colaborador' | string;

export interface User {
  id: number;
  name?: string;
  email: string;
  role: UserRole;
  is_active: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface MessageResponse {
  message: string;
}

export interface ApiErrorResponse {
  detail: string;
}
