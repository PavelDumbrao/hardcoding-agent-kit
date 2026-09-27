# Live VPS Inventory & Карта — Hostinger `<VPS_HOST>`

> Подтверждённый inventory по live read-only аудиту.
> Обновлено: **2026-06-19** · Source of truth = живой VPS (не этот файл).
> ⚠️ Локальная рабочая копия с реальными значениями — **не шарить публично**. Секреты здесь НЕ хранятся, только указатели «где смотреть».

## Подключение
- Хост: `<VPS_HOST>` · IP: `<VPS_IP>` · OS: Ubuntu (`6.8.0-101-generic`) · 4 vCPU / 15 GB / диск 193 GB (~35%)
- SSH: `ssh -i ~/.ssh/id_ed25519 <SSH_USER>@<VPS_IP>`
- Docker **29.1.3**. Демон капризный: overlay2-GC медленный (prune/rmi крупных образов идут минутами и подвешивают `docker ps`); боевое при этом продолжает работать.

## Архитектура (слои)
```
Интернет (<VPS_IP>)
   └─ Traefik :80/:443 (контейнер n8n-traefik-1, сеть n8n_default) — TLS-edge для всех доменов
        ├─ боевое: Клуб (proai-stack) · LiteLLM · Billing
        ├─ инфра: n8n · агент-врапперы · Cline/Lovable bot-фабрика
        └─ контент/утилиты: search · shlink · fathom · postforme · telegram-api-engine
   Данные: своя PostgreSQL у каждого стека; Redis общий у n8n
```
**n8n_default — общая сеть-шина**: ~24 контейнера в ней (Traefik роутит туда, сервисы общаются напрямую). Изолированные стеки имеют ещё и свою сеть.

## Edge — публичные домены (статус на 2026-06-19)
| Домен | → сервис | Статус |
|---|---|---|
| `api.proaicommunity.online` | LiteLLM шлюз (:32779) | ✅ 200 |
| `club.proaicommunity.online` / `club-api.` | Клуб (miniapp / backend) | ✅ 200 |
| `billing.proaicommunity.online` | Billing Portal | ✅ 200 |
| `shlink.proaicommunity.online` | Shlink Web UI | ✅ 200 |
| `connect.proaicommunity.online` | connect-redirect (статика) | ✅ 200 |
| `radar.proaicommunity.online` | Content Radar AI (агент-сервис, `/opt/content-radar-ai`) | ✅ 200 (подтверждено 2026-09-22) |
| `cliproxy.<VPS_HOST>.hstgr.cloud` | CLIProxyAPI | ✅ 200 |
| `s.proaicommunity.online` | Shlink короткие ссылки (:32775) | ⚠️ 000 — движок жив, edge/cert битый |
| `fathom.` · `fathom-dev.` | Fathom Hub | ⚠️ 000 — backend ↑, edge/cert битый |
| `n8n-ffmpeg.<VPS_HOST>.hstgr.cloud` | n8n | ⚠️ 000 — n8n ↑, edge/cert битый |
| `claude-cli.` / `gpt-cli.<VPS_HOST>.hstgr.cloud` | Claude/Codex CLI relay | ⚠️ 000 / 404 |
| `mcp.proaicommunity.online` | postforme-mcp gateway | ⚠️ 404 (отвечает на путь, не на корень) |
| `app.proaicommunity.online` | proaicommunity-miniapp | ❌ 404 — контейнера НЕТ (мёртвый маршрут) |
| `hub.proaicommunity.online` | Open WebUI | ⏸ 404 — выключен намеренно |

## Кластеры сервисов (Docker)

