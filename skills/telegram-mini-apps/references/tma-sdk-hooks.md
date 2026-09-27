# @tma.js/sdk-react Hooks Reference

Полный справочник React hooks из @tma.js/sdk-react для работы с Telegram Mini Apps API.

## 🎯 Основные hooks

### useInitData()
Получение данных инициализации Mini App от Telegram.

```typescript
import { useInitData } from '@tma.js/sdk-react';

function MyComponent() {
  const initData = useInitData();
  
  // Данные пользователя
  const user = initData?.user;
  console.log(user?.id);          // ID пользователя
  console.log(user?.firstName);   // Имя
  console.log(user?.lastName);    // Фамилия
  console.log(user?.username);    // Username
  console.log(user?.languageCode); // Язык (ru, en, etc.)
  console.log(user?.isPremium);   // Telegram Premium статус
  
  // Дополнительные данные
  console.log(initData?.chatType);     // Тип чата
  console.log(initData?.chatInstance); // ID инстанса чата
  console.log(initData?.startParam);   // Параметр запуска
  console.log(initData?.authDate);     // Дата авторизации
  console.log(initData?.hash);         // Хеш для валидации
  
  return <div>Hello, {user?.firstName}!</div>;
}
```

### useLaunchParams()
Параметры запуска Mini App.

```typescript
import { useLaunchParams } from '@tma.js/sdk-react';

function MyComponent() {
  const launchParams = useLaunchParams();
  
  console.log(launchParams.platform);    // tdesktop, ios, android, etc.
  console.log(launchParams.version);     // Версия Telegram
  console.log(launchParams.botInline);   // Запущен через inline режим
  console.log(launchParams.startParam);  // Параметр из deep link
  
  return <div>Platform: {launchParams.platform}</div>;
}
```

### useThemeParams()
Параметры темы Telegram для адаптации UI.

```typescript
import { useThemeParams } from '@tma.js/sdk-react';

function ThemedComponent() {
  const themeParams = useThemeParams();
  
  return (
    <div style={{
      backgroundColor: themeParams.bgColor,
      color: themeParams.textColor,
    }}>
      <button style={{
        backgroundColor: themeParams.buttonColor,
        color: themeParams.buttonTextColor,
      }}>
        Кнопка
      </button>
      <a style={{ color: themeParams.linkColor }}>
        Ссылка
      </a>
    </div>
  );
}
```

**Доступные цвета темы:**
- `bgColor` — фон приложения
- `textColor` — основной текст
- `hintColor` — подсказки
- `linkColor` — ссылки
- `buttonColor` — фон кнопок
- `buttonTextColor` — текст кнопок
- `secondaryBgColor` — вторичный фон
- `headerBgColor` — фон заголовка
- `accentTextColor` — акцентный текст
- `sectionBgColor` — фон секций
- `sectionHeaderTextColor` — текст заголовков секций
- `subtitleTextColor` — подзаголовки
- `destructiveTextColor` — деструктивные действия

## 🔘 UI Components Hooks

### useMainButton()
Управление главной кнопкой внизу экрана.

```typescript
import { useMainButton } from '@tma.js/sdk-react';

function MyComponent() {
  const mainButton = useMainButton();
  
  useEffect(() => {
    // Настроить кнопку
    mainButton.setParams({
      text: 'Продолжить',
      isVisible: true,
      isEnabled: true,
      isLoaderVisible: false,
      color: '#5288c1',
      textColor: '#ffffff',
    });
    
    // Обработчик клика
    const handleClick = () => {
      mainButton.showLoader();
      // Выполнить действие
      setTimeout(() => {
        mainButton.hideLoader();
      }, 1000);
    };
    
    mainButton.on('click', handleClick);
    
    return () => {
      mainButton.off('click', handleClick);
      mainButton.hide();
    };
  }, []);
  
  return <div>Контент</div>;
}
```

### useBackButton()
Кнопка "Назад" в заголовке.

