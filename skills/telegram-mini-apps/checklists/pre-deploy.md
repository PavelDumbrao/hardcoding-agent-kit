# Pre-Deploy Checklist для Telegram Mini Apps

Полный чек-лист перед деплоем Mini App в production.

## 🔐 Безопасность

- [ ] **Все секреты в переменных окружения**
  - BOT_TOKEN не в коде
  - API ключи не в коде
  - Приватные ключи не в коде
  
- [ ] **.env файлы в .gitignore**
  ```
  .env
  .env.local
  .env.production
  ```

- [ ] **Валидация initData на backend**
  ```typescript
  import { validate } from '@tma.js/init-data-node';
  
  const isValid = validate(initDataRaw, BOT_TOKEN);
  if (!isValid) throw new Error('Invalid init data');
  ```

- [ ] **CORS настроен правильно**
  - Только разрешённые домены
  - Не используется `*` в production

- [ ] **Rate limiting настроен**
  - Защита от DDoS
  - Лимиты на API запросы

- [ ] **Security headers настроены**
  ```
  X-Frame-Options: SAMEORIGIN
  X-Content-Type-Options: nosniff
  X-XSS-Protection: 1; mode=block
  ```

## 🌐 HTTPS и домен

- [ ] **HTTPS настроен и работает**
  - Валидный SSL сертификат
  - Нет ошибок в браузере
  - Проверено на https://www.ssllabs.com/

- [ ] **Домен настроен**
  - DNS записи корректны
  - Домен резолвится
  - Нет редиректов на http://

- [ ] **CDN настроен** (опционально)
  - Статика раздаётся через CDN
  - Кеширование работает

## 📱 Тестирование

- [ ] **Тестирование на iOS**
  - iPhone (разные модели)
  - iPad
  - Safari браузер

- [ ] **Тестирование на Android**
  - Разные версии Android
  - Разные производители
  - Chrome браузер

- [ ] **Тестирование на Desktop**
  - Windows
  - macOS
  - Linux
  - Telegram Desktop

- [ ] **Тестирование в разных темах**
  - Светлая тема
  - Тёмная тема
  - Кастомные цвета

- [ ] **Тестирование функционала**
  - Main Button работает
  - Back Button работает
  - Haptic Feedback работает
  - Viewport расширяется
  - Popup/Alert работают
  - QR Scanner работает (если используется)
  - Clipboard работает (если используется)

## ⚡ Производительность

- [ ] **Размер bundle проверен**
  ```bash
  pnpm build
  # Проверь размер .next/static/chunks/
  # Должен быть < 500KB для первой загрузки
  ```

- [ ] **Lighthouse score > 90**
  - Performance > 90
  - Accessibility > 90
  - Best Practices > 90
  - SEO > 90

- [ ] **Время загрузки < 2 секунд**
  - First Contentful Paint < 1.5s
  - Time to Interactive < 2s
  - Проверено на 3G соединении

- [ ] **Изображения оптимизированы**
  - WebP формат
  - Правильные размеры
  - Lazy loading

- [ ] **Code splitting настроен**
  ```typescript
  const Heavy = dynamic(() => import('./Heavy'), {
    loading: () => <Spinner />,
    ssr: false,
  });
  ```

- [ ] **Gzip/Brotli сжатие включено**

## 🎨 UI/UX

- [ ] **Адаптивный дизайн**
  - Работает на всех разрешениях
  - Нет горизонтального скролла
  - Кнопки достаточно большие (min 44x44px)

- [ ] **Цвета темы используются**
  ```typescript
  const themeParams = useThemeParams();
  backgroundColor: themeParams.bgColor
  ```

- [ ] **Шрифты читаемые**
  - Размер >= 14px
  - Контраст достаточный (WCAG AA)

- [ ] **Loading states**
  - Скелетоны для контента
  - Спиннеры для загрузки
  - Disabled состояния для кнопок

- [ ] **Error states**
  - Понятные сообщения об ошибках
  - Возможность повторить действие
  - Fallback UI

- [ ] **Empty states**
  - Понятные сообщения
  - Призыв к действию