### 💰 Клуб ProAiCommunity — боевой продукт (деньги)
`/opt/proai-stack` · сети `proai-stack_default` + `n8n_default`
| Контейнер | Что | Порт |
|---|---|---|
| proai-stack-backend-1 | API клуба | internal :3000 |
| proai-stack-bot-1 | @ProAiClubBot (polling) | — |
| proai-stack-miniapp-1 | Mini App (club.) | :80 |
| proai-stack-postgres-1 | БД клуба | postgres:16-alpine |
- **Зависит от LiteLLM**: `OPENAI_BASE_URL` / `CURATOR_LITELLM_BASE_URL` / `VIBE_AGENT_BASE_URL` → `https://api.proaicommunity.online/v1` (внутри: `http://litellm-xne6-litellm-1:4000`). Если LiteLLM лежит — AI-функции клуба не работают.
- **Оплаты**: Prodamus (`proaicommunity.payform.ru`). Поднимается/чинится watchdog'ом (cron `*/2 мин` `/opt/proai-stack/watchdog.sh`, делает `docker compose up -d` без `--build`).

### 🧠 LLM-шлюз LiteLLM — центральный AI-хаб
`/docker/litellm-xne6` · сеть `litellm-xne6_default` (+ litellm-1 в n8n_default)
| Контейнер | Что | Порт |
|---|---|---|
| litellm-xne6-litellm-1 | LiteLLM, 124 модели, `config.yaml` | :32779→4000 |
| litellm-xne6-litellm-db-1 | БД | postgres:16.1-alpine |
| litellm-xne6-{kimi,minimax,qwen}-gonka-helper-1 | sidecar-прокси gonka-моделей | :8012/8011/8013 |
- ⚙️ Грабли старта: `prisma migrate` зацикливался → фикс `DISABLE_SCHEMA_UPDATE=True` в `docker-compose.override.yml`. Старт ~3-4 мин (124 модели), не убивать раньше. Логи DEBUG-уровня — убрать `LITELLM_LOG` из override при следующем рестарте.
- Потребители: Клуб · proaicommunity-miniapp (`OPENAI_API_BASE_URL: http://litellm-xne6-litellm-1:4000/v1`) · cli-proxy (в сети litellm).
- Образ canary `main-stable` удалён 2026-06-19, бэкап в `/opt/backups/litellm-canary-backup-*`.

### ⚙️ n8n — автоматизация + владелец edge/сети
`/docker/n8n` · сеть `n8n_default`
n8n-1 (`127.0.0.1:5678`) · worker · runners-main/worker (внешние, 2.10.4) · ffmpeg (`rxchi1d/n8n-ffmpeg`) · postgres:15 (БД `n8ndb`) · redis:6 · **traefik** (:80/:443).
- Образ запинен в compose на `2.10.4` (в рантайме ещё `:latest` — применится при рестарте). БД n8n правил вручную (Codex) — следить за migration-warnings.

### 🤖 Agent-врапперы (Claude/Codex CLI как HTTP API)
| Сервис | Порт | Путь | Runtime | Edge |
|---|---|---|---|---|
| Claude CLI Wrapper | **0.0.0.0:8787** ⚠️ | `/opt/claude-cli-wrapper` | systemd+node | claude-cli.hstgr |
| Codex CLI Wrapper | `127.0.0.1:8788` (+bridge 172.17.0.1) | `/opt/codex-cli-wrapper` | systemd+node/python | gpt-cli.hstgr |
| Codex Wrapper | `*:3333` | (PM2 cline-wrapper) | node | — |
| CLIProxyAPI | `127.0.0.1:1455/8317` | `/opt/cliproxyapi` | Docker (litellm+n8n nets) | cliproxy.hstgr |
| claude/codex/proai-bot relay | internal | `/docker/*-relay`, `/opt/proai-bot-relay` | Caddy | через Traefik |

### 🏭 Cline / Lovable — фабрика Telegram-ботов
- PM2: `cline-wrapper` + `telegram-cline-bot` (online ~17д).
- `telegram-listener.service` → `/opt/telegram-bot/listener.sh` = бот **@OpenCline_bot** (эхо, build НЕ запускает; токен захардкожен ⚠️). Рядом `bot.js`.
- `/opt/lovable-telegram` = «Lovable для Telegram»: `lovable-orchestrator` (FastAPI :8095) + `lovable-service-bot` + `lovable-client-bot@…` — сборка клиентских ботов через cline-wrapper.

