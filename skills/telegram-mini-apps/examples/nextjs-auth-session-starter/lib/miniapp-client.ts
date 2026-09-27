// Клиентские helper'ы для работы с Telegram Mini App и API

export type MiniAppSurface = 'telegram' | 'browser';

export class MiniAppApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload?: unknown) {
    super(message);
    this.name = 'MiniAppApiError';
    this.status = status;
    this.payload = payload;
  }
}

export function isMiniAppApiError(error: unknown): error is MiniAppApiError {
  return error instanceof MiniAppApiError;
}

export function getTelegramInitData(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  return window.Telegram?.WebApp?.initData || null;
}

export function getMiniAppSurface(): MiniAppSurface {
  return getTelegramInitData() ? 'telegram' : 'browser';
}

export function buildTelegramHeaders(input?: HeadersInit): Headers {
  const headers = new Headers(input);
  const initData = getTelegramInitData();

  if (initData) {
    headers.set('x-telegram-init-data', initData);
  }

  return headers;
}

export async function fetchMiniAppJson<T>(input: string, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    ...init,
    headers: buildTelegramHeaders(init?.headers),
    cache: init?.cache ?? 'no-store',
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const errorMessage =
      payload && typeof payload === 'object' && 'error' in payload && typeof payload.error === 'string'
        ? payload.error
        : `Ошибка запроса (${response.status})`;

    throw new MiniAppApiError(errorMessage, response.status, payload);
  }

  return payload as T;
}
