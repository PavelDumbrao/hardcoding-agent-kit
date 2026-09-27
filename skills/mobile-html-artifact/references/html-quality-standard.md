# Mobile HTML Artifact Quality Standard

Этот reference открывай, когда создаешь или ревьюишь автономный HTML-артефакт: лендинг, лид-магнит, гайд, оффер, мини-презентацию или страницу для Telegram/iPhone.

## Базовый стандарт

Итоговый файл должен быть:
- один автономный `.html`, если пользователь не попросил структуру проекта;
- CSS внутри `<style>`;
- JS внутри `<script>` только если нужен;
- mobile-first под 360-430px;
- без горизонтального скролла;
- основной контент видим без JS;
- с ясным CTA и повтором CTA в длинных страницах;
- с надежным интерактивом, предпочтительно CSS-only;
- с оптимизированными изображениями и осмысленными `alt`;
- пригоден к локальному открытию и пересылке.

## Первый экран

Hero должен за 3-5 секунд отвечать:
- что это;
- для кого;
- какой результат получит человек;
- что нажать дальше.

Не делай hero абстрактной заставкой. Первый экран должен содержать смысл, CTA и визуальный сигнал темы. Для branded/product/object pages объект должен быть заметен в первом viewport.

## Структура страницы

Базовая структура:
1. Hero.
2. Короткое обещание результата.
3. Проблема или боль.
4. Почему старый подход не работает.
5. Новая механика или решение.
6. Пошаговый план.
7. Примеры, кейсы или сценарии.
8. Выгоды.
9. Интерактив: квиз, вкладки, чеклист, калькулятор или развилка.
10. CTA.
11. FAQ.
12. Финальный CTA.

Для business/offfer страниц:
1. Что это.
2. Для кого.
3. Какую проблему закрывает.
4. Как работает.
5. Что получает клиент.
6. Почему это выгодно.
7. Как начать.
8. CTA.

## CSS-фундамент

```css
* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
  overflow-x: hidden;
}

body {
  margin: 0;
  min-width: 320px;
  overflow-x: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
  line-height: 1.5;
  color: #111;
  background: #f7efe3;
}

img, svg, video, canvas {
  max-width: 100%;
  height: auto;
}

.container {
  width: min(100% - 32px, 1120px);
  margin: 0 auto;
}
```

## Контент видим без JS

Плохо:

```css
.section {
  opacity: 0;
  transform: translateY(24px);
}
```

Правильно:

```css
.section {
  opacity: 1;
  transform: none;
}

.js-enabled .section.reveal {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity .5s ease, transform .5s ease;
}

.js-enabled .section.reveal.is-visible {
  opacity: 1;
  transform: none;
}
```

И только потом:

```js
document.documentElement.classList.add('js-enabled');
```

## Fixed CTA

Используй fixed CTA только когда это помогает конверсии. Требования:
- `body` имеет нижний padding;
- кнопка учитывает `env(safe-area-inset-bottom)`;
- высота минимум 52-56px;
- не перекрывает финальный блок;
- есть обычные CTA внутри контента для no-CSS/no-fixed сценариев.

```css
body {
  padding-bottom: 104px;
}

.fixed-cta {
  position: fixed;
  left: 16px;
  right: 16px;
  bottom: calc(14px + env(safe-area-inset-bottom));
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 56px;
  padding: 14px 18px;
  border-radius: 999px;
  background: #111;
  color: #fff;
  text-decoration: none;
  font-weight: 800;
  box-shadow: 0 18px 40px rgba(0, 0, 0, .22);
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
```

## Надежный интерактив

Предпочитай:
- `<details><summary>` для FAQ;
- `radio input + label` для вкладок;
- `checkbox + label` для раскрывающихся блоков;
- CSS-only квизы и чеклисты.

Для больших промптов используй `textarea readonly`, а не `pre`, если пользователь должен копировать текст на iPhone.

Копирование делай с fallback:
1. `navigator.clipboard.writeText` в secure context.
2. `document.execCommand('copy')`.
3. Ручное выделение textarea и текстовая подсказка.

## Изображения

Три режима:
- Внешние файлы рядом с HTML: лучше для проекта или архива.
- Base64 внутри HTML: только если нужен один файл.
- SVG/CSS-графика: для простых схем, иконок, декоративных элементов.