### 🔎 Search / контент
searxng `:8888` · scraper-server `:9111` · yt-transcript `:9222` · whisper-asr `:9000` (project `docker-compose`).
**invidious** (`/opt/invidious`): invidious + companion **выключены** (ждут оплату Evomi-прокси — `402 Payment Required`); invidious-db (postgres:14) поднята. Companion жжёт CPU (BotGuard PO-token), на этом боксе тяжёлый — см. отдельную заметку в памяти.

### 🛠 Утилиты / MCP
shlink (`:32775`/`:32776`, RoadRunner — воркеры урезаны до WEB=2/TASK=1 + cpus-cap в override) · fathom-hub (web+worker) · ticktick-mcp `:9333` · postforme-mcp (app+gateway; поднимать `docker compose -f docker-compose.remote.yml` или `docker start`) · agent-capture-api `:7788` · connect-redirect (статика connect.) · hyperframes-mcp-worker (systemd) · billing-portal (`127.0.0.1:8002`).

## Host-сервисы (вне Docker)
| Сервис | Порт | Тип |
|---|---|---|
| **Telegram API Engine** | `0.0.0.0:8000` ⚠️ | python/uvicorn (`/opt/telegram-api-engine`) — user-аккаунт, экспорт юзеров/групп (`/api/export/users/{id}` Bearer). Отдаёт PII по HTTP. |
| Claude CLI Wrapper | `0.0.0.0:8787` | systemd+node |
| Codex CLI Wrapper (+bridge) | `127.0.0.1:8788`, `:3333` | systemd |
| lovable-orchestrator | `127.0.0.1:8095` | systemd uvicorn |
| hyperframes-mcp-worker | — | systemd |
| cline-wrapper, telegram-cline-bot | `:3333` | PM2 |

## Слой данных
PostgreSQL изолированы по стекам: `pg15`→n8n (`n8ndb`) · `pg16.1`→LiteLLM · `pg16`→Клуб · `pg14`→Invidious. **Redis:6** — общий у n8n. БД наружу не торчат (только в своих сетях). Тома: `*_pgdata`, `n8n_*`, `shlink-by0k_shlink-data`, `invidious-*`, `traefik_data`.

## Планировщик (cron root)
- `*/2 * * * *` `/opt/proai-stack/watchdog.sh` — сторож клуба.
- `0 */6 * * *` чистка старых `proai_msg*.mp4` экспортов.
- `0 4 * * 0` `/opt/invidious/cleanup-db.sh` — еженедельная чистка БД invidious.

## 🔐 Секреты — где искать (значения НЕ хранить здесь)
| Сервис | Файл / место | Ключевые переменные |
|---|---|---|
| LiteLLM | `/docker/litellm-xne6/.env` | `LITELLM_MASTER_KEY`, `DB_PASSWORD`, `UI_PASSWORD`, провайдеры `JENIYA_*`/`POLO_*`/`ANIDEAAI_*`/`GENGRUIHUAN_*`/`GRSAI_API_KEY`, `TAVILY_API_KEY` |
| Клуб proai-stack | `/opt/proai-stack/.env` | `BOT_TOKEN`, `OPENAI_API_KEY`, `POSTGRES_PASSWORD`, `PRODAMUS_SECRET_KEY`, `ADMIN_TOKEN`, `INTERNAL_KEY`, `SESSION_SECRET`, `TG_ENGINE_KEY`, `SUPADATA_API_KEY`, `YOUTUBE_API_KEY` и др. |
| Telegram API Engine | `/opt/telegram-api-engine/.env` | `API_KEY` (Bearer для :8000), `TELEGRAM_API_ID/HASH`, `ADMIN_USER/PASS`, `KIE_API_KEY`, `VIDEO_NOTE_BOT_TOKEN` |
| Shlink | `/docker/shlink-by0k/.env` | `INITIAL_API_KEY` |
| Scraper | `/opt/scraper-server/docker-compose.yml` | `FEWSATS_SCRAPER_API_KEY` |
| Evomi proxy (invidious) | `/opt/invidious/docker-compose.yml` (inline) | `PROXY` (резидентный прокси, аккаунт исчерпан — 402) |

