# Hooks — что здесь происходит

Это универсальное ядро Hard Coding Agent Kit. Скрипты лежат в `~/.hardcoding-agent-kit/hooks` и подключаются через отдельный adapter конкретного рантайма.

## События

- `SessionStart` → `session_start.py` — подмешивает только существующие project-state / plan / handoff-файлы.
- `PreToolUse` → `pre_tool_use.py` — блокирует опасное удаление, `sudo`, `find /`, чтение secret-файлов через shell/Read и `git add .env`.
- `PostToolUse` → `post_tool_use.py` — пишет минимальную локальную телеметрию без tool output.
- `Stop` → `stop_notify.py` — если локально настроен Telegram, присылает короткое уведомление.

## Важная граница защиты

Hook — не антивирус и не абсолютная песочница. Он защищает только события и tool calls, которые конкретный runtime реально передаёт в lifecycle hooks.

Поэтому:
- конфиг включает `Read` в `PreToolUse` там, где это поддерживается;
- секреты всё равно нельзя класть в обычный чат;
- не надо считать hook единственным слоем безопасности.

## Проверка

```bash
python3 ~/.hardcoding-agent-kit/hooks/smoke.py
```

Smoke не отправляет сеть и не читает реальные секреты.