```typescript
import { useBackButton } from '@tma.js/sdk-react';
import { useRouter } from 'next/navigation';

function MyComponent() {
  const backButton = useBackButton();
  const router = useRouter();
  
  useEffect(() => {
    backButton.show();
    
    const handleClick = () => {
      router.back();
    };
    
    backButton.on('click', handleClick);
    
    return () => {
      backButton.off('click', handleClick);
      backButton.hide();
    };
  }, []);
  
  return <div>Страница с кнопкой назад</div>;
}
```

### useSettingsButton()
Кнопка настроек в заголовке.

```typescript
import { useSettingsButton } from '@tma.js/sdk-react';

function MyComponent() {
  const settingsButton = useSettingsButton();
  
  useEffect(() => {
    settingsButton.show();
    
    const handleClick = () => {
      // Открыть настройки
      console.log('Settings clicked');
    };
    
    settingsButton.on('click', handleClick);
    
    return () => {
      settingsButton.off('click', handleClick);
      settingsButton.hide();
    };
  }, []);
  
  return <div>Контент</div>;
}
```

### usePopup()
Показ нативных попапов Telegram.

```typescript
import { usePopup } from '@tma.js/sdk-react';

function MyComponent() {
  const popup = usePopup();
  
  const showConfirm = async () => {
    const result = await popup.open({
      title: 'Подтверждение',
      message: 'Вы уверены?',
      buttons: [
        { id: 'cancel', type: 'cancel' },
        { id: 'ok', type: 'ok' },
      ],
    });
    
    if (result === 'ok') {
      console.log('Подтверждено');
    }
  };
  
  return <button onClick={showConfirm}>Показать попап</button>;
}
```

## 📱 Device & Platform Hooks

### useViewport()
Информация о viewport и управление расширением.

```typescript
import { useViewport } from '@tma.js/sdk-react';

function MyComponent() {
  const viewport = useViewport();
  
  useEffect(() => {
    // Расширить на весь экран
    if (!viewport.isExpanded) {
      viewport.expand();
    }
  }, []);
  
  return (
    <div>
      <p>Высота: {viewport.height}px</p>
      <p>Ширина: {viewport.width}px</p>
      <p>Расширен: {viewport.isExpanded ? 'Да' : 'Нет'}</p>
      <p>Стабильная высота: {viewport.stableHeight}px</p>
    </div>
  );
}
```

### useHapticFeedback()
Тактильная обратная связь (вибрация).

```typescript
import { useHapticFeedback } from '@tma.js/sdk-react';

function MyComponent() {
  const haptic = useHapticFeedback();
  
  const handleClick = () => {
    // Лёгкая вибрация
    haptic.impactOccurred('light'); // light, medium, heavy, rigid, soft
  };
  
  const handleSuccess = () => {
    // Вибрация успеха
    haptic.notificationOccurred('success'); // success, warning, error
  };
  
  const handleSelection = () => {
    // Вибрация при выборе
    haptic.selectionChanged();
  };
  
  return (
    <div>
      <button onClick={handleClick}>Клик</button>
      <button onClick={handleSuccess}>Успех</button>
      <button onClick={handleSelection}>Выбор</button>
    </div>
  );
}
```

### useClosingBehavior()
Управление поведением при закрытии Mini App.

```typescript
import { useClosingBehavior } from '@tma.js/sdk-react';

function MyComponent() {
  const closingBehavior = useClosingBehavior();
  
  useEffect(() => {
    // Показать подтверждение при закрытии
    closingBehavior.enableConfirmation();
    
    return () => {
      closingBehavior.disableConfirmation();
    };
  }, []);
  
  return <div>Контент с подтверждением закрытия</div>;
}
```

## 💳 Payment & Invoice Hooks

### useInvoice()
Работа с платежами через Telegram.

```typescript
import { useInvoice } from '@tma.js/sdk-react';

function ShopComponent() {
  const invoice = useInvoice();
  
  const handleBuy = async () => {
    try {
      const result = await invoice.open({
        url: 'https://t.me/$invoice_link_from_bot',
      });
      
      if (result.status === 'paid') {
        console.log('Оплата успешна');
      } else if (result.status === 'cancelled') {
        console.log('Оплата отменена');
      } else if (result.status === 'failed') {
        console.log('Ошибка оплаты');
      }
    } catch (error) {
      console.error('Ошибка открытия инвойса:', error);
    }
  };
  
  return <button onClick={handleBuy}>Купить за 100₽</button>;
}
```

