# 📱 CryptoBot - Documentação do Site (Frontend)

## Índice
- [Visão Geral](#visão-geral)
- [Tecnologias](#tecnologias)
- [Arquitetura](#arquitetura)
- [Estrutura de Componentes](#estrutura-de-componentes)
- [Páginas](#páginas)
- [Recursos PWA](#recursos-pwa)
- [Autenticação](#autenticação)
- [API Integration](#api-integration)
- [Estilização](#estilização)
- [Build e Deploy](#build-e-deploy)

---

## Visão Geral

O CryptoBot Frontend é uma Progressive Web App (PWA) construída com React que fornece uma interface moderna e responsiva para gerenciamento de portfolio de criptomoedas e controle de bot de trading automatizado.

**URL de Produção:** `https://cryptobot-frontend.netlify.app` (ou similar)

**Características principais:**
- ✅ Interface responsiva (mobile-first)
- ✅ Progressive Web App (PWA) - instalável
- ✅ Suporte offline com Service Worker
- ✅ Design moderno com gradientes e animações
- ✅ Tema escuro
- ✅ Atualização automática de dados
- ✅ Gráficos e estatísticas em tempo real
- ✅ Configurações personalizáveis

---

## Tecnologias

### Frontend Stack
```
React 18.2.0              - Biblioteca UI
React Router DOM 6.20.0   - Roteamento
Axios 1.6.2               - Cliente HTTP
Tailwind CSS 3.3.6        - Framework CSS
Heroicons 2.1.1           - Ícones
```

### Build Tools
```
react-scripts 5.0.1       - Build & Dev Server
PostCSS 8.4.32            - Processamento CSS
Autoprefixer 10.4.16      - Compatibilidade CSS
```

### PWA
```
Service Worker            - Cache e offline support
Web App Manifest          - Configuração PWA
```

---

## Arquitetura

### Estrutura de Diretórios
```
frontend/
├── public/
│   ├── index.html              # HTML principal
│   ├── manifest.json           # PWA manifest
│   ├── service-worker.js       # Service Worker
│   ├── _redirects              # Netlify redirects
│   ├── favicon.ico
│   ├── icon-192.png
│   ├── icon-512.png
│   └── apple-touch-icon.png
├── src/
│   ├── App.js                  # Componente raiz
│   ├── index.js                # Entry point
│   ├── index.css               # Estilos globais
│   ├── config.js               # Configuração da API
│   ├── components/
│   │   ├── ApiKeysModal.js     # Modal de config de API keys
│   │   ├── AssetSettingsModal.js # Modal de config de ativos
│   │   ├── BotSettingsModal.js # Modal de config do bot
│   │   ├── OfflineIndicator.js # Indicador de conexão
│   │   ├── ProtectedRoute.js   # Proteção de rotas
│   │   └── PWAInstallPrompt.js # Prompt de instalação PWA
│   ├── context/
│   │   └── AuthContext.js      # Contexto de autenticação
│   ├── pages/
│   │   ├── Login.js            # Página de login
│   │   ├── Register.js         # Página de registro
│   │   └── Dashboard.js        # Dashboard principal
│   └── serviceWorkerRegistration.js
├── package.json
├── tailwind.config.js
└── postcss.config.js
```

### Fluxo de Navegação
```
App.js
  ├── AuthProvider
  │     └── Router
  │           ├── /login → Login
  │           ├── /register → Register
  │           ├── /dashboard → Dashboard (Protected)
  │           └── / → Redirect to Dashboard
  └── PWA Components
        ├── OfflineIndicator
        └── PWAInstallPrompt
```

---

## Estrutura de Componentes

### App.js
**Função:** Componente raiz da aplicação

**Responsabilidades:**
- Setup do Router
- Provedor de contexto de autenticação
- Componentes PWA globais
- Configuração de rotas

```jsx
<AuthProvider>
  <Router>
    <OfflineIndicator />
    <PWAInstallPrompt />
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <Dashboard />
        </ProtectedRoute>
      } />
      <Route path="/" element={<Navigate to="/dashboard" />} />
    </Routes>
  </Router>
</AuthProvider>
```

---

### AuthContext
**Função:** Gerenciamento global de autenticação

**Estado:**
```javascript
{
  token: string | null,
  isAuthenticated: boolean
}
```

**Funções:**
- `login(token)` - Salva token e configura Axios
- `logout()` - Remove token e limpa Axios
- Persiste token em localStorage
- Configura header Authorization automaticamente

**Uso:**
```javascript
const { token, isAuthenticated, login, logout } = useContext(AuthContext);
```

---

### ProtectedRoute
**Função:** Proteção de rotas autenticadas

**Comportamento:**
- Verifica `isAuthenticated` do contexto
- Redireciona para `/login` se não autenticado
- Renderiza children se autenticado

```javascript
if (!isAuthenticated) {
  return <Navigate to="/login" replace />;
}
return children;
```

---

### PWAInstallPrompt
**Função:** Prompt de instalação PWA

**Features:**
- Detecta evento `beforeinstallprompt`
- Mostra banner de instalação personalizado
- Esconde após instalação ou dismiss
- Persiste estado no sessionStorage

**UI:**
```
┌─────────────────────────────────────┐
│ 📱 Instalar CryptoBot                │
│ Instale nosso app para acesso rápido│
│ [Instalar] [Fechar]                  │
└─────────────────────────────────────┘
```

---

### OfflineIndicator
**Função:** Indicador de conexão

**Estados:**
- **Online:** Banner verde (auto-hide após 3s)
- **Offline:** Banner vermelho (persistente)

**UI (Offline):**
```
┌─────────────────────────────────────┐
│ ⚠️ Você está offline                 │
└─────────────────────────────────────┘
```

---

### ApiKeysModal
**Função:** Configuração de API Keys da Binance

**Campos:**
- API Key (text input)
- API Secret (password input)

**Validações:**
- Campos obrigatórios
- Teste de conexão com Binance
- Feedback de erro

**Features:**
- Exibe chave mascarada se já configurada
- Botão "Testar Conexão"
- Criptografa API Secret no backend

**UI:**
```
┌─────────────────────────────────────┐
│ 🔑 Configurar API Keys               │
├─────────────────────────────────────┤
│ API Key:                             │
│ [_________________________]          │
│                                      │
│ API Secret:                          │
│ [•••••••••••••••••••••••••]          │
│                                      │
│ [Cancelar] [Salvar]                  │
└─────────────────────────────────────┘
```

---

### BotSettingsModal
**Função:** Configuração do intervalo de verificação do bot

**Campos:**
- Check Interval (number input, em minutos)

**Validações:**
- Mínimo: 1 minuto
- Máximo: 1440 minutos (24 horas)
- Apenas números inteiros

**Restrições:**
- Desabilitado quando bot está rodando
- Mostra mensagem de aviso

**UI:**
```
┌─────────────────────────────────────┐
│ ⚙️ Configurações do Bot              │
├─────────────────────────────────────┤
│ Intervalo de Verificação (minutos): │
│ [___30___]                           │
│                                      │
│ O bot verificará as médias móveis    │
│ a cada X minutos.                    │
│                                      │
│ [Cancelar] [Salvar]                  │
└─────────────────────────────────────┘
```

---

### AssetSettingsModal
**Função:** Configuração de ativos e valores de investimento

**Funcionalidades:**
- Lista de 10 criptomoedas principais
- Toggle para habilitar/desabilitar cada ativo
- Campo de valor de investimento por ativo (em USDT)

**Validações:**
- Valores positivos
- Formato numérico

**UI:**
```
┌─────────────────────────────────────┐
│ 💰 Configurar Ativos                 │
├─────────────────────────────────────┤
│ ☑️ Bitcoin (BTC)      [__50.00__]   │
│ ☑️ Ethereum (ETH)     [__30.00__]   │
│ ☐ Binance Coin (BNB)  [__0.00___]   │
│ ☑️ Solana (SOL)       [__20.00__]   │
│ ...                                  │
│                                      │
│ [Cancelar] [Salvar]                  │
└─────────────────────────────────────┘
```

---

## Páginas

### Login (pages/Login.js)

**Rota:** `/login`

**Campos:**
- Username (email)
- Password

**Funcionalidades:**
- Autenticação via API
- Armazena JWT token
- Redireciona para dashboard após login
- Link para página de registro
- Feedback de erros

**Design:**
- Background com gradiente animado
- Card centralizado com glass morphism
- Animações suaves

**Fluxo:**
```
1. Usuário preenche credenciais
2. Submit → POST /api/login
3. Recebe JWT token
4. Salva token no AuthContext
5. Redireciona para /dashboard
```

---

### Register (pages/Register.js)

**Rota:** `/register`

**Campos:**
- Username (email)
- Password
- Confirm Password

**Validações:**
- Username único
- Password match
- Campos obrigatórios

**Funcionalidades:**
- Criação de conta
- Login automático após registro
- Link para página de login
- Feedback de erros

**Fluxo:**
```
1. Usuário preenche dados
2. Submit → POST /api/register
3. Recebe JWT token
4. Salva token no AuthContext
5. Redireciona para /dashboard
```

---

### Dashboard (pages/Dashboard.js)

**Rota:** `/dashboard` (protegida)

**Seções:**

#### 1. Header
- Título do app
- Botões de ação:
  - Start/Stop Bot
  - Configurações do Bot
  - Configurar Ativos
  - API Keys
  - Sincronizar Transações
  - Atualizar
  - Resetar Transações
  - Logout

#### 2. Bot Status Card
- Status: Rodando / Parado
- Timestamp de início
- Intervalo de verificação
- Indicador visual (animado quando rodando)

#### 3. Stats Cards (Grid 4 colunas)
- **Total Value:** Valor total do portfolio
- **Total Invested:** Total investido
- **Total Return:** Retorno total (valor + percentual)
- **USDT Balance:** Saldo disponível em USDT

#### 4. Portfolio Section
- Lista de ativos com:
  - Nome e símbolo
  - Quantidade
  - Preço atual
  - Valor em USDT
  - Valor investido
  - Retorno (valor + percentual)
  - Médias móveis (curta e longa)
- Design: Cards com hover effect e gradientes

#### 5. Transactions Section
- Lista de últimas transações
- Tipo (BUY/SELL)
- Ativo
- Quantidade
- Preço
- Total
- Timestamp

**Features:**
- Auto-refresh baseado no intervalo do bot
- Loading states
- Error handling
- Responsive design (mobile-first)
- Animações e transições suaves

**Gerenciamento de Estado:**
```javascript
const [portfolio, setPortfolio] = useState(null);
const [transactions, setTransactions] = useState([]);
const [stats, setStats] = useState(null);
const [loading, setLoading] = useState(true);
const [refreshing, setRefreshing] = useState(false);
const [syncing, setSyncing] = useState(false);
const [botStatus, setBotStatus] = useState({ is_running: false });
const [apiKeysStatus, setApiKeysStatus] = useState({ has_keys: false });
const [botSettings, setBotSettings] = useState({ check_interval_minutes: 30 });
```

**Auto-refresh:**
```javascript
useEffect(() => {
  const interval = setInterval(() => {
    if (!fetchingRef.current) {
      fetchData();
    }
  }, botSettings.check_interval_minutes * 60 * 1000);
  
  return () => clearInterval(interval);
}, [botSettings.check_interval_minutes]);
```

---

## Recursos PWA

### Service Worker

**Arquivo:** `public/service-worker.js`

**Funcionalidades:**
- Cache de assets estáticos
- Estratégia Cache-First para recursos
- Network-First para API calls
- Fallback para modo offline

**Cache Strategy:**
```javascript
// Cache static assets
self.addEventListener('fetch', (event) => {
  if (event.request.destination === 'image') {
    event.respondWith(cacheFirst(event.request));
  }
  
  if (event.request.url.includes('/api/')) {
    event.respondWith(networkFirst(event.request));
  }
});
```

---

### Web App Manifest

**Arquivo:** `public/manifest.json`

**Configuração:**
```json
{
  "short_name": "CryptoBot",
  "name": "CryptoBot - Crypto Trading Dashboard",
  "icons": [
    {
      "src": "icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "start_url": ".",
  "display": "standalone",
  "theme_color": "#000000",
  "background_color": "#ffffff"
}
```

**Features:**
- Ícones adaptativos
- Standalone mode (sem barra de navegação)
- Splash screen personalizada

---

## Autenticação

### Fluxo de Autenticação

```
1. Usuário acessa app
   ↓
2. AuthContext verifica localStorage
   ↓
3a. Token existe → Define isAuthenticated=true
3b. Sem token → Define isAuthenticated=false
   ↓
4. ProtectedRoute verifica isAuthenticated
   ↓
5a. Autenticado → Renderiza Dashboard
5b. Não autenticado → Redireciona para Login
```

### Token Management

**Armazenamento:**
```javascript
localStorage.setItem('token', jwtToken);
```

**Configuração Axios:**
```javascript
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}
```

**Logout:**
```javascript
const logout = () => {
  localStorage.removeItem('token');
  delete axios.defaults.headers.common['Authorization'];
  setToken(null);
};
```

---

## API Integration

### Configuração

**Arquivo:** `src/config.js`

```javascript
const API_BASE_URL = 'https://cryptobot-api-jcrn.onrender.com';
export default API_BASE_URL;
```

### Chamadas de API

**Exemplo - Fetch Portfolio:**
```javascript
const fetchPortfolio = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/portfolio`);
    setPortfolio(response.data);
  } catch (error) {
    if (error.response?.status === 401) {
      logout();
      navigate('/login');
    }
  }
};
```

**Exemplo - Start Bot:**
```javascript
const handleStartBot = async () => {
  setStarting(true);
  try {
    await axios.post(`${API_BASE_URL}/api/bot/start`);
    await fetchData(); // Refresh data
  } catch (error) {
    alert(error.response?.data?.error || 'Erro ao iniciar o bot');
  } finally {
    setStarting(false);
  }
};
```

### Error Handling

**Padrões:**
- **401:** Logout e redirecionar para login
- **400:** Mostrar mensagem de erro do servidor
- **500:** Mensagem genérica de erro

---

## Estilização

### Tailwind CSS

**Arquivo de Config:** `tailwind.config.js`

```javascript
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom colors
      },
      animation: {
        blob: 'blob 7s infinite',
      },
      keyframes: {
        blob: {
          '0%': { transform: 'translate(0px, 0px) scale(1)' },
          '33%': { transform: 'translate(30px, -50px) scale(1.1)' },
          '66%': { transform: 'translate(-20px, 20px) scale(0.9)' },
          '100%': { transform: 'translate(0px, 0px) scale(1)' },
        },
      },
    },
  },
  plugins: [],
}
```

### Design System

**Cores Principais:**
```css
Background: gradient-to-br from-slate-900 via-purple-900 to-slate-900
Cards: gradient-to-br from-gray-800 to-gray-900
Accent: gradient-to-r from-yellow-400 via-orange-400 to-yellow-600
Success: gradient-to-r from-green-500 to-emerald-600
Danger: gradient-to-r from-red-600 to-red-700
Info: gradient-to-r from-blue-600 to-cyan-600
```

**Componentes:**

**Stat Card:**
- Border com gradiente
- Shadow colorida
- Hover scale effect
- Ícones Heroicons

**Portfolio Card:**
- Background com gradiente
- Border animada no hover
- Grid layout para informações
- Indicador de retorno (verde/vermelho)

**Transaction Card:**
- Badge colorido para tipo (BUY/SELL)
- Timestamp formatado
- Hover effect sutil

### Animações

**Blob Animation:**
```css
@keyframes blob {
  0%, 100% { transform: translate(0px, 0px) scale(1); }
  33% { transform: translate(30px, -50px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
}
```

**Spin (Loading):**
```jsx
<div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-white"></div>
```

**Pulse (Status Indicator):**
```jsx
<span className="animate-pulse w-2 h-2 bg-green-300 rounded-full"></span>
```

### Responsividade

**Breakpoints:**
- `sm:` - 640px
- `md:` - 768px
- `lg:` - 1024px
- `xl:` - 1280px

**Mobile-First Approach:**
```jsx
// Base (mobile)
<div className="text-sm p-3 grid-cols-1">

// Tablet
<div className="sm:text-base sm:p-4 sm:grid-cols-2">

// Desktop
<div className="lg:text-lg lg:p-6 lg:grid-cols-4">
```

---

## Build e Deploy

### Scripts

**package.json:**
```json
{
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build && npm run copy-sw",
    "build:pwa": "npm run build",
    "copy-sw": "cp public/service-worker.js build/service-worker.js",
    "test": "react-scripts test",
    "serve": "npm run build && serve -s build -l 3000"
  }
}
```

### Build de Produção

```bash
npm run build
```

**Output:**
```
build/
├── static/
│   ├── css/
│   ├── js/
│   └── media/
├── index.html
├── manifest.json
├── service-worker.js
└── asset-manifest.json
```

### Deploy no Netlify

**Configuração:**
- **Build command:** `npm run build`
- **Publish directory:** `build`

**_redirects:**
```
/* /index.html 200
```

**Variáveis de Ambiente:**
- Nenhuma necessária (API URL hardcoded em `config.js`)

### Deploy em Outro Serviço

**Vercel:**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "build",
  "devCommand": "npm start"
}
```

**Render (Static Site):**
- Build Command: `npm run build`
- Publish Directory: `build`

---

## Testes

### Testes Locais

**Dev Server:**
```bash
npm start
# http://localhost:3000
```

**Build Local:**
```bash
npm run serve
# http://localhost:3000
```

### Teste PWA

**1. Build de produção:**
```bash
npm run build
```

**2. Servir com HTTPS (necessário para PWA):**
```bash
npx serve -s build -l 3000 --ssl-cert <cert> --ssl-key <key>
```

**3. Verificar:**
- Chrome DevTools → Application → Manifest
- Chrome DevTools → Application → Service Workers
- Lighthouse → PWA audit

---

## Performance

### Otimizações

**Code Splitting:**
- React Router lazy loading (se implementado)
- Dynamic imports para modais pesados

**Asset Optimization:**
- Imagens comprimidas (PNG otimizados)
- SVG para ícones (Heroicons)
- CSS minificado (Tailwind purge)

**Caching:**
- Service Worker cache de assets
- localStorage para token

**Debouncing:**
- Prevent multiple simultaneous fetches usando `useRef`
```javascript
const fetchingRef = useRef(false);
if (fetchingRef.current) return;
fetchingRef.current = true;
```

### Lighthouse Score Targets

- **Performance:** > 90
- **Accessibility:** > 95
- **Best Practices:** > 95
- **SEO:** > 90
- **PWA:** ✓ Installable

---

## Troubleshooting

### PWA não instala

**Checklist:**
- [ ] HTTPS habilitado?
- [ ] `manifest.json` válido?
- [ ] Service Worker registrado?
- [ ] Ícones corretos (192px e 512px)?
- [ ] Testando em produção (não dev server)?

### Auto-refresh não funciona

**Verificar:**
- `botSettings.check_interval_minutes` está definido?
- Intervalo > 0?
- `fetchingRef.current` não está travado em `true`?

### Axios não envia token

**Verificar:**
- Token está no localStorage?
- `AuthContext` chamou `axios.defaults.headers.common['Authorization']`?
- Token no formato correto: `Bearer <token>`?

---

## Roadmap Futuro

### Features Planejadas

- [ ] Dark/Light mode toggle
- [ ] Gráficos interativos (Chart.js ou Recharts)
- [ ] Notificações push
- [ ] Multi-idioma (i18n)
- [ ] Dashboard personalizável (drag & drop)
- [ ] Histórico de retorno (gráfico de linha temporal)
- [ ] Alertas customizáveis
- [ ] Export de relatórios (PDF/CSV)

### Melhorias Técnicas

- [ ] Testes unitários (Jest + React Testing Library)
- [ ] Testes E2E (Cypress)
- [ ] Storybook para componentes
- [ ] TypeScript migration
- [ ] Redux ou Zustand para state management
- [ ] React Query para data fetching

---

## Contato

**Desenvolvedor:** Marcos Laine  
**Email:** marcospslaine@gmail.com  
**Repositório:** [GitHub - CryptoBot](https://github.com/MarcosLaine/CryptoBot)

