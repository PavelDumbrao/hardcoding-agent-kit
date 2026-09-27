---
name: hostinger-vps
description: Управление Hostinger VPS через SSH, Docker, systemd и PM2. Используй при live-аудите VPS, работе с контейнерами, сервисами, логами, портами и инфраструктурой пользователя.
---

> **Локальная рабочая версия (не для публикации):** `docs/live-vps-inventory.md` содержит реальные IP/домены/порты и полную карту VPS. Секреты в нём НЕ хранятся — только указатели «где смотреть» (env-файл + имена переменных). Перед шарингом скилла — заменить реальные значения на placeholders.


# Hostinger VPS Management

## Когда использовать
- Используй этот skill, когда задача касается VPS, Docker, systemd, PM2, сервисов или портов на сервере.
- Для любых архитектурных решений по VPS считай source of truth = live VPS + read-only аудит.
- Не полагайся только на старые markdown-файлы на Desktop, если не сверил их с сервером.

## Источник истины
- Полный подтверждённый inventory VPS смотри в `docs/live-vps-inventory.md`.
- Если есть расхождение между markdown и live VPS — верь live VPS.
- Перед изменениями сначала делай read-only аудит, потом уже предлагай правки.

## Подключение к серверу
```bash
ssh -i ~/.ssh/id_ed25519 <SSH_USER>@<VPS_IP>   # <VPS_HOST>
```

## Быстрый read-only аудит
```bash
# Активные контейнеры
docker ps

# Все контейнеры
docker ps -a

# Прослушиваемые порты
ss -tulpn | grep LISTEN

# Запущенные systemd-сервисы
systemctl list-units --type=service --state=running --no-pager

# PM2 процессы
pm2 list

# compose / env файлы
find /opt /docker -maxdepth 2 \( -name docker-compose.yml -o -name compose.yml -o -name compose.yaml -o -name .env -o -name "*.env" \)
```

## Доступные CLI-утилиты
- `ripgrep` установлен на `<VPS_HOST>` 2026-06-25: используй `rg` / `rg --files` для быстрого поиска по VPS вместо `grep`/`find`, когда это подходит задаче.
- Если `rg` неожиданно недоступен после смены сервера или образа, сначала проверь `command -v rg && rg --version`, затем ставь пакет `ripgrep`.

## Диагностика load, swap и dockerd
- Полный swap сам по себе не доказывает текущий дефицит RAM. Сопоставляй `free -h`, `vmstat 1 5`, `/proc/pressure/{cpu,io,memory}` и свежие `si/so`. Не делай `swapoff`, если занятый swap больше доступной RAM.
- Владельцев swap считай по `VmSwap`/`VmRSS` из `/proc/<pid>/status` и группируй по `/proc/<pid>/cgroup`. Не печатай полные argv: в них могут быть prompts и чувствительные данные.
- При аномальном load проверяй `sar -u ALL`, `sar -q` и `sar -d`. Высокий `%steal` при низких `%usr/%sys` означает конкуренцию на гипервизоре, а не локальный CPU-процесс.
- `ps %CPU` усредняет CPU за жизнь процесса. Для текущего `dockerd` снимай delta `/proc/<pid>/stat` за 5 секунд или используй `pidstat`.
- Если `dockerd` держит ядро без build/pull/compose, проверь зависшие `docker logs` без `--follow`. Штатный `SIGUSR1` создаёт `/var/run/docker/goroutine-stacks-*.log`; runnable stack в `pkg/tailfile` указывает на зацикленный logs client. Завершай только подтверждённый stale client и его оболочку, затем повторно измеряй CPU.
- Non-follow `docker logs` старше пяти минут уже не является нормальной разовой диагностикой. Watchdog может завершать такие процессы, включая переподчинённые PID 1 после смерти Desktop Commander; `docker logs -f/--follow` не трогать.
- Не запускай широкий `du /` на нагруженном VPS. Сначала используй известные каталоги и точечные `du -xhd1 <path>`.

## Docker операции
```bash
# Просмотр логов
docker logs <container_name> --tail 100
docker logs <container_name> -f

# Проверка конфигурации compose
cd /opt/<service> && docker compose config

# Перезапуск сервиса
cd /opt/<service> && docker compose restart
```