## 🤖 Настройка бота

- [ ] **Menu Button настроен**
  ```
  /mybots → Bot Settings → Menu Button
  URL: https://your-domain.com
  ```

- [ ] **Команды настроены**
  ```
  /setcommands
  start - Запустить бота
  help - Помощь
  app - Открыть Mini App
  ```

- [ ] **Описание бота заполнено**
  ```
  /setdescription
  /setabouttext
  ```

- [ ] **Аватар бота установлен**
  ```
  /setuserpic
  ```

- [ ] **Inline mode настроен** (если нужно)
  ```
  /setinline
  /setinlinefeedback
  ```

## 📊 Мониторинг и аналитика

- [ ] **Sentry настроен**
  ```typescript
  Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    environment: 'production',
  });
  ```

- [ ] **Google Analytics настроен**
  ```typescript
  gtag('config', GA_ID);
  ```

- [ ] **Логирование настроено**
  - Важные события логируются
  - Ошибки логируются
  - PII не логируется

- [ ] **Uptime monitoring настроен**
  - UptimeRobot / Pingdom
  - Алерты на email/Telegram

## 🗄️ База данных (если используется)

- [ ] **Миграции применены**
  ```bash
  pnpm prisma migrate deploy
  ```

- [ ] **Индексы созданы**
  - На часто запрашиваемые поля
  - На foreign keys

- [ ] **Backup настроен**
  - Автоматический backup
  - Проверен restore

- [ ] **Connection pooling настроен**
  ```
  DATABASE_URL="postgresql://...?connection_limit=10"
  ```

## 🔄 CI/CD

- [ ] **Автоматический деплой настроен**
  - GitHub Actions / Vercel / Railway
  - Деплой на push в main

- [ ] **Preview деплой настроен**
  - Для каждого PR
  - Автоматическое удаление после merge

- [ ] **Environment variables настроены**
  - Production переменные
  - Preview переменные

- [ ] **Тесты запускаются**
  ```yaml
  - name: Run tests
    run: pnpm test
  ```

## 📝 Документация

- [ ] **README.md обновлён**
  - Описание проекта
  - Инструкции по установке
  - Инструкции по деплою
  - Переменные окружения

- [ ] **CHANGELOG.md ведётся**
  - Версии
  - Изменения
  - Breaking changes

- [ ] **API документация** (если есть API)
  - Эндпоинты описаны
  - Примеры запросов
  - Примеры ответов

## 🚀 Финальные проверки

- [ ] **Проверка в production окружении**
  - Открыть через бота
  - Проверить все функции
  - Проверить на разных устройствах

- [ ] **Проверка метрик**
  - Sentry: нет ошибок
  - Analytics: события отслеживаются
  - Logs: нет критичных ошибок

- [ ] **Проверка производительности**
  - Lighthouse в production
  - Время загрузки
  - Размер bundle

- [ ] **Backup план готов**
  - Rollback стратегия
  - Контакты команды
  - Документация по восстановлению

## ✅ Готово к запуску!

После прохождения всех пунктов:

1. **Сделай финальный коммит**
   ```bash
   git add .
   git commit -m "chore: production ready"
   git push origin main
   ```

2. **Задеплой в production**
   ```bash
   vercel --prod
   # или
   railway up --environment production
   ```

3. **Проверь в Telegram**
   - Открой бота
   - Нажми Menu Button
   - Проверь все функции

4. **Мониторь первые часы**
   - Следи за Sentry
   - Следи за логами
   - Следи за метриками

5. **Объяви о запуске!** 🎉
   - Пост в канале
   - Уведомление пользователей
   - Обновление документации

---

## 🆘 Если что-то пошло не так

### Rollback
```bash
# Vercel
vercel rollback

# Railway
railway rollback

# Git
git revert HEAD
git push origin main
```

### Проверка логов
```bash
# Vercel
vercel logs

# Railway
railway logs

# Sentry
# Открой dashboard
```

### Контакты поддержки
- Telegram: @your_support_bot
- Email: support@your-domain.com
- GitHub Issues: github.com/your-repo/issues

---

**Последнее обновление:** 09.03.2026
