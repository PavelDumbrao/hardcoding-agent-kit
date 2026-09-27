---
name: deployment-guide
description: Универсальный гайд по деплою приложений. Выбор платформы, подготовка проекта, деплой и мониторинг. Используй когда нужно задеплоить проект или выбрать платформу для деплоя.
---

> **Примечание для экспортной версии:** ниже чувствительные IP, домены, пути, SSH-цели и другие infra-значения заменены на примеры и placeholders вида `<YOUR_...>`. Если ИИ-агенту нужны реальные значения, он должен **подставить реальные данные пользователя** или **сначала запросить их у пользователя**, а не использовать примеры как есть.


# Deployment Guide

## Выбор платформы

### Когда использовать что:

| Платформа | Лучше всего для | Когда выбирать |
|---|---|---|
| **Hostinger VPS** ⭐ | Docker, N8N, полный контроль | **Основной VPS** — все self-hosted сервисы, Docker контейнеры, N8N |
| **Vercel** | Frontend, Next.js, React | Статические сайты, SSR, Jamstack, быстрый деплой |
| **Railway** | Full-stack, БД, воркеры | Нужна БД, фоновые задачи, простой деплой |
| **Render** | Backend, API, веб-сервисы | API серверы, веб-сервисы, Docker |

### Решение за 30 секунд:

```
Self-hosted сервисы (N8N, SearXNG, Scraper)? → Hostinger VPS ⭐
Только фронтенд? → Vercel
Нужна БД? → Railway
API сервер? → Render
```

### ⭐ Hostinger VPS — основной сервер

**IP:** `<YOUR_VPS_IP>`
**SSH:** `ssh -i ~/.ssh/id_ed25519 <SSH_USER>@<YOUR_VPS_IP>`

**Сервисы на VPS:**
- N8N (порт 5678) — автоматизация
- SearXNG (порт 8888) — поиск
- Scraper Server (порт 9111) — извлечение контента
- Perplexica (порт 3000) — AI поиск
- Invidious (порт 3001) — YouTube API
- YT Transcript (порт 9222) — субтитры
- Telegram API (порт 8000) — Telegram сервис
- Shlink (порт 32775) — сокращение URL

## Подготовка проекта

### 1. Проверить зависимости
```bash
# Убедиться что все зависимости в package.json
npm install

# Проверить что проект собирается
npm run build
```

### 2. Настроить переменные окружения
```bash
# Создать .env.example
cp .env .env.example

# Убрать секреты
sed -i 's/=.*/=/' .env.example
```

### 3. Проверить .gitignore
```bash
# Должно быть:
node_modules/
.env
dist/
build/
*.log
```

### 4. Настроить скрипты
```json
// package.json
{
  "scripts": {
    "build": "tsc && vite build",
    "start": "node dist/server.js",
    "dev": "tsx watch src/server.ts"
  }
}
```

## Деплой на Vercel

### Быстрый старт:
```bash
npm install -g vercel
vercel login
vercel --prod
```

### С конфигурацией:
```json
// vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "nextjs"
}
```

## Деплой на Railway

### Быстрый старт:
```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

### С БД:
```bash
railway add --database postgres
railway variables set DATABASE_URL=<connection-string>
```

## Деплой на Render

### Быстрый старт:
```bash
npm install -g render-cli
render login
render blueprint init
render blueprint apply
```

### С конфигурацией:
```yaml
# render.yaml
services:
  - type: web
    name: my-app
    env: node
    buildCommand: npm install && npm run build
    startCommand: npm start
```

## Деплой на Hostinger VPS

### Быстрый старт:
```bash
ssh root@VPS_IP
cd /opt/project
git pull origin main
docker-compose up -d --build
```

### С Docker:
```dockerfile
# Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist ./dist
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    restart: unless-stopped
```

## Мониторинг после деплоя

### Проверить что работает:
```bash
# Проверить health endpoint
curl https://your-app.com/health

# Проверить логи
# Vercel: vercel logs <url>
# Railway: railway logs
# Render: render logs --service <id>
# VPS: docker logs <container>
```

### Настроить мониторинг:
- **Uptime Kuma** — self-hosted мониторинг (на VPS)
- **Vercel Analytics** — встроенный мониторинг
- **Railway Metrics** — встроенный мониторинг
- **Render Metrics** — встроенный мониторинг

## Troubleshooting

### Деплой не работает:
1. Проверить логи сборки
2. Проверить переменные окружения
3. Проверить что проект собирается локально
4. Проверить порты и health check

### Медленный деплой:
1. Оптимизировать Docker образ
2. Использовать кеширование
3. Уменьшить размер node_modules

### Ошибки runtime:
1. Проверить логи приложения
2. Проверить переменные окружения
3. Проверить подключение к БД

## Best Practices

1. **Использовать preview environments** для тестирования
2. **Настроить автодеплой** из GitHub
3. **Использовать переменные окружения** для секретов
4. **Настроить health checks** для мониторинга
5. **Мониторить логи** после каждого деплоя
6. **Делать бэкапы** перед major изменениями
7. **Использовать Infrastructure as Code** (render.yaml, railway.json)