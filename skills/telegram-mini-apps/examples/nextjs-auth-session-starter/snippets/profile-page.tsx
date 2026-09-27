'use client';

import { useEffect, useMemo, useState } from 'react';
import BrowserAuthNotice from '@/components/ui/BrowserAuthNotice';
import { fetchMiniAppJson, getMiniAppSurface, isMiniAppApiError } from '@/lib/miniapp-client';

interface ProfilePayload {
  viewer: {
    user: { id: number; firstName: string | null; username: string | null };
  };
}

export default function ProfilePage() {
  const [data, setData] = useState<ProfilePayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const isBrowserSurface = useMemo(() => getMiniAppSurface() === 'browser', []);

  useEffect(() => {
    async function load() {
      try {
        setData(await fetchMiniAppJson<ProfilePayload>('/api/profile'));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Не удалось загрузить профиль');
        setErrorStatus(isMiniAppApiError(err) ? err.status : null);
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  const needsLogin = Boolean(!loading && error && errorStatus === 401 && isBrowserSurface);

  if (needsLogin) {
    return (
      <BrowserAuthNotice
        isAuthenticated={false}
        guestTitle="Подключить Telegram к профилю"
        guestDescription="В браузере профиль открывается через web fallback. После входа та же session будет работать и на остальных персональных экранах."
        authenticatedTitle="Веб-сессия активна"
        authenticatedDescription="Session уже активна."
        guestActions={[{ label: 'Войти через Телеграм', href: '/login/telegram' }]}
      />
    );
  }

  return <pre>{JSON.stringify(data, null, 2)}</pre>;
}
