# Deployment Guide для Telegram Mini Apps

Подробный гайд по деплою Telegram Mini Apps на различные платформы.

## 🎯 Требования перед деплоем

### Обязательные требования
- ✅ HTTPS соединение (обязательно для Telegram)
- ✅ Валидный SSL сертификат
- ✅ Быстрая загрузка (< 2 секунд)
- ✅ Адаптивный дизайн (mobile-first)
- ✅ Работа на iOS, Android, Desktop

### Рекомендуемые требования
- ✅ CDN для статики
- ✅ Gzip/Brotli сжатие
- ✅ Кеширование статических ресурсов
- ✅ Мониторинг ошибок (Sentry, LogRocket)
- ✅ Аналитика (Google Analytics, Amplitude)

## 🚀 Vercel (Рекомендуется)

### Преимущества
- Автоматический HTTPS
- Глобальный CDN
- Мгновенный деплой
- Бесплатный тариф для хобби-проектов
- Интеграция с GitHub

### Шаг 1: Установка Vercel CLI
```bash
npm i -g vercel
```

### Шаг 2: Логин
```bash
vercel login
```

### Шаг 3: Деплой
```bash
# Первый деплой (preview)
vercel

# Production деплой
vercel --prod
```

### Шаг 4: Настройка переменных окружения
```bash
# Через CLI
vercel env add BOT_TOKEN

# Или через веб-интерфейс
# https://vercel.com/your-project/settings/environment-variables
```

### Шаг 5: Автоматический деплой через GitHub
1. Подключи репозиторий к Vercel
2. Каждый push в `main` → автоматический production деплой
3. Каждый PR → preview деплой

### vercel.json (опционально)
```json
{
  "buildCommand": "pnpm build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "regions": ["iad1"],
  "env": {
    "BOT_TOKEN": "@bot_token"
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Frame-Options",
          "value": "SAMEORIGIN"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        }
      ]
    }
  ]
}
```

## 🚂 Railway

### Преимущества
- Простой деплой
- Автоматический HTTPS
- Поддержка Docker
- Интеграция с GitHub
- Бесплатный тариф ($5 кредитов/месяц)

### Шаг 1: Установка Railway CLI
```bash
npm i -g @railway/cli
```

### Шаг 2: Логин
```bash
railway login
```

### Шаг 3: Инициализация проекта
```bash
railway init
```

### Шаг 4: Деплой
```bash
railway up
```

### Шаг 5: Настройка переменных
```bash
# Через CLI
railway variables set BOT_TOKEN=your_token

# Или через веб-интерфейс
# https://railway.app/project/your-project/settings
```