⚠️ **Захардкожено в открытом виде (вынести в env + ревокнуть):**
- `/opt/telegram-bot/listener.sh` — `BOT_TOKEN` (@OpenCline_bot) inline.
- `/opt/invidious/docker-compose.yml` — `hmac_key`, db `password`, `companion_key`, `PROXY` inline.
- `:8787` Claude-wrapper слушает `0.0.0.0` (наружу); `:8000` Telegram API Engine отдаёт PII по HTTP. Bearer-токен этого API лежит открытым в n8n-ноде.

## Риски / хвосты
1. **Безопасность**: открытые `:8787`/`:8000`, PII по HTTP, захардкоженные токены (см. выше) → закрыть фаерволом/internal, увести за TLS, ревокнуть/в env.
2. **Сети-призраки** (пустые, от удалённых сервисов): `chroma-hnuc`, `docker-metube`, `metube-downloader`, `openclaw-ztxp` → `docker network rm`.
3. **Мёртвые маршруты**: `app.` (нет контейнера), `s.`/`fathom.`/`n8n-ffmpeg.`/`claude-cli.` (000 — cert/route) → чинить cert или убрать из Traefik.
4. **Дубль miniapp**: `proaicommunity-miniapp` (app., мёртвый) vs `proai-stack-miniapp` (club., боевой).
5. **Остатки на диске**: `/opt/metube` (только downloads), `/opt/postforme-mcp-server.prev`, `/docker/billing-test*`, `*_archive` — кандидаты на уборку.
6. **Docker-образы**: ~47 GB, но реального мусора почти нет (слои общие); крупное освобождение — только снос образов выключенных сервисов.

## Content Radar AI (добавлено 2026-09-22)

- Каталог: `/opt/content-radar-ai`, compose-project `content-radar-ai`, сети `internal` (`10.247.0.0/24`) + `n8n_default`.
- Контейнеры: `content-radar-ai-api-1` (FastAPI, :8000 внутри), `content-radar-ai-db-1` (pgvector/pg16).
- Edge: Traefik-роутер `radar` → `https://radar.proaicommunity.online`, certresolver `mytlschallenge`.
- LLM: внутренний LiteLLM `http://litellm-xne6-litellm-1:4000`, рабочая модель `gemini-2.5-flash`.
- Git на VPS: deploy key read-only `~/.ssh/id_ed25519_ghdeploy_radar`, alias `github-radar` в `~/.ssh/config`.
- Секреты: `/opt/content-radar-ai/.env` (mode 600): `POSTGRES_PASSWORD`, `LITELLM_API_KEY`, `YOUTUBE_API_KEY`, `VK_ACCESS_TOKEN`.
- Обновление: `cd /opt/content-radar-ai && git pull --ff-only && docker compose up -d --build`.

### Ограничения хоста, важные для новых сервисов (подтверждено 2026-09-22)

- **Пул адресов Docker исчерпан.** Новый compose без явной подсети падает с
  `all predefined address pools have been fully subnetted`. Нужно задавать
  `ipam.config.subnet`. Занято: `172.17-172.31`, `192.168.0-240` (шаг 16),
  `10.252-10.254`; свободно `10.240-10.251`.
- **Модели LiteLLM для приложений** (проверено с master key): стабильно с tool calling —
  `gemini-2.5-flash` (3/3) и `proai-max` (3/3); `claude-haiku-4-5` отвечает, но при
  нагрузке уходит в фоллбек-группы и отдаёт `AUTH_GROUP_FORBIDDEN`; `gpt-5.4-mini`
  таймаутит; `gpt-5.4-nano` ловит 429.
