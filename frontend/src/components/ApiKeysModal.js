import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';
import { XMarkIcon, KeyIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const ApiKeysModal = ({ isOpen, onClose, onSuccess }) => {
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [hasKeys, setHasKeys] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (isOpen) {
      checkApiKeys();
    }
  }, [isOpen]);

  const checkApiKeys = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/api-keys`);
      setHasKeys(response.data.has_keys);
      setChecking(false);
    } catch (error) {
      console.error('Error checking API keys:', error);
      setChecking(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setLoading(true);

    try {
      await axios.post(`${API_BASE_URL}/api/api-keys`, {
        api_key: apiKey.trim(),
        api_secret: apiSecret.trim(),
      });

      setSuccess(true);
      setApiKey('');
      setApiSecret('');
      setHasKeys(true);
      
      setTimeout(() => {
        onSuccess && onSuccess();
        onClose();
      }, 1500);
    } catch (error) {
      setError(error.response?.data?.error || 'Erro ao salvar chaves de API');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-gray-800 rounded-xl shadow-2xl max-w-md w-full p-4 sm:p-6 relative border-2 border-purple-500/30 backdrop-blur-sm my-4">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-purple-300 hover:text-yellow-400 transition"
        >
          <XMarkIcon className="h-6 w-6" />
        </button>

        <div className="flex items-start gap-3 mb-4 sm:mb-6">
          <KeyIcon className="h-6 w-6 sm:h-8 sm:w-8 text-yellow-400 drop-shadow-lg flex-shrink-0 mt-1" />
          <div className="flex-1 min-w-0">
            <h2 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
              🔑 Configurar Chaves de API da Binance
            </h2>
            <p className="text-xs sm:text-sm text-purple-300 mt-1">Não use a senha da sua conta. Use as chaves de API geradas na Binance.</p>
          </div>
        </div>

        {checking ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500 mx-auto"></div>
          </div>
        ) : (
          <>
            {hasKeys && (
              <div className="mb-4 p-3 bg-green-900 bg-opacity-30 border border-green-500 rounded-lg flex items-center gap-2">
                <CheckCircleIcon className="h-5 w-5 text-green-400" />
                <span className="text-green-400 text-sm">Você já possui chaves de API configuradas</span>
              </div>
            )}

            {error && (
              <div className="mb-4 p-3 bg-red-900 bg-opacity-30 border border-red-500 rounded-lg flex items-center gap-2">
                <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                <span className="text-red-400 text-sm">{error}</span>
              </div>
            )}

            {success && (
              <div className="mb-4 p-3 bg-green-900 bg-opacity-30 border border-green-500 rounded-lg flex items-center gap-2">
                <CheckCircleIcon className="h-5 w-5 text-green-400" />
                <span className="text-green-400 text-sm">Chaves de API salvas com sucesso!</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
              <label htmlFor="api_key" className="block text-sm font-medium text-purple-300 mb-2">
                API Key
              </label>
                <input
                  id="api_key"
                  type="text"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-gray-800 border-2 border-purple-500/30 rounded-lg text-white focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 outline-none transition shadow-lg shadow-purple-500/20 placeholder-gray-500"
                  placeholder="Insira sua API Key da Binance"
                />
              </div>

              <div>
                <label htmlFor="api_secret" className="block text-sm font-medium text-purple-300 mb-2">
                  API Secret
                </label>
                <input
                  id="api_secret"
                  type="password"
                  value={apiSecret}
                  onChange={(e) => setApiSecret(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-gray-800 border-2 border-purple-500/30 rounded-lg text-white focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 outline-none transition shadow-lg shadow-purple-500/20 placeholder-gray-500"
                  placeholder="Insira sua API Secret da Binance"
                />
              </div>

              <div className="bg-blue-900 bg-opacity-20 border border-blue-500 rounded-lg p-3 mt-2">
                <p className="text-blue-300 text-xs mb-2">
                  ℹ️ <strong>O que são chaves de API?</strong> São credenciais separadas criadas na Binance para permitir 
                  que aplicativos façam operações em seu nome. <strong>NÃO é a senha da sua conta.</strong>
                </p>
                <p className="text-blue-300 text-xs">
                  Para criar chaves de API: Binance → API Management → Create API Key
                </p>
              </div>

              <div className="bg-yellow-900 bg-opacity-20 border border-yellow-600 rounded-lg p-3 mt-2">
                <p className="text-yellow-300 text-xs">
                  ⚠️ <strong>Importante:</strong> As chaves de API serão criptografadas e armazenadas de forma segura. 
                  Certifique-se de que suas chaves têm permissões apenas de leitura e escrita, <strong>sem permissão de saque</strong>.
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 text-white rounded-lg font-semibold transition shadow-lg"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 text-white rounded-lg font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-yellow-500/50"
                >
                  {loading ? 'Salvando...' : hasKeys ? 'Atualizar' : 'Salvar'}
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
};

export default ApiKeysModal;

