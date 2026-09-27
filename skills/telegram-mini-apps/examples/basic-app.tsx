// Минимальный рабочий пример Telegram Mini App
// Показывает данные пользователя и демонстрирует основные возможности SDK

'use client';

import { useEffect, useState } from 'react';
import {
  useInitData,
  useLaunchParams,
  useThemeParams,
  useMainButton,
  useBackButton,
  useHapticFeedback,
  useMiniApp,
  useViewport,
} from '@tma.js/sdk-react';

export default function BasicTelegramMiniApp() {
  const initData = useInitData();
  const launchParams = useLaunchParams();
  const themeParams = useThemeParams();
  const mainButton = useMainButton();
  const backButton = useBackButton();
  const haptic = useHapticFeedback();
  const miniApp = useMiniApp();
  const viewport = useViewport();
  
  const [counter, setCounter] = useState(0);
  const [isExpanded, setIsExpanded] = useState(false);

  // Инициализация Mini App
  useEffect(() => {
    // Сообщить Telegram что приложение готово
    miniApp.ready();
    
    // Установить цвета заголовка и фона
    miniApp.setHeaderColor(themeParams.headerBgColor || '#17212b');
    miniApp.setBackgroundColor(themeParams.bgColor || '#17212b');
    
    // Расширить viewport на весь экран
    if (!viewport.isExpanded) {
      viewport.expand();
      setIsExpanded(true);
    }
  }, []);

  // Настройка главной кнопки
  useEffect(() => {
    mainButton.setParams({
      text: 'Отправить данные',
      isVisible: true,
      isEnabled: true,
      color: themeParams.buttonColor || '#5288c1',
      textColor: themeParams.buttonTextColor || '#ffffff',
    });

    const handleMainButtonClick = () => {
      // Вибрация при клике
      if (haptic.isAvailable()) {
        haptic.impactOccurred('medium');
      }
      
      // Показать loader
      mainButton.showLoader();
      
      // Имитация отправки данных
      setTimeout(() => {
        mainButton.hideLoader();
        
        // Показать уведомление об успехе
        if (haptic.isAvailable()) {
          haptic.notificationOccurred('success');
        }
        
        alert('Данные отправлены!');
      }, 1000);
    };

    mainButton.on('click', handleMainButtonClick);

    return () => {
      mainButton.off('click', handleMainButtonClick);
      mainButton.hide();
    };
  }, []);

  // Настройка кнопки "Назад"
  useEffect(() => {
    if (counter > 0) {
      backButton.show();
      
      const handleBackClick = () => {
        if (haptic.isAvailable()) {
          haptic.impactOccurred('light');
        }
        setCounter(prev => Math.max(0, prev - 1));
      };
      
      backButton.on('click', handleBackClick);
      
      return () => {
        backButton.off('click', handleBackClick);
      };
    } else {
      backButton.hide();
    }
  }, [counter]);

  const handleIncrement = () => {
    if (haptic.isAvailable()) {
      haptic.impactOccurred('light');
    }
    setCounter(prev => prev + 1);
  };

  const handleDecrement = () => {
    if (haptic.isAvailable()) {
      haptic.impactOccurred('light');
    }
    setCounter(prev => Math.max(0, prev - 1));
  };

  const user = initData?.user;

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: themeParams.bgColor || '#17212b',
        color: themeParams.textColor || '#ffffff',
        padding: '20px',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      }}
    >
      {/* Заголовок */}
      <h1
        style={{
          fontSize: '24px',
          fontWeight: 'bold',
          marginBottom: '20px',
          color: themeParams.textColor || '#ffffff',
        }}
      >
        Telegram Mini App
      </h1>

      {/* Информация о пользователе */}
      <div
        style={{
          backgroundColor: themeParams.secondaryBgColor || '#232e3c',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '20px',
        }}
      >
        <h2
          style={{
            fontSize: '18px',
            fontWeight: '600',
            marginBottom: '12px',
            color: themeParams.textColor || '#ffffff',
          }}
        >
          👤 Информация о пользователе
        </h2>
        
        {user ? (
          <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
            <p><strong>ID:</strong> {user.id}</p>
            <p><strong>Имя:</strong> {user.firstName}</p>
            {user.lastName && <p><strong>Фамилия:</strong> {user.lastName}</p>}
            {user.username && <p><strong>Username:</strong> @{user.username}</p>}
            <p><strong>Язык:</strong> {user.languageCode}</p>
            {user.isPremium && (
              <p style={{ color: themeParams.linkColor || '#6ab3f3' }}>
                ⭐ Telegram Premium
              </p>
            )}
          </div>
        ) : (
          <p style={{ color: themeParams.hintColor || '#708499' }}>
            Данные пользователя недоступны
          </p>
        )}
      </div>

      {/* Информация о платформе */}
      <div
        style={{
          backgroundColor: themeParams.secondaryBgColor || '#232e3c',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '20px',
        }}
      >
        <h2
          style={{
            fontSize: '18px',
            fontWeight: '600',
            marginBottom: '12px',
            color: themeParams.textColor || '#ffffff',
          }}
        >
          📱 Платформа
        </h2>
        
        <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
          <p><strong>Платформа:</strong> {launchParams.platform}</p>
          <p><strong>Версия:</strong> {launchParams.version}</p>
          <p><strong>Viewport:</strong> {viewport.width}x{viewport.height}px</p>
          <p><strong>Расширен:</strong> {isExpanded ? 'Да' : 'Нет'}</p>
        </div>
      </div>

      {/* Счётчик с кнопками */}
      <div
        style={{
          backgroundColor: themeParams.secondaryBgColor || '#232e3c',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '20px',
        }}
      >
        <h2
          style={{
            fontSize: '18px',
            fontWeight: '600',
            marginBottom: '12px',
            color: themeParams.textColor || '#ffffff',
          }}
        >
          🔢 Счётчик
        </h2>
        
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '20px',
            marginTop: '16px',
          }}
        >
          <button
            onClick={handleDecrement}
            disabled={counter === 0}
            style={{
              width: '50px',
              height: '50px',
              borderRadius: '50%',
              border: 'none',
              backgroundColor: themeParams.buttonColor || '#5288c1',
              color: themeParams.buttonTextColor || '#ffffff',
              fontSize: '24px',
              cursor: 'pointer',
              opacity: counter === 0 ? 0.5 : 1,
            }}
          >
            −
          </button>
          
          <div
            style={{
              fontSize: '48px',
              fontWeight: 'bold',
              minWidth: '80px',
              textAlign: 'center',
              color: themeParams.textColor || '#ffffff',
            }}
          >
            {counter}
          </div>
          
          <button
            onClick={handleIncrement}
            style={{
              width: '50px',
              height: '50px',
              borderRadius: '50%',
              border: 'none',
              backgroundColor: themeParams.buttonColor || '#5288c1',
              color: themeParams.buttonTextColor || '#ffffff',
              fontSize: '24px',
              cursor: 'pointer',
            }}
          >
            +
          </button>
        </div>
        
        {counter > 0 && (
          <p
            style={{
              marginTop: '16px',
              textAlign: 'center',
              color: themeParams.hintColor || '#708499',
              fontSize: '14px',
            }}
          >
            Нажми кнопку "Назад" чтобы уменьшить счётчик
          </p>
        )}
      </div>

      {/* Информация о теме */}
      <div
        style={{
          backgroundColor: themeParams.secondaryBgColor || '#232e3c',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '80px', // Отступ для главной кнопки
        }}
      >
        <h2
          style={{
            fontSize: '18px',
            fontWeight: '600',
            marginBottom: '12px',
            color: themeParams.textColor || '#ffffff',
          }}
        >
          🎨 Цвета темы
        </h2>
        
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
            gap: '12px',
            fontSize: '12px',
          }}
        >
          {Object.entries(themeParams).map(([key, value]) => (
            <div key={key} style={{ textAlign: 'center' }}>
              <div
                style={{
                  width: '100%',
                  height: '40px',
                  backgroundColor: value as string,
                  borderRadius: '8px',
                  marginBottom: '4px',
                  border: '1px solid rgba(255,255,255,0.1)',
                }}
              />
              <div style={{ color: themeParams.hintColor || '#708499' }}>
                {key}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Подсказка о главной кнопке */}
      <div
        style={{
          position: 'fixed',
          bottom: '80px',
          left: '20px',
          right: '20px',
          backgroundColor: themeParams.secondaryBgColor || '#232e3c',
          borderRadius: '12px',
          padding: '12px',
          textAlign: 'center',
          fontSize: '14px',
          color: themeParams.hintColor || '#708499',
        }}
      >
        👇 Нажми на главную кнопку внизу экрана
      </div>
    </div>
  );
}