- **Порты наружу не публиковать.** Только Traefik + `n8n_default` через labels.

## Быстрые read-only команды
```bash
docker ps -a --format '{{.Names}}|{{.Status}}|{{.Networks}}'   # контейнеры+сети
ss -tulpn | grep LISTEN                                        # порты→процесс
systemctl list-units --type=service --state=running --no-pager # host-сервисы
pm2 list
crontab -l
for n in $(docker network ls --format '{{.Name}}'); do echo "== $n =="; docker network inspect "$n" --format '{{range .Containers}}{{.Name}} {{end}}'; done
grep -rE 'rule=Host' /opt /docker --include=*.yml --exclude-dir=node_modules   # edge-маршруты
```

## 🔐 Перенос секретов 2026-09-05 (значения НЕ здесь)
| Сервис | Где теперь лежит | Переменные | Примечание |
|---|---|---|---|
| Invidious | `/opt/invidious/.env` (600) | `INVIDIOUS_DB_PASSWORD`, `INVIDIOUS_HMAC_KEY`, `INVIDIOUS_COMPANION_KEY`, `INVIDIOUS_PROXY` | compose ссылается `${…}`; рендер `docker compose config` идентичен прежнему; бэкап старого compose `/opt/invidious/backups-secrets-20260905/` (700) |
| Shlink | `/docker/shlink-by0k/.env` (600) | `SHLINK_WEB_API_KEY` (новый ключ `shlink-web-20260905` для UI), `INITIAL_API_KEY` (первичный admin-ключ, остаётся валидным в БД, из compose убран) | список ключей: `docker exec shlink-by0k-shlink-1 shlink api-key:list`; бэкап compose/.env в `backups-secrets-20260905/` |
| Roma Content Studio (удалён 05.09) | архив `/opt/archive/decommission-20260905/roma-content-studio-20260905.tar.zst` (600) | внутри `secrets.json` (access_token, ключ Orion) и `vlm.env` | сервис, юниты, edge и `/opt/roma-content-studio` удалены; порт 8099 закрыт |
| LiteLLM | `/docker/litellm-xne6/.env` | как раньше (см. таблицу выше); бэкапы конфигов `/docker/litellm-xne6/backups-20260905/` | `general_settings` + `mem_limit 5g` добавлены 05.09 |

## 🔥 Сеть после 2026-09-05
- ufw: **default deny incoming**; allow 22/80/443/2222; allow from 172.16.0.0/12, 192.168.0.0/16, 10.0.0.0/8 (docker-bridge → сервисы хоста, напр. движок :8000 и fashionmatrix :3100); deny eth0 → 3100/8000/8787/3333.
- Docker-порты: 3001/7788/32775/32776/32779 → bind `127.0.0.1`; 8888/9111/9222/9333 остаются 0.0.0.0 (n8n зовёт их по публичному IP), но дропаются с eth0 правилами `DOCKER-USER` в `/etc/ufw/after.rules` (`conntrack --ctorigdstport`). Новый публикуемый порт по умолчанию ОТКРЫТ наружу — добавлять bind 127.0.0.1 или строку в after.rules.
- daemon.json: `live-restore: true`. Бэкапы: `/opt/backups/bin/*.sh`, cron `/etc/cron.d/db-backups` (03:40/03:45), каталоги `/opt/backups/{db,engine}`.

## tinyproxy для Claude Code с мака (2026-09-05)
- `tinyproxy` 1.11.1 (apt), systemd unit `tinyproxy`, слушает ТОЛЬКО 127.0.0.1:3128 (`Allow 127.0.0.1`), конфиг `/etc/tinyproxy/tinyproxy.conf` (оригинал `.orig`). Наружу не виден (ufw default deny). Используется через SSH-туннель с мака (`~/Library/LaunchAgents/com.pavel.claude-proxy-tunnel.plist`) как выделенный канал Claude Code → Anthropic с литовского IP VPS. Остановить: `systemctl disable --now tinyproxy`.
