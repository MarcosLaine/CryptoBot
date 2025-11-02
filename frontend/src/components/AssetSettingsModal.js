import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';
import { XMarkIcon, CheckIcon } from '@heroicons/react/24/outline';

const AssetSettingsModal = ({ isOpen, onClose, onSave }) => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchAssets();
    }
  }, [isOpen]);

  const fetchAssets = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/assets/settings`);
      setAssets(response.data.assets || []);
    } catch (error) {
      console.error('Error fetching assets:', error);
      // If error, try to get available assets
      try {
        const response = await axios.get(`${API_BASE_URL}/api/assets`);
        setAssets((response.data.assets || []).map(asset => ({
          ...asset,
          enabled: true,
          investment_amount: 0
        })));
      } catch (e) {
        console.error('Error fetching available assets:', e);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAsset = (index) => {
    const updatedAssets = [...assets];
    updatedAssets[index].enabled = !updatedAssets[index].enabled;
    setAssets(updatedAssets);
  };

  const handleInvestmentAmountChange = (index, value) => {
    const updatedAssets = [...assets];
    const numValue = parseFloat(value) || 0;
    updatedAssets[index].investment_amount = numValue;
    setAssets(updatedAssets);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.post(`${API_BASE_URL}/api/assets/settings`, {
        assets: assets
      });
      onSave();
      onClose();
    } catch (error) {
      alert(error.response?.data?.error || 'Erro ao salvar configurações de ativos');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-gray-800 rounded-lg p-4 sm:p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto border-2 border-purple-500/30 backdrop-blur-sm shadow-2xl my-4">
        <div className="flex justify-between items-start gap-4 mb-4 sm:mb-6">
          <h2 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent flex-1">
            💎 Configurar Ativos
          </h2>
          <button
            onClick={onClose}
            className="text-purple-300 hover:text-yellow-400 transition flex-shrink-0"
          >
            <XMarkIcon className="h-5 w-5 sm:h-6 sm:w-6" />
          </button>
        </div>

        <p className="text-purple-300 mb-4 sm:mb-6 text-xs sm:text-sm">
          Selecione quais ativos você deseja que o bot opere e defina o valor de investimento para cada um.
          O valor de investimento define quanto USDT será usado para comprar cada ativo.
        </p>

        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-white"></div>
          </div>
        ) : (
          <div className="space-y-4">
            {assets.map((asset, index) => (
              <div
                key={asset.symbol}
                className={`bg-gradient-to-br from-gray-700 to-gray-800 rounded-lg p-4 transition border-2 shadow-lg ${
                  asset.enabled 
                    ? 'border-yellow-500/50 hover:border-yellow-500 hover:shadow-yellow-500/30' 
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleToggleAsset(index)}
                      className={`w-6 h-6 rounded flex items-center justify-center transition shadow-lg ${
                        asset.enabled
                          ? 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700'
                          : 'bg-gray-600 hover:bg-gray-500 border-2 border-gray-400'
                      }`}
                    >
                      {asset.enabled && <CheckIcon className="h-4 w-4 text-white" />}
                    </button>
                    <div>
                      <h3 className="text-lg font-semibold bg-gradient-to-r from-white to-gray-200 bg-clip-text text-transparent">{asset.name}</h3>
                      <p className="text-sm text-purple-300 font-medium">{asset.symbol}</p>
                    </div>
                  </div>
                </div>

                {asset.enabled && (
                  <div className="mt-3 pt-3 border-t border-purple-500/30">
                    <label className="block text-sm text-purple-300 mb-2 font-medium">
                      Valor de Investimento (USDT)
                    </label>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={asset.investment_amount || ''}
                      onChange={(e) => handleInvestmentAmountChange(index, e.target.value)}
                      placeholder="0.00"
                      className="w-full px-3 py-2 bg-gray-800 border-2 border-purple-500/30 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 transition shadow-lg shadow-purple-500/20 placeholder-gray-500"
                    />
                    <p className="text-xs text-purple-300 mt-1">
                      Deixe em 0 para usar todo o saldo disponível ou defina um valor específico
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 rounded-lg transition shadow-lg text-white"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 rounded-lg transition disabled:opacity-50 shadow-lg shadow-yellow-500/50 text-white font-semibold"
          >
            {saving ? 'Salvando...' : 'Salvar Configurações'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssetSettingsModal;

