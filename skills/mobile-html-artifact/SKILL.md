---
name: mobile-html-artifact
description: Use when creating autonomous mobile-first HTML artifacts such as one-file landing pages, lead magnets, guides, offer pages, mini-presentations, Telegram/iPhone friendly HTML documents, or polished business/AI pages with embedded CSS, optional JS, CTA, responsive layout, images, WebP optimization, or base64 data URIs. Pair with cc-design for high-fidelity visual direction and use frontend-design instead when the request is a production React/Next.js/Tailwind app.
---

# Mobile HTML Artifact

Коротко: этот skill помогает создавать красивые автономные mobile-first HTML-файлы, которые можно локально открыть, отправить одним файлом и показать в Telegram, ChatGPT preview, Safari или мобильном браузере.

## Когда использовать
- Пользователь просит `HTML`, `лендинг`, `лид-магнит`, `гайд`, `продающую страницу`, `оффер`, `мини-презентацию`, `воронку`, `визуальный отчет` или файл, который можно отправить одним `.html`.
- Нужен mobile-first результат под iPhone/Android без горизонтального скролла.
- Нужны CTA, FAQ, CSS-only интерактив, copy buttons, embedded prompts, AI/business визуалы, WebP-сжатие или base64 images.
- Пользователь говорит "сделай красиво", "как digital artifact", "для Telegram", "одним файлом", "готовый HTML".

## Когда НЕ использовать
- Нужен backend, авторизация, база данных, платежи, сложный SPA или production app. Для React/Next.js/Tailwind UI используй `frontend-design`.
- Нужен только визуальный HTML-прототип, дизайн-система, slide-like demo или исследование направлений без требования автономного mobile HTML. Сначала используй `cc-design`.
- Нужно публиковать полноценный сайт с SEO, CDN и отдельными ассетами. Этот skill можно использовать только для первого артефакта/прототипа.

## Связка с UI skills
1. Для нетривиальной визуальной задачи сначала используй `cc-design`: определить аудиторию, визуальное направление, композицию, анти-паттерны и план проверки.
2. Затем используй этот skill как packaging/reliability слой: автономность, mobile-first, no-JS fallback, CTA, image compression, base64, локальная проверка.
3. Если в процессе выяснилось, что это production React/Next.js/Tailwind интерфейс, переключись на `frontend-design`, а этот skill не применяй как основной.

## Workflow
1. Определи цель страницы, аудиторию, целевое действие, стиль, первый экран, секции, требования к Telegram/iPhone и режим изображений.
2. Если ввод неполный и риск низкий, сделай явные предположения и продолжай. Если выбор влияет на бизнес-смысл, бренд, факты или необратимую публикацию, задай один точный вопрос.
3. Собери структуру: hero -> обещание результата -> проблема -> новая механика/решение -> шаги -> примеры/сценарии -> выгоды -> интерактив -> CTA -> FAQ -> финальный CTA.
4. Верстай mobile-first: один `.html`, CSS внутри `<style>`, JS внутри `<script>` только если нужен, `box-sizing: border-box`, `min-width: 320px`, без горизонтального скролла.
5. Контент должен быть видим без JavaScript. JS и анимации только progressive enhancement.
6. Важный интерактив делай надежным: `details/summary`, `radio/checkbox + label`, CSS-only tabs/quiz/checklist. Копирование текста делай с fallback.
7. Для продающей страницы добавляй фиксированный CTA снизу только если он помогает. Обязательно учитывай `env(safe-area-inset-bottom)` и `body padding-bottom`.
8. Изображения добавляй осмысленно: hero и 2-5 supporting visuals. Не допускай случайного текста, логотипов или watermark внутри AI-картинок.
9. Если нужен один автономный файл, сначала сожми изображения в WebP, затем встраивай base64. Не вставляй тяжелые PNG/JPG напрямую.
10. Проверь локально и на мобильной ширине: читаемость 360px, CTA, отсутствие горизонтального скролла, no-JS fallback, вес итогового файла.

## Ресурсы
- `references/html-quality-standard.md` — подробный стандарт верстки, изображений, base64, CTA, интерактива и чеклист сдачи. Читай перед созданием или ревью HTML.
- `assets/templates/starter.html` — стартовый автономный шаблон для быстрого первого файла.
- `scripts/optimize_images.py` — WebP-сжатие изображений перед base64.
- `scripts/embed_images_base64.py` — замена локальных `img src` на base64 data URI в финальной копии HTML.

## Visual direction по умолчанию
Для AI/business страниц, если пользователь не дал стиль:
- premium clean business aesthetic;
- теплый ivory/cream фон;
- graphite/black UI;
- orange/gold accents;
- subtle green growth highlights;
- мягкие тени, ясная сетка, низкий визуальный шум;
- без логотипов, watermark и случайного текста в изображениях.

Не превращай это в однотонную beige/orange страницу: добавляй графит, белые поверхности, зеленые/золотые акценты и достаточный контраст.

## Smoke tests
- Запрос: "Сделай красивый HTML-лид-магнит одним файлом для Telegram" -> ожидается mobile-first `index.html`, CTA, FAQ, no-JS-visible контент, проверка ширины 360px, при base64 сначала WebP-сжатие.
- Запрос: "Создай React dashboard и красиво оформи" -> ожидается переключение на `frontend-design`, этот skill не основной.
- Запрос: "Сделай HTML-презентацию/лендинг, чтобы выглядело дорого" -> ожидается связка `cc-design` для визуального направления + этот skill для автономного HTML и проверки.

## Red flags
- Секции скрыты через `opacity: 0` и становятся видимыми только после JS.
- Fixed CTA перекрывает финальный контент или не учитывает safe area.
- Base64 вставлен из несжатых PNG/JPG.
- На мобильном есть горизонтальный скролл всей страницы.
- Текст на изображениях сгенерирован моделью и выглядит случайно.
- Визуальная композиция generic: гигантский hero, однотипные cards, бессмысленные декоративные иконки, агрессивные градиенты.
