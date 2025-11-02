import React, { useState, useEffect } from 'react';
import { XMarkIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';

const PWAInstallPrompt = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    // Check if already installed (standalone mode)
    const standalone = window.matchMedia('(display-mode: standalone)').matches ||
                      window.navigator.standalone ||
                      document.referrer.includes('android-app://');
    setIsStandalone(standalone);

    // Check if iOS
    const ios = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    setIsIOS(ios);

    // Check if user has previously dismissed the prompt
    const dismissed = localStorage.getItem('pwa-prompt-dismissed');
    const dismissedTime = dismissed ? parseInt(dismissed) : 0;
    const daysSinceDismissed = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24);

    // Show prompt if not standalone, not recently dismissed, and either has deferred prompt or is iOS
    if (!standalone && daysSinceDismissed > 7) {
      // Listen for the beforeinstallprompt event (Chrome, Edge, Samsung)
      const handleBeforeInstallPrompt = (e) => {
        e.preventDefault();
        setDeferredPrompt(e);
        setShowPrompt(true);
      };

      window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

      // For iOS, show manual install instructions after a delay
      if (ios) {
        setTimeout(() => {
          setShowPrompt(true);
        }, 5000); // Show after 5 seconds on iOS
      }

      return () => {
        window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      };
    }
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) {
      return;
    }

    // Show the install prompt
    deferredPrompt.prompt();

    // Wait for the user to respond to the prompt
    const { outcome } = await deferredPrompt.userChoice;
    
    console.log(`User response to the install prompt: ${outcome}`);

    // Clear the deferredPrompt
    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('pwa-prompt-dismissed', Date.now().toString());
  };

  // Don't show if already installed or if prompt is not ready
  if (isStandalone || !showPrompt) {
    return null;
  }

  return (
    <div className="pwa-install-prompt">
      <ArrowDownTrayIcon className="h-6 w-6 flex-shrink-0" />
      <div className="flex-1">
        {isIOS ? (
          <div className="text-sm">
            <p className="font-semibold mb-1">Instale o CryptoBot!</p>
            <p className="text-xs opacity-90">
              Toque em <span className="inline-flex items-center px-1 py-0.5 rounded bg-white/20 mx-1">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"/>
                </svg>
              </span> e depois em "Adicionar à Tela de Início"
            </p>
          </div>
        ) : (
          <>
            <p className="font-semibold text-sm">Instale o CryptoBot</p>
            <p className="text-xs opacity-90">Acesse rápido e trabalhe offline!</p>
          </>
        )}
      </div>
      <div className="flex gap-2">
        {!isIOS && deferredPrompt && (
          <button
            onClick={handleInstallClick}
            className="px-4 py-2 bg-white text-purple-700 rounded-lg font-semibold text-sm hover:bg-gray-100 transition"
          >
            Instalar
          </button>
        )}
        <button
          onClick={handleDismiss}
          className="p-2 hover:bg-white/10 rounded-lg transition"
          aria-label="Dismiss"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
};

export default PWAInstallPrompt;