## Systemd / процессы
```bash
# Статус сервиса
systemctl status <service> --no-pager

# Включён ли сервис
systemctl is-enabled <service>

# Активен ли сервис
systemctl is-active <service>

# Проверить конкретный PID
ps -p <pid> -o pid,ppid,user,cmd --no-headers
```

## Правила безопасности
- Не копируй реальные секреты в markdown, rules, skill docs или отчёты.
- Если нужно описать секрет — фиксируй путь / env key, но не значение.
- Для risky-действий (restart, edit, deploy) сначала делай read-only аудит и объясняй, что меняется.
- Если сервис «есть на диске», это не значит, что он реально активен в проде.

## NotebookLM REST, MCP и Android backend

- Для NotebookLM используй основной skill `notebooklm-cli`; этот раздел отвечает только за VPS-размещение.
- Live-аудит 19.09.2026: legacy runtime находится в `/opt/notebooklm/venv`, wrapper `/usr/local/bin/nblm`, версия `0.7.2`; `nblm-refresh.timer` inactive/disabled, Web auth возвращает `token_fetch=false`.
- Не обновляй legacy venv на месте. Ставь `0.8.2` side-by-side в `/opt/notebooklm/venv-082` с rollback на старый wrapper.
- Порт `8000` занят `telegram-api-engine.service`; рекомендуемые loopback endpoints: MCP `127.0.0.1:9420`, REST `127.0.0.1:9421`.
- REST bearer token хранится в `/etc/notebooklm/rest.token`, mode `0600`, передаётся через `--token-file`. Само значение не указывать в unit, argv или логах.
- Android backend требует `master_token.json`. Рекомендуется выделенный аккаунт; для профиля `hostinger` 19.09.2026 Павел явно разрешил свой текущий аккаунт после объяснения риска. Используются отдельный Linux user `notebooklm`, закрытый профиль, credential files `0600`.
- Проверено 19.09.2026: master token получен через Comet и передан по SSH; VPS `auth refresh` самостоятельно создал Web storage. Android `list`, REST `/v1/notebooks` (200 с токеном, 401 без), MCP initialize/38 tools/server_info/notebook_list прошли. `notebooklm-rest.service` и `notebooklm-mcp.service` enabled/active, NRestarts=0 при проверке, оба bind loopback. Старый wrapper `nblm` остаётся на 0.7.2.
- REST/MCP по умолчанию держать на loopback. Публичный reverse proxy, tunnel, OAuth или bearer exposure требуют отдельного approval и threat review.
- Перед запуском: версия `0.8.2`, 38 MCP tools, auth smoke, Android `list --limit 1 --json`, REST authenticated read, MCP `server_info`, занятые порты, systemd sandboxing.

### Live NotebookLM snapshot, 23.09.2026

В этом контуре notebooklm-py 0.8.2 установлен side-by-side. Master token восстановлен и проверен, mode 0600, owner notebooklm. Android CLI list/source search/research discover, REST authenticated read и MCP initialize/tools/list/server_info/notebook_list прошли. REST/MCP active на loopback с Android backend; Web auth timer оставлен резервом около 15 минут. Android bearer короткоживущий и автоматически получается из master token; Web cookies являются отдельным резервным путём. Drop-in 30-android-backend.conf действует поверх сохранённого 20-web-backend.conf; откат возможен снятием 30-android drop-in. NRestarts MCP хранит историческое значение 6 454, новых рестартов в окне проверки не прибавилось.

Этот snapshot быстро устаревает. Перед каждым VPS изменением сверяй live systemd и auth probe; локальные README и inventory не доказывают актуальное состояние.

## Что важно помнить про этот VPS
- Здесь активно используются **Docker**, **systemd**, **PM2** и отдельные процессы без systemd.
- На сервере есть как продуктовые сервисы, так и старые директории / архивы / тестовые остатки.
- При документировании разделяй:
  1. активные сервисы,
  2. внутренние wrapper/agent-сервисы,
  3. директории/архивы/остатки, не подтверждённые как активные.
