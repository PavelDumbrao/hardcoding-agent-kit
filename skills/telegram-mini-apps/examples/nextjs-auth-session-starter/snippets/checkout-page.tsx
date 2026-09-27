'use client';

import { useMemo, useState } from 'react';
import BrowserAuthNotice from '@/components/ui/BrowserAuthNotice';
import { fetchMiniAppJson, getMiniAppSurface, isMiniAppApiError } from '@/lib/miniapp-client';

export default function ExampleCheckoutPage() {
  const isBrowserSurface = useMemo(() => getMiniAppSurface() === 'browser', []);
  const [viewerIsAuthenticated, setViewerIsAuthenticated] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const canStartCheckout = !isBrowserSurface || viewerIsAuthenticated;

  async function handleCheckout() {
    try {
      setError(null);

      if (!canStartCheckout) {
        setError('Чтобы открыть checkout в браузере, сначала войди через Телеграм.');
        return;
      }

      await fetchMiniAppJson('/api/payments/create-link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flowType: 'extend_1m', email: 'user@example.com' }),
      });
    } catch (err) {
      if (isMiniAppApiError(err) && err.status === 401 && isBrowserSurface) {
        setError('Сессия в браузере истекла. Войди через Телеграм ещё раз и повтори действие.');
      } else {
        setError(err instanceof Error ? err.message : 'Не удалось подготовить checkout');
      }
    }
  }

  return (
    <>
      {isBrowserSurface ? (
        <BrowserAuthNotice
          isAuthenticated={viewerIsAuthenticated}
          guestTitle="Для browser checkout сначала нужен вход"
          guestDescription="Каталог и офферы можно изучать без Telegram WebView, но создание платёжной ссылки требует активной Telegram-сессии."
          authenticatedTitle="Веб-сессия активна"
          authenticatedDescription="После входа можно продолжать checkout в том же browser surface."
          guestActions={[{ label: 'Войти через Телеграм', href: '/login/telegram' }]}
        />
      ) : null}

      <button onClick={() => void handleCheckout()} disabled={!canStartCheckout}>
        {canStartCheckout ? 'Запустить checkout' : 'Сначала войди через Телеграм'}
      </button>
      {error ? <p>{error}</p> : null}
    </>
  );
}