### railway.json (опционально)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pnpm install && pnpm build"
  },
  "deploy": {
    "startCommand": "pnpm start",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## 🔥 Firebase Hosting

### Преимущества
- Глобальный CDN
- Автоматический HTTPS
- Бесплатный тариф (10GB/месяц)
- Интеграция с Firebase services

### Шаг 1: Установка Firebase CLI
```bash
npm i -g firebase-tools
```

### Шаг 2: Логин
```bash
firebase login
```

### Шаг 3: Инициализация
```bash
firebase init hosting
```

Выбери:
- Hosting: Configure files for Firebase Hosting
- Use an existing project или Create a new project
- Public directory: `out` (для Next.js static export)
- Single-page app: Yes
- GitHub integration: Yes (опционально)

### Шаг 4: Настройка Next.js для static export
```javascript
// next.config.ts
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
```

### Шаг 5: Build и деплой
```bash
# Build
pnpm build

# Деплой
firebase deploy --only hosting
```

### firebase.json
```json
{
  "hosting": {
    "public": "out",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(jpg|jpeg|gif|png|svg|webp)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000, immutable"
          }
        ]
      }
    ]
  }
}
```

## ☁️ Cloudflare Pages

### Преимущества
- Бесплатный тариф (неограниченный трафик)
- Глобальный CDN
- Автоматический HTTPS
- Интеграция с GitHub

### Шаг 1: Подключение через веб-интерфейс
1. Зайди на [pages.cloudflare.com](https://pages.cloudflare.com)
2. Connect to Git → выбери репозиторий
3. Configure build:
   - Build command: `pnpm build`
   - Build output directory: `.next`
   - Framework preset: Next.js

### Шаг 2: Настройка переменных окружения
В настройках проекта → Environment variables:
```
BOT_TOKEN=your_token
NODE_VERSION=18
```

### Шаг 3: Деплой
Автоматически при каждом push в main.

## 🐳 Docker + VPS

### Преимущества
- Полный контроль
- Можно использовать свой VPS
- Подходит для сложных приложений

### Dockerfile
```dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies
COPY package.json pnpm-lock.yaml ./
RUN corepack enable pnpm && pnpm install --frozen-lockfile

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN corepack enable pnpm && pnpm build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  tma:
    build: .
    ports:
      - "3000:3000"
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - NODE_ENV=production
    restart: unless-stopped
    networks:
      - tma-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - tma
    restart: unless-stopped
    networks:
      - tma-network

networks:
  tma-network:
    driver: bridge
```

### Деплой на VPS
```bash
# Подключиться к VPS
ssh user@your-vps-ip

# Клонировать репозиторий
git clone https://github.com/your-username/your-tma.git
cd your-tma

# Создать .env файл
echo "BOT_TOKEN=your_token" > .env

# Запустить
docker-compose up -d

# Проверить логи
docker-compose logs -f
```

## 🔒 Настройка HTTPS (для VPS)

### Certbot (Let's Encrypt)
```bash
# Установить Certbot
sudo apt install certbot python3-certbot-nginx

# Получить сертификат
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo certbot renew --dry-run
```

### nginx.conf для HTTPS
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://tma:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 📊 Мониторинг и аналитика

### Sentry (мониторинг ошибок)
```bash
npm install @sentry/nextjs
```

```javascript
// sentry.client.config.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 1.0,
  environment: process.env.NODE_ENV,
});
```

### Google Analytics
```typescript
// app/layout.tsx
import Script from 'next/script';

export default function RootLayout({ children }) {
  return (
    <html>
      <head>
        <Script
          src={`https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GA_ID}`}
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${process.env.NEXT_PUBLIC_GA_ID}');
          `}
        </Script>
      </head>
      <body>{children}</body>
    </html>
  );
}
```

## ⚡ Оптимизация производительности

### 1. Image Optimization
```typescript
import Image from 'next/image';

<Image
  src="/logo.png"
  alt="Logo"
  width={200}
  height={200}
  priority
/>
```

### 2. Code Splitting
```typescript
import dynamic from 'next/dynamic';

const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <p>Loading...</p>,
  ssr: false,
});
```

### 3. Caching
```typescript
// app/api/data/route.ts
export async function GET() {
  return Response.json(data, {
    headers: {
      'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
    },
  });
}
```

## 🔗 Настройка бота после деплоя

### Установка Menu Button
```
/mybots → выбрать бота → Bot Settings → Menu Button → Configure Menu Button
Введи URL: https://your-domain.com
```

### Установка Web App
```
/setmenubutton
Выбери бота
Введи URL: https://your-domain.com
```

### Проверка
Открой бота в Telegram и нажми на кнопку Menu — должен открыться твой Mini App.

## 📋 Чек-лист перед production деплоем

- [ ] HTTPS настроен и работает
- [ ] Все переменные окружения установлены
- [ ] Тестирование на iOS, Android, Desktop
- [ ] Загрузка < 2 секунд
- [ ] Мониторинг ошибок настроен (Sentry)
- [ ] Аналитика настроена (GA)
- [ ] Backup стратегия определена
- [ ] CDN настроен для статики
- [ ] Gzip/Brotli сжатие включено
- [ ] Security headers настроены
- [ ] Rate limiting настроен (если нужно)
- [ ] Документация обновлена
- [ ] README.md содержит инструкции по деплою

## 🐛 Troubleshooting

### Mini App не открывается
1. Проверь HTTPS — должен быть валидный сертификат
2. Проверь URL в настройках бота
3. Проверь логи сервера
4. Попробуй открыть URL напрямую в браузере

### Медленная загрузка
1. Включи CDN
2. Оптимизируй изображения
3. Включи code splitting
4. Проверь размер bundle (должен быть < 500KB)

### Ошибки в production
1. Проверь логи через `vercel logs` или `railway logs`
2. Проверь Sentry dashboard
3. Проверь переменные окружения

## 🔗 Полезные ссылки

- [Vercel Documentation](https://vercel.com/docs)
- [Railway Documentation](https://docs.railway.app/)
- [Firebase Hosting](https://firebase.google.com/docs/hosting)
- [Cloudflare Pages](https://developers.cloudflare.com/pages/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
