'use client';

import Link from 'next/link';

export default function LoginPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl items-center px-4 py-10 md:px-6">
      <section className="w-full rounded-3xl border border-sky-400/20 bg-sky-500/10 p-6 text-center shadow-xl shadow-black/10 backdrop-blur md:p-8">
        <p className="text-sm uppercase tracking-[0.24em] text-sky-300">Вход</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">Подключить Telegram к веб-профилю</h1>
        <p className="mx-auto mt-4 max-w-2xl text-sm leading-6 text-sky-50/90">
          В обычном браузере Mini App использует web fallback через Telegram. Внутри Telegram WebView отдельный вход не нужен — там авторизация идёт через `initData`.
        </p>

        <Link
          href="/login/telegram"
          className="mt-6 inline-flex rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm font-medium text-white transition hover:bg-white/15 hover:border-white/20"
        >
          Войти через Телеграм
        </Link>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-3 text-sm text-sky-100/80">
          <Link href="/profile" className="rounded-2xl border border-white/10 px-4 py-3 text-white hover:bg-white/5">
            Назад в профиль
          </Link>
          <Link href="/" className="rounded-2xl border border-white/10 px-4 py-3 text-white hover:bg-white/5">
            На главную
          </Link>
        </div>
      </section>
    </main>
  );
}
