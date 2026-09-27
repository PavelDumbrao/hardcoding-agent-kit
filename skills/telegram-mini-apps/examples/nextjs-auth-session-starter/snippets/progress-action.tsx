import { fetchMiniAppJson, getMiniAppSurface, isMiniAppApiError } from '@/lib/miniapp-client';

async function handleCompleteLesson(lessonId: number, isAuthenticated: boolean) {
  const isBrowserSurface = getMiniAppSurface() === 'browser';
  const canUpdateProgress = !isBrowserSurface || isAuthenticated;

  if (!canUpdateProgress) {
    throw new Error('Чтобы сохранять прогресс в браузере, сначала войди через Телеграм.');
  }

  try {
    await fetchMiniAppJson('/api/progress', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
      },
      body: JSON.stringify({ lessonId, completed: true }),
    });
  } catch (err) {
    if (isMiniAppApiError(err) && err.status === 401 && isBrowserSurface) {
      throw new Error('Сессия в браузере истекла. Войди через Телеграм ещё раз и повтори действие.');
    }
    throw err;
  }
}