Перед base64 обязательно оптимизируй изображения. Ориентиры:

| Тип | Формат | Ширина | Качество | Цель |
|---|---:|---:|---:|---:|
| Hero | WebP | 1200-1600px | 70-82 | 120-350 KB |
| Секция | WebP | 900-1400px | 68-80 | 80-250 KB |
| Иконка | SVG/WebP | 128-512px | 70-85 | до 50 KB |
| Текстура | WebP | 800-1200px | 45-65 | до 120 KB |

Не встраивай base64, если:
- изображений больше 8-10;
- картинки после сжатия тяжелее 400-500 KB каждая;
- итоговый HTML тяжелее 6-10 MB;
- файл нужен для SEO/публикации на сайте;
- есть нормальный хостинг для ассетов.

## Section visual component

```html
<figure class="section-visual">
  <img src="assets_optimized/section-1.webp" alt="Описание визуала" loading="lazy">
  <figcaption>Короткое пояснение, если оно помогает.</figcaption>
</figure>
```

```css
.section-visual {
  margin: 24px 0;
  padding: 10px;
  border-radius: 24px;
  background: rgba(255, 255, 255, .72);
  border: 1px solid rgba(17, 17, 17, .08);
  box-shadow: 0 20px 60px rgba(40, 28, 15, .14);
}

.section-visual img {
  display: block;
  width: 100%;
  border-radius: 18px;
}

.section-visual figcaption {
  margin: 10px 4px 2px;
  color: #6f675e;
  font-size: 13px;
}
```

## AI visual prompts

Сначала определи, какие секции реально усиливаются визуалами. Затем сформируй единое visual direction.

Базовое направление:

```text
Premium clean business CGI, warm ivory background, graphite black interface elements, orange and gold accents, subtle green growth highlights, soft shadows, clean composition, no logos, no watermark, no random text, mobile-friendly composition.
```

Для каждой картинки добавляй смысл сцены. Не проси модель генерировать читаемый текст внутри изображения: текст лучше делать HTML/CSS.

## Контраст и темные секции

Если темная секция содержит светлые карточки, явно задай цвет текста внутри карточек.

```css
.dark-section {
  background: #111;
  color: #fff;
}

.dark-section .card {
  background: #fff;
  color: #111;
}

.dark-section .card .muted {
  color: #665f57;
}
```

## Типографика

- Hero title: 34-46px на мобильном, можно больше на desktop.
- Body: 16-18px.
- Small text: не ниже 13px.
- `line-height`: 1.1-1.2 для заголовков, 1.45-1.65 для текста.
- Не делай длинные строки на desktop: ограничивай `max-width`.
- Не используй `vw` для обычного текста. Для hero допустим `clamp`, но проверь мобильную ширину.

## Кнопки

- Высота 48-56px.
- Большой hit area.
- `touch-action: manipulation`.
- Видимый `:focus-visible`.
- Не полагайся только на hover.

## Проверка размера

Если HTML содержит base64:

```bash
ls -lh index_embedded.html
```

Ориентиры:
- до 1 MB: отлично;
- 1-3 MB: нормально;
- 3-6 MB: допустимо при большом количестве визуалов;
- 6-10 MB: тяжело для мобильного;
- больше 10 MB: лучше убрать часть base64 или сильнее сжать.

## Чеклист сдачи

- [ ] HTML открывается локально.
- [ ] Нет горизонтального скролла.
- [ ] Первый экран понятен за 3-5 секунд.
- [ ] Есть CTA.
- [ ] Fixed CTA не перекрывает низ страницы.
- [ ] `body` имеет нижний padding, если есть fixed CTA.
- [ ] Основной контент видим без JS.
- [ ] Критичный интерактив работает без JS.
- [ ] Картинки сжаты.
- [ ] Base64 используется только после оптимизации.
- [ ] У всех картинок есть `alt`.
- [ ] Тёмные секции не ломают контраст карточек.
- [ ] Текст читаем на ширине 360px.
- [ ] Кнопки удобно нажимать пальцем.
- [ ] Нет внешних зависимостей без необходимости.
- [ ] Нет случайного текста внутри AI-картинок.
- [ ] Итоговый файл не раздут без необходимости.
