import React, { useState, useEffect } from 'react';
import { WifiIcon, SignalSlashIcon } from '@heroicons/react/24/outline';

const OfflineIndicator = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showOnlineNotification, setShowOnlineNotification] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setShowOnlineNotification(true);
      
      // Hide the "back online" notification after 3 seconds
      setTimeout(() => {
        setShowOnlineNotification(false);
      }, 3000);
    };

    const handleOffline = () => {
      setIsOnline(false);
      setShowOnlineNotification(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (isOnline && !showOnlineNotification) {
    return null;
  }

  return (
    <>
      {!isOnline && (
        <div className="offline-indicator">
          <div className="flex items-center justify-center gap-2">
            <SignalSlashIcon className="h-5 w-5" />
            <span>Você está offline - Algumas funcionalidades podem estar limitadas</span>
          </div>
        </div>
      )}
      
      {isOnline && showOnlineNotification && (
        <div className="online-indicator">
          <div className="flex items-center justify-center gap-2">
            <WifiIcon className="h-5 w-5" />
            <span>Conexão restaurada!</span>
          </div>
        </div>
      )}
    </>
  );
};

export default OfflineIndicator;