## 🔗 Navigation & Links Hooks

### useUtils()
Утилиты для работы с ссылками и QR-кодами.

```typescript
import { useUtils } from '@tma.js/sdk-react';

function MyComponent() {
  const utils = useUtils();
  
  const openLink = () => {
    // Открыть ссылку в браузере
    utils.openLink('https://example.com');
  };
  
  const openTelegramLink = () => {
    // Открыть Telegram ссылку
    utils.openTelegramLink('https://t.me/username');
  };
  
  const scanQR = async () => {
    // Сканировать QR код
    try {
      const result = await utils.readTextFromClipboard();
      console.log('QR данные:', result);
    } catch (error) {
      console.error('Ошибка сканирования:', error);
    }
  };
  
  return (
    <div>
      <button onClick={openLink}>Открыть ссылку</button>
      <button onClick={openTelegramLink}>Открыть Telegram</button>
      <button onClick={scanQR}>Сканировать QR</button>
    </div>
  );
}
```

### useCloudStorage()
Хранилище данных в облаке Telegram.

```typescript
import { useCloudStorage } from '@tma.js/sdk-react';

function MyComponent() {
  const cloudStorage = useCloudStorage();
  
  const saveData = async () => {
    await cloudStorage.setItem('user_settings', JSON.stringify({
      theme: 'dark',
      language: 'ru',
    }));
  };
  
  const loadData = async () => {
    const data = await cloudStorage.getItem('user_settings');
    if (data) {
      const settings = JSON.parse(data);
      console.log(settings);
    }
  };
  
  const deleteData = async () => {
    await cloudStorage.removeItem('user_settings');
  };
  
  return (
    <div>
      <button onClick={saveData}>Сохранить</button>
      <button onClick={loadData}>Загрузить</button>
      <button onClick={deleteData}>Удалить</button>
    </div>
  );
}
```

## 🎨 Advanced Hooks

### useSwipeBehavior()
Управление жестом свайпа для закрытия.

```typescript
import { useSwipeBehavior } from '@tma.js/sdk-react';

function MyComponent() {
  const swipeBehavior = useSwipeBehavior();
  
  useEffect(() => {
    // Отключить свайп для закрытия
    swipeBehavior.disableVerticalSwipe();
    
    return () => {
      swipeBehavior.enableVerticalSwipe();
    };
  }, []);
  
  return <div>Контент без свайпа</div>;
}
```

### useMiniApp()
Общие методы Mini App.

```typescript
import { useMiniApp } from '@tma.js/sdk-react';

function MyComponent() {
  const miniApp = useMiniApp();
  
  useEffect(() => {
    // Сообщить что приложение готово
    miniApp.ready();
    
    // Установить цвет заголовка
    miniApp.setHeaderColor('#5288c1');
    
    // Установить цвет фона
    miniApp.setBackgroundColor('#17212b');
  }, []);
  
  const closeApp = () => {
    miniApp.close();
  };
  
  return <button onClick={closeApp}>Закрыть приложение</button>;
}
```

## 📊 Best Practices

### 1. Всегда вызывай ready()
```typescript
const miniApp = useMiniApp();

useEffect(() => {
  miniApp.ready(); // Обязательно!
}, []);
```

### 2. Очищай обработчики событий
```typescript
useEffect(() => {
  const handler = () => console.log('clicked');
  mainButton.on('click', handler);
  
  return () => {
    mainButton.off('click', handler); // Важно!
  };
}, []);
```

### 3. Проверяй доступность функций
```typescript
if (haptic.isAvailable()) {
  haptic.impactOccurred('medium');
}
```

### 4. Используй TypeScript
```typescript
import type { InitData, User } from '@tma.js/sdk-react';

const user: User | undefined = initData?.user;
```

## 🔗 Полезные ссылки

- [Официальная документация](https://docs.telegram-mini-apps.com/packages/telegram-apps-sdk-react)
- [GitHub репозиторий](https://github.com/Telegram-Mini-Apps/telegram-apps)
- [Примеры использования](https://github.com/Telegram-Mini-Apps/nextjs-template)
