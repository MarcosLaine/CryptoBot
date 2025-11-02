import React, { useState, useEffect, useContext, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import API_BASE_URL from '../config';
import ApiKeysModal from '../components/ApiKeysModal';
import BotSettingsModal from '../components/BotSettingsModal';
import AssetSettingsModal from '../components/AssetSettingsModal';
import { ArrowUpIcon, ArrowDownIcon, ArrowRightOnRectangleIcon, ArrowPathIcon, ArrowDownTrayIcon, PlayIcon, StopIcon, KeyIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';

const Dashboard = () => {
  const [portfolio, setPortfolio] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [botStatus, setBotStatus] = useState({ is_running: false });
  const [apiKeysStatus, setApiKeysStatus] = useState({ has_keys: false });
  const [botSettings, setBotSettings] = useState({ check_interval_minutes: 30 });
  const [showApiKeysModal, setShowApiKeysModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showAssetSettingsModal, setShowAssetSettingsModal] = useState(false);
  const [starting, setStarting] = useState(false);
  const [stopping, setStopping] = useState(false);
  const { logout } = useContext(AuthContext);
  const navigate = useNavigate();
  
  // Use ref to prevent multiple simultaneous calls
  const fetchingRef = useRef(false);
  const intervalRef = useRef(null);

  const fetchData = async () => {
    // Prevent multiple simultaneous calls using ref (more reliable than state)
    if (fetchingRef.current) {
      return;
    }
    
    fetchingRef.current = true;
    try {
      setRefreshing(true);
      const [portfolioRes, transactionsRes, statsRes, botStatusRes, apiKeysRes, settingsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/portfolio`).catch(() => ({ data: null })),
        axios.get(`${API_BASE_URL}/api/transactions`).catch(() => ({ data: { transactions: [] } })),
        axios.get(`${API_BASE_URL}/api/stats`).catch(() => ({ data: null })),
        axios.get(`${API_BASE_URL}/api/bot/status`).catch(() => ({ data: { is_running: false } })),
        axios.get(`${API_BASE_URL}/api/api-keys`).catch(() => ({ data: { has_keys: false } })),
        axios.get(`${API_BASE_URL}/api/bot/settings`).catch(() => ({ data: { check_interval_minutes: 30 } })),
      ]);

      setPortfolio(portfolioRes.data);
      setTransactions(transactionsRes.data.transactions || []);
      setStats(statsRes.data);
      setBotStatus(botStatusRes.data);
      setApiKeysStatus(apiKeysRes.data);
      setBotSettings(settingsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      if (error.response?.status === 401) {
        logout();
        navigate('/login');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
      fetchingRef.current = false;
    }
  };

  // Initial data fetch on mount
  useEffect(() => {
    fetchData();
  }, []); // Run only once on mount

  // Auto-refresh based on user's configured interval
  useEffect(() => {
    // Clear any existing interval first
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    // Skip if settings not loaded yet or if interval is 0 or negative
    if (!botSettings.check_interval_minutes || botSettings.check_interval_minutes <= 0) {
      return;
    }
    
    const refreshIntervalMinutes = botSettings.check_interval_minutes;
    const refreshIntervalMs = refreshIntervalMinutes * 60 * 1000; // Convert minutes to milliseconds
    
    // Minimum interval of 1 minute to prevent too frequent calls
    if (refreshIntervalMs < 60000) {
      return;
    }
    
    // Create interval for auto-refresh
    intervalRef.current = setInterval(() => {
      // Only refresh if not currently fetching (using ref for reliability)
      if (!fetchingRef.current) {
        fetchData();
      }
    }, refreshIntervalMs);
    
    // Cleanup: clear interval when component unmounts or when interval changes
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [botSettings.check_interval_minutes]); // Re-create interval when settings change

  const handleStartBot = async () => {
    if (!apiKeysStatus.has_keys) {
      setShowApiKeysModal(true);
      return;
    }

    setStarting(true);
    try {
      await axios.post(`${API_BASE_URL}/api/bot/start`);
      await fetchData();
    } catch (error) {
      alert(error.response?.data?.error || 'Erro ao iniciar o bot');
    } finally {
      setStarting(false);
    }
  };

  const handleStopBot = async () => {
    setStopping(true);
    try {
      await axios.post(`${API_BASE_URL}/api/bot/stop`);
      await fetchData();
    } catch (error) {
      alert(error.response?.data?.error || 'Erro ao parar o bot');
    } finally {
      setStopping(false);
    }
  };

  const handleRefresh = async () => {
    if (fetchingRef.current) {
      return; // Prevent multiple simultaneous refreshes
    }
    await fetchData();
  };

  const handleSyncTransactions = async () => {
    setSyncing(true);
    try {
      await axios.post(`${API_BASE_URL}/api/sync-transactions`);
      await fetchData();
    } catch (error) {
      console.error('Error syncing transactions:', error);
    } finally {
      setSyncing(false);
    }
  };

  const handleResetTransactions = async () => {
    const confirmed = window.confirm(
      'Tem certeza que deseja resetar todas as transações?\n\n' +
      'Isso irá:\n' +
      '• Deletar todas as transações do banco de dados\n' +
      '• Resetar o cálculo de Total Investido\n' +
      '• Resetar o cálculo de Retorno Total\n' +
      '• Limpar os snapshots do portfolio\n\n' +
      'Esta ação NÃO pode ser desfeita!\n\n' +
      'O bot deve estar parado para executar esta ação.'
    );
    
    if (!confirmed) {
      return;
    }
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/reset-transactions`);
      alert(response.data.message || 'Transações resetadas com sucesso!');
      await fetchData();
    } catch (error) {
      alert(error.response?.data?.error || 'Erro ao resetar transações');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const formatCurrency = (value) => {
    // USDT não é um código de moeda ISO 4217 válido, então usamos USD e substituímos
    try {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(value).replace('USD', 'USDT');
    } catch (e) {
      // Fallback caso haja algum erro: formatar manualmente
      const numValue = typeof value === 'number' ? value : parseFloat(value) || 0;
      return `$${numValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USDT`;
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-white"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white p-3 sm:p-4 md:p-6 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-yellow-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>
      
      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 sm:mb-8 gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-2 bg-gradient-to-r from-yellow-400 via-orange-400 to-yellow-600 bg-clip-text text-transparent">
              ₿ CryptoBot Dashboard
            </h1>
            <p className="text-purple-300 text-sm sm:text-base">Track your cryptocurrency investments</p>
          </div>
          <div className="flex flex-wrap gap-2 sm:gap-4 w-full sm:w-auto">
            {botStatus.is_running ? (
              <button
                onClick={handleStopBot}
                disabled={stopping}
                className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 text-sm sm:text-base bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 rounded-lg transition disabled:opacity-50 shadow-lg shadow-red-500/50"
              >
                <StopIcon className={`h-4 w-4 sm:h-5 sm:w-5 ${stopping ? 'animate-spin' : ''}`} />
                {stopping ? 'Parando...' : <span className="hidden sm:inline">Parar Bot</span>}
              </button>
            ) : (
              <button
                onClick={handleStartBot}
                disabled={starting}
                className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 text-sm sm:text-base bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 rounded-lg transition disabled:opacity-50 shadow-lg shadow-green-500/50"
              >
                <PlayIcon className={`h-4 w-4 sm:h-5 sm:w-5 ${starting ? 'animate-spin' : ''}`} />
                {starting ? 'Iniciando...' : <span className="hidden sm:inline">Iniciar Bot</span>}
              </button>
            )}
            <button
              onClick={() => setShowSettingsModal(true)}
              disabled={botStatus.is_running}
              className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 text-sm sm:text-base bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/50"
              title={botStatus.is_running ? 'Pare o bot antes de alterar configurações' : 'Configurações do Bot'}
            >
              <Cog6ToothIcon className="h-4 w-4 sm:h-5 sm:w-5" />
              <span className="hidden sm:inline">Configurações</span>
            </button>
            <button
              onClick={() => setShowAssetSettingsModal(true)}
              disabled={botStatus.is_running}
              className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 text-sm sm:text-base bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-500/50"
              title={botStatus.is_running ? 'Pare o bot antes de alterar ativos' : 'Configurar Ativos'}
            >
              <svg className="h-4 w-4 sm:h-5 sm:w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="hidden sm:inline">Ativos</span>
            </button>
            <button
              onClick={() => setShowApiKeysModal(true)}
              className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 text-sm sm:text-base bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 rounded-lg transition shadow-lg"
            >
              <KeyIcon className="h-4 w-4 sm:h-5 sm:w-5" />
              <span className="hidden md:inline">{apiKeysStatus.has_keys ? 'Chaves de API' : 'Configurar API'}</span>
              <span className="md:hidden">API</span>
            </button>
            <button
              onClick={handleSyncTransactions}
              disabled={syncing}
              className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 text-sm sm:text-base bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 rounded-lg transition disabled:opacity-50 shadow-lg shadow-blue-500/50"
            >
              <ArrowDownTrayIcon className={`h-4 w-4 sm:h-5 sm:w-5 ${syncing ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">{syncing ? 'Sincronizando...' : 'Sincronizar'}</span>
            </button>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 text-sm sm:text-base bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 rounded-lg transition disabled:opacity-50 shadow-lg shadow-yellow-500/50"
            >
              <ArrowPathIcon className={`h-4 w-4 sm:h-5 sm:w-5 ${refreshing ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Atualizar</span>
            </button>
            <button
              onClick={handleResetTransactions}
              disabled={botStatus.is_running}
              className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 text-sm sm:text-base bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 rounded-lg transition disabled:opacity-50 shadow-lg shadow-orange-500/50"
              title={botStatus.is_running ? 'Pare o bot antes de resetar' : 'Resetar Transações e Estatísticas'}
            >
              <svg className="h-4 w-4 sm:h-5 sm:w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              <span className="hidden sm:inline">Resetar</span>
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 text-sm sm:text-base bg-gradient-to-r from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 rounded-lg transition shadow-lg"
            >
              <ArrowRightOnRectangleIcon className="h-4 w-4 sm:h-5 sm:w-5" />
              <span className="hidden sm:inline">Sair</span>
            </button>
          </div>
        </div>

        {/* Bot Status Card */}
        <div className="mb-4 sm:mb-6">
          <div className={`p-3 sm:p-4 rounded-xl shadow-xl border-2 ${
            botStatus.is_running 
              ? 'bg-gradient-to-r from-green-600 via-emerald-600 to-green-700 border-green-400 shadow-green-500/50' 
              : 'bg-gradient-to-r from-gray-700 via-gray-800 to-gray-900 border-gray-600'
          }`}>
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
              <div className="flex-1">
                <h3 className="text-base sm:text-lg font-semibold text-white mb-1">
                  Status do Bot
                </h3>
                <p className="text-gray-200 text-xs sm:text-sm">
                  {botStatus.is_running ? (
                    <>
                      <span className="inline-block w-2 h-2 bg-green-300 rounded-full mr-2 animate-pulse"></span>
                      Bot em operação
                      {botStatus.started_at && (
                        <span className="block text-xs mt-1">
                          Iniciado em: {new Date(botStatus.started_at).toLocaleString('pt-BR', {
                            timeZone: 'America/Sao_Paulo',
                            day: '2-digit',
                            month: '2-digit',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </span>
                      )}
                      <span className="block text-xs mt-1 text-gray-300">
                        Intervalo de verificação: {botSettings.check_interval_minutes} minutos
                      </span>
                    </>
                  ) : (
                    <>
                      <span className="inline-block w-2 h-2 bg-gray-400 rounded-full mr-2"></span>
                      Bot parado
                      {!apiKeysStatus.has_keys && (
                        <span className="block text-xs mt-1 text-yellow-300">
                          Configure suas chaves de API para iniciar o bot
                        </span>
                      )}
                      {apiKeysStatus.has_keys && (
                        <span className="block text-xs mt-1 text-gray-300">
                          Intervalo de verificação: {botSettings.check_interval_minutes} minutos
                        </span>
                      )}
                    </>
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-6 sm:mb-8">
            <StatCard
              title="Total Value"
              value={formatCurrency(portfolio?.total_value || 0)}
              icon={<ArrowUpIcon className="h-8 w-8 text-yellow-300 drop-shadow-lg" />}
              bgColor="bg-gradient-to-br from-yellow-600 via-orange-600 to-yellow-700 border-yellow-400"
            />
            <StatCard
              title="Total Invested"
              value={formatCurrency(stats.total_invested || 0)}
              icon={<ArrowDownIcon className="h-8 w-8 text-blue-300 drop-shadow-lg" />}
              bgColor="bg-gradient-to-br from-blue-600 via-indigo-600 to-blue-700 border-blue-400"
            />
            <StatCard
              title="Total Return"
              value={formatCurrency(portfolio?.total_return || 0)}
              subtitle={`${(portfolio?.total_return_percentage || 0).toFixed(2)}%`}
              icon={
                (portfolio?.total_return || 0) >= 0 ? (
                  <ArrowUpIcon className="h-8 w-8 text-green-300 drop-shadow-lg" />
                ) : (
                  <ArrowDownIcon className="h-8 w-8 text-red-300 drop-shadow-lg" />
                )
              }
              bgColor={
                (portfolio?.total_return || 0) >= 0
                  ? 'bg-gradient-to-br from-green-600 via-emerald-600 to-green-700 border-green-400'
                  : 'bg-gradient-to-br from-red-600 via-rose-600 to-red-700 border-red-400'
              }
            />
            <StatCard
              title="USDT Balance"
              value={formatCurrency(stats.usdt_balance || 0)}
              icon={<ArrowUpIcon className="h-8 w-8 text-purple-300 drop-shadow-lg" />}
              bgColor="bg-gradient-to-br from-purple-600 via-pink-600 to-purple-700 border-purple-400"
            />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
          {/* Portfolio Section */}
          <div className="lg:col-span-2">
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-4 sm:p-6 shadow-xl border-2 border-gray-700">
              <h2 className="text-xl sm:text-2xl font-bold mb-4 sm:mb-6 bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
                💎 Portfolio
              </h2>
              <div className="space-y-3 sm:space-y-4">
                {portfolio?.portfolio.map((item) => (
                  <PortfolioCard key={item.asset} item={item} formatCurrency={formatCurrency} />
                ))}
                {(!portfolio?.portfolio || portfolio.portfolio.length === 0) && (
                  <div className="text-center py-8 text-gray-400">
                    No portfolio data available
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Transactions Section */}
          <div>
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-4 sm:p-6 shadow-xl border-2 border-gray-700">
              <h2 className="text-xl sm:text-2xl font-bold mb-4 sm:mb-6 bg-gradient-to-r from-blue-400 to-cyan-500 bg-clip-text text-transparent">
                📊 Latest Transactions
              </h2>
              <div className="space-y-2 sm:space-y-3 max-h-96 overflow-y-auto">
                {transactions.map((tx, index) => (
                  <TransactionCard
                    key={index}
                    transaction={tx}
                    formatCurrency={formatCurrency}
                    formatDate={formatDate}
                  />
                ))}
                {transactions.length === 0 && (
                  <div className="text-center py-8 text-gray-400">
                    No transactions yet
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* API Keys Modal */}
      <ApiKeysModal
        isOpen={showApiKeysModal}
        onClose={() => setShowApiKeysModal(false)}
        onSuccess={() => {
          fetchData();
        }}
      />

      {/* Bot Settings Modal */}
      <BotSettingsModal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        onSuccess={() => {
          fetchData();
        }}
        currentInterval={botSettings.check_interval_minutes}
        isRunning={botStatus.is_running}
      />
      <AssetSettingsModal
        isOpen={showAssetSettingsModal}
        onClose={() => setShowAssetSettingsModal(false)}
        onSave={() => {
          setShowAssetSettingsModal(false);
          fetchData();
        }}
      />
    </div>
  );
};

const StatCard = ({ title, value, subtitle, icon, bgColor }) => {
  return (
    <div className={`${bgColor} rounded-xl p-6 shadow-2xl transform transition hover:scale-105 border-2 border-opacity-50 backdrop-blur-sm`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-gray-100 text-sm font-medium uppercase tracking-wider">{title}</h3>
        {icon}
      </div>
      <div className="text-3xl font-bold mb-1 bg-gradient-to-r from-white to-gray-200 bg-clip-text text-transparent">{value}</div>
      {subtitle && <div className="text-gray-200 text-sm">{subtitle}</div>}
    </div>
  );
};

const PortfolioCard = ({ item, formatCurrency }) => {
  const isPositive = item.return_percentage >= 0;
  
  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg p-4 hover:from-gray-700 hover:to-gray-800 transition border-2 border-gray-700 hover:border-yellow-500/50 shadow-lg hover:shadow-yellow-500/20">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-xl font-bold bg-gradient-to-r from-white to-gray-200 bg-clip-text text-transparent">{item.asset}</h3>
          <p className="text-purple-300 text-sm font-medium">{item.symbol}</p>
        </div>
        <div className="text-right">
          <div className="text-lg font-semibold bg-gradient-to-r from-yellow-300 to-orange-300 bg-clip-text text-transparent">{formatCurrency(item.value_usdt)}</div>
          <div className={`text-sm font-bold ${isPositive ? 'text-green-300' : 'text-red-300'}`}>
            {isPositive ? '↑ +' : '↓ '}{item.return_percentage.toFixed(2)}%
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
        <div>
          <p className="text-purple-300">Quantity</p>
          <p className="font-semibold text-white">{item.quantity.toFixed(6)}</p>
        </div>
        <div>
          <p className="text-purple-300">Price</p>
          <p className="font-semibold text-yellow-300">{formatCurrency(item.current_price)}</p>
        </div>
        <div>
          <p className="text-purple-300">Invested</p>
          <p className="font-semibold text-blue-300">{formatCurrency(item.invested)}</p>
        </div>
        <div>
          <p className="text-purple-300">Return</p>
          <p className={`font-semibold ${isPositive ? 'text-green-300' : 'text-red-300'}`}>
            {isPositive ? '↑ +' : '↓ '}{formatCurrency(item.return_amount)}
          </p>
        </div>
      </div>
      
      <div className="mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-purple-500/30">
        <div className="flex flex-col sm:flex-row justify-between gap-1 sm:gap-0 text-xs text-purple-300">
          <span className="font-medium">MA Short: <span className="text-yellow-300">{item.media_curta.toFixed(4)}</span></span>
          <span className="font-medium">MA Long: <span className="text-yellow-300">{item.media_longa.toFixed(4)}</span></span>
        </div>
      </div>
    </div>
  );
};

const TransactionCard = ({ transaction, formatCurrency, formatDate }) => {
  const isBuy = transaction.type === 'BUY';
  
  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg p-4 hover:from-gray-700 hover:to-gray-800 transition border-2 border-gray-700 hover:border-blue-500/50 shadow-lg">
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-2 py-1 rounded text-xs font-semibold shadow-lg ${
              isBuy ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white border border-green-400' : 'bg-gradient-to-r from-red-500 to-rose-600 text-white border border-red-400'
            }`}>
              {transaction.type}
            </span>
            <span className="font-bold">{transaction.asset.replace('USDT', '')}</span>
          </div>
          <p className="text-gray-400 text-xs">{formatDate(transaction.timestamp)}</p>
        </div>
        <div className="text-right">
          <div className="font-semibold">{formatCurrency(transaction.total)}</div>
          <div className="text-xs text-gray-400">
            {transaction.quantity.toFixed(6)} @ {formatCurrency(transaction.price)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

