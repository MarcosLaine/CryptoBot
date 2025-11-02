import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';
import { XMarkIcon, Cog6ToothIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const BotSettingsModal = ({ isOpen, onClose, onSuccess, currentInterval, isRunning }) => {
  const [interval, setInterval] = useState(30);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setInterval(currentInterval || 30);
      setError('');
      setSuccess(false);
    }
  }, [isOpen, currentInterval]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setLoading(true);

    try {
      await axios.post(`${API_BASE_URL}/api/bot/settings`, {
        check_interval_minutes: parseInt(interval),
      });

      setSuccess(true);
      
      setTimeout(() => {
        onSuccess && onSuccess();
        onClose();
      }, 1500);
    } catch (error) {
      setError(error.response?.data?.error || 'Erro ao salvar configurações');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-gray-800 rounded-xl shadow-2xl max-w-md w-full p-4 sm:p-6 relative border-2 border-purple-500/30 backdrop-blur-sm my-4">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 sm:top-4 sm:right-4 text-purple-300 hover:text-yellow-400 transition"
        >
          <XMarkIcon className="h-5 w-5 sm:h-6 sm:w-6" />
        </button>

        <div className="flex items-start gap-3 mb-4 sm:mb-6 pr-8">
          <Cog6ToothIcon className="h-6 w-6 sm:h-8 sm:w-8 text-yellow-400 drop-shadow-lg flex-shrink-0 mt-1" />
          <h2 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
            ⚙️ Configurações do Bot
          </h2>
        </div>

        {isRunning && (
          <div className="mb-4 p-3 bg-yellow-900 bg-opacity-30 border border-yellow-500 rounded-lg flex items-center gap-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
            <span className="text-yellow-400 text-sm">
              O bot está em execução. Pare o bot antes de alterar as configurações.
            </span>
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
            <span className="text-green-400 text-sm">Configurações salvas com sucesso!</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="interval" className="block text-sm font-medium text-purple-300 mb-2">
              Intervalo de Verificação (minutos)
            </label>
            <input
              id="interval"
              type="number"
              min="1"
              max="1440"
              value={interval}
              onChange={(e) => setInterval(e.target.value)}
              required
              disabled={isRunning || loading}
              className="w-full px-4 py-3 bg-gray-800 border-2 border-purple-500/30 rounded-lg text-white focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 outline-none transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/20 placeholder-gray-500"
              placeholder="30"
            />
            <p className="text-xs text-purple-300 mt-2">
              Intervalo em minutos entre as verificações das médias móveis e possíveis transações.
              Mínimo: 1 minuto, Máximo: 1440 minutos (24 horas).
            </p>
          </div>

          <div className="bg-blue-900 bg-opacity-20 border border-blue-500 rounded-lg p-3 mt-4">
            <p className="text-blue-300 text-xs">
              ℹ️ <strong>Como funciona:</strong> O bot verificará as médias móveis e executará transações 
              (compras/vendas) de acordo com a estratégia a cada intervalo configurado. 
              Intervalos menores permitem reações mais rápidas, mas geram mais requisições à API.
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 text-white rounded-lg font-semibold transition disabled:opacity-50 shadow-lg"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading || isRunning}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 text-white rounded-lg font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-yellow-500/50"
                >
                  {loading ? 'Salvando...' : 'Salvar'}
                </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BotSettingsModal;

