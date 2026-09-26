#!/usr/bin/env bash
# Безопасный установщик набора хуков Hard Coding Agent Kit.
# Ничего не перезаписывает без нужды: конфиг трогает только как подсказку.
set -euo pipefail

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
ZCODE_DIR="$HOME/.zcode"

echo "1/4 Создаю папки: $ZCODE_DIR/hooks и $ZCODE_DIR/secrets"
mkdir -p "$ZCODE_DIR/hooks" "$ZCODE_DIR/secrets"

echo "2/4 Копирую скрипты хуков..."
cp "$KIT_DIR"/hooks/*.py "$ZCODE_DIR/hooks/"
chmod 600 "$KIT_DIR"/hooks/*.py 2>/dev/null || true

if [ ! -f "$ZCODE_DIR/secrets/telegram.env" ]; then
  cp "$KIT_DIR/secrets-template/telegram.env.example" "$ZCODE_DIR/secrets/telegram.env"
  chmod 600 "$ZCODE_DIR/secrets/telegram.env"
  echo "   → Заготовка секретов создана: $ZCODE_DIR/secrets/telegram.env (заполни её!)"
else
  echo "   → Секреты уже есть, не трогаю."
fi

if [ ! -f "$ZCODE_DIR/AGENTS.md" ]; then
  cp "$KIT_DIR/AGENTS.md" "$ZCODE_DIR/AGENTS.md"
  echo "3/4 Шаблон инструкции скопирован в $ZCODE_DIR/AGENTS.md (заполни раздел «Мои данные»)"
else
  echo "3/4 Инструкция уже есть ($ZCODE_DIR/AGENTS.md) — не трогаю. Сравни с AGENTS.md из кита вручную."
fi

cat <<'EOF'
4/4 Осталось руками (5 минут):
  a) Заполни ~/.zcode/secrets/telegram.env (токен бота и chat_id).
  b) Открой ~/.zcode/cli/config.json и добавь блок "hooks" из
     config-examples/config-zcode.json (файл создай, если его нет).
     ВАЖНО: события кладутся внутрь "hooks": { "enabled": true, "events": {...} }.
  c) Перезапусти ZCode.
  d) Проверка: python3 ~/.zcode/hooks/smoke.py  → должно быть 24/24 PASS.
  e) Когда закончишь любую задачу — придёт Telegram-сообщение. Значит, работает.
EOF
