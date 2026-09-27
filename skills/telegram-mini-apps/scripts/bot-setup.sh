#!/bin/bash

# Скрипт автоматизации настройки Telegram бота для Mini App
# Использование: ./bot-setup.sh

set -e

echo "🤖 Настройка Telegram бота для Mini App"
echo "========================================"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Проверка наличия необходимых инструментов
check_dependencies() {
    print_info "Проверка зависимостей..."
    
    if ! command -v curl &> /dev/null; then
        print_error "curl не установлен. Установите curl и попробуйте снова."
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        print_warning "jq не установлен. Рекомендуется установить для лучшего форматирования JSON."
        print_info "macOS: brew install jq"
        print_info "Ubuntu: sudo apt install jq"
    fi
    
    print_success "Все зависимости установлены"
}

# Получение токена бота
get_bot_token() {
    echo ""
    print_info "Шаг 1: Получение токена бота"
    echo ""
    echo "Если у вас ещё нет бота:"
    echo "1. Открой Telegram и найди @BotFather"
    echo "2. Отправь команду /newbot"
    echo "3. Следуй инструкциям для создания бота"
    echo "4. Скопируй токен, который даст BotFather"
    echo ""
    
    read -p "Введи токен бота: " BOT_TOKEN
    
    if [ -z "$BOT_TOKEN" ]; then
        print_error "Токен не может быть пустым"
        exit 1
    fi
    
    # Проверка токена
    print_info "Проверка токена..."
    RESPONSE=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe")
    
    if echo "$RESPONSE" | grep -q '"ok":true'; then
        BOT_USERNAME=$(echo "$RESPONSE" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
        print_success "Токен валиден! Бот: @${BOT_USERNAME}"
    else
        print_error "Неверный токен бота"
        exit 1
    fi
}

# Получение URL Mini App
get_mini_app_url() {
    echo ""
    print_info "Шаг 2: URL Mini App"
    echo ""
    echo "Введи URL твоего Mini App (должен начинаться с https://)"
    echo "Примеры:"
    echo "  - https://your-app.vercel.app"
    echo "  - https://your-domain.com"
    echo "  - https://localhost:3000 (для разработки)"
    echo ""
    
    read -p "URL Mini App: " MINI_APP_URL
    
    if [ -z "$MINI_APP_URL" ]; then
        print_error "URL не может быть пустым"
        exit 1
    fi
    
    if [[ ! "$MINI_APP_URL" =~ ^https:// ]]; then
        print_error "URL должен начинаться с https://"
        exit 1
    fi
    
    print_success "URL принят: $MINI_APP_URL"
}

# Настройка Menu Button
setup_menu_button() {
    echo ""
    print_info "Шаг 3: Настройка Menu Button"
    echo ""
    
    read -p "Введи текст для кнопки меню (по умолчанию: 'Открыть'): " BUTTON_TEXT
    BUTTON_TEXT=${BUTTON_TEXT:-"Открыть"}
    
    print_info "Настройка Menu Button..."
    
    # Создание JSON для запроса
    JSON_DATA=$(cat <<EOF
{
  "menu_button": {
    "type": "web_app",
    "text": "$BUTTON_TEXT",
    "web_app": {
      "url": "$MINI_APP_URL"
    }
  }
}
EOF
)
    
    RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setChatMenuButton" \
        -H "Content-Type: application/json" \
        -d "$JSON_DATA")
    
    if echo "$RESPONSE" | grep -q '"ok":true'; then
        print_success "Menu Button настроен!"
    else
        print_error "Ошибка настройки Menu Button"
        echo "$RESPONSE"
        exit 1
    fi
}

# Настройка команд бота
setup_bot_commands() {
    echo ""
    print_info "Шаг 4: Настройка команд бота"
    echo ""
    
    read -p "Хочешь настроить команды бота? (y/n): " SETUP_COMMANDS
    
    if [[ "$SETUP_COMMANDS" =~ ^[Yy]$ ]]; then
        print_info "Настройка команд..."
        
        COMMANDS='[
          {"command": "start", "description": "Запустить бота"},
          {"command": "help", "description": "Помощь"},
          {"command": "app", "description": "Открыть Mini App"}
        ]'
        
        RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setMyCommands" \
            -H "Content-Type: application/json" \
            -d "{\"commands\": $COMMANDS}")
        
        if echo "$RESPONSE" | grep -q '"ok":true'; then
            print_success "Команды настроены!"
        else
            print_warning "Не удалось настроить команды (не критично)"
        fi
    fi
}

# Сохранение конфигурации
save_config() {
    echo ""
    print_info "Шаг 5: Сохранение конфигурации"
    echo ""
    
    read -p "Сохранить конфигурацию в .env файл? (y/n): " SAVE_ENV
    
    if [[ "$SAVE_ENV" =~ ^[Yy]$ ]]; then
        ENV_FILE=".env.local"
        
        if [ -f "$ENV_FILE" ]; then
            print_warning "Файл $ENV_FILE уже существует"
            read -p "Перезаписать? (y/n): " OVERWRITE
            if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
                print_info "Пропускаем сохранение"
                return
            fi
        fi
        
        cat > "$ENV_FILE" <<EOF
# Telegram Bot Configuration
BOT_TOKEN=$BOT_TOKEN
MINI_APP_URL=$MINI_APP_URL
BOT_USERNAME=$BOT_USERNAME

# Next.js
NEXT_PUBLIC_BOT_USERNAME=$BOT_USERNAME
EOF
        
        print_success "Конфигурация сохранена в $ENV_FILE"
        print_warning "Не забудь добавить .env.local в .gitignore!"
    fi
}

# Вывод итоговой информации
print_summary() {
    echo ""
    echo "========================================"
    print_success "Настройка завершена!"
    echo "========================================"
    echo ""
    echo "📋 Информация о боте:"
    echo "   Username: @${BOT_USERNAME}"
    echo "   Mini App URL: ${MINI_APP_URL}"
    echo ""
    echo "🚀 Следующие шаги:"
    echo "   1. Открой Telegram и найди @${BOT_USERNAME}"
    echo "   2. Нажми на кнопку меню (☰) внизу"
    echo "   3. Твой Mini App должен открыться!"
    echo ""
    echo "💡 Полезные команды:"
    echo "   - Проверить бота: curl https://api.telegram.org/bot${BOT_TOKEN}/getMe"
    echo "   - Получить обновления: curl https://api.telegram.org/bot${BOT_TOKEN}/getUpdates"
    echo ""
    echo "📚 Документация:"
    echo "   - Telegram Bot API: https://core.telegram.org/bots/api"
    echo "   - Mini Apps: https://docs.telegram-mini-apps.com/"
    echo ""
}

# Основная функция
main() {
    check_dependencies
    get_bot_token
    get_mini_app_url
    setup_menu_button
    setup_bot_commands
    save_config
    print_summary
}

# Запуск скрипта
main
