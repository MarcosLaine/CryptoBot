# 📚 CryptoBot - Documentação da API

## Índice
- [Visão Geral](#visão-geral)
- [Tecnologias](#tecnologias)
- [Arquitetura](#arquitetura)
- [Autenticação](#autenticação)
- [Endpoints](#endpoints)
  - [Autenticação](#endpoints-de-autenticação)
  - [Portfolio](#endpoints-de-portfolio)
  - [Transações](#endpoints-de-transações)
  - [Estatísticas](#endpoints-de-estatísticas)
  - [API Keys](#endpoints-de-api-keys)
  - [Bot](#endpoints-de-bot)
  - [Configurações](#endpoints-de-configurações)
  - [Ativos](#endpoints-de-ativos)
- [Banco de Dados](#banco-de-dados)
- [Bot de Trading](#bot-de-trading)
- [Segurança](#segurança)
- [Deploy](#deploy)

---

## Visão Geral

A CryptoBot API é uma API REST construída com Flask que fornece funcionalidades completas para gerenciamento de portfólio de criptomoedas, trading automatizado e integração com a Binance.

**Base URL:** `https://cryptobot-api-jcrn.onrender.com`

**Características principais:**
- ✅ Sistema de autenticação JWT
- ✅ Gerenciamento de portfolio multi-usuário
- ✅ Bot de trading automatizado com médias móveis
- ✅ Integração completa com Binance API
- ✅ Armazenamento seguro de API keys com criptografia
- ✅ Sistema de configurações personalizáveis por usuário
- ✅ Sincronização de transações históricas

---

## Tecnologias

### Backend Stack
```
Flask 3.0.0               - Framework web
Flask-CORS 4.0.0          - Cross-Origin Resource Sharing
Flask-JWT-Extended 4.5.3  - Autenticação JWT
Werkzeug 3.0.1            - Segurança e hashing de senhas
SQLite3                   - Banco de dados
Cryptography 41.0.7       - Criptografia de API secrets
python-binance 1.0.19     - Cliente Binance
pandas 2.1.4              - Análise de dados
gunicorn 21.2.0           - WSGI HTTP Server
```

---

## Arquitetura

### Estrutura de Diretórios
```
CryptoBot/
├── app.py                      # API Flask principal
├── bot.py                      # Lógica do bot de trading
├── cryptobot.db                # Banco de dados SQLite
├── requirements.txt            # Dependências Python
├── Procfile                    # Configuração de deploy
├── runtime.txt                 # Versão do Python
├── Indicators/
│   ├── moving_averages.py      # Cálculo de médias móveis
│   └── rsi.py                  # Indicador RSI
├── src/
│   ├── strategy/
│   │   └── tranding_strategy.py # Estratégia de trading
│   └── information/
│       ├── show_info.py         # Display de informações
│       └── check_position.py    # Verificação de posições
└── utils/
    ├── data.py                  # Utilidades de dados
    └── transaction_sync.py      # Sincronização de transações
```

### Fluxo de Dados
```
Cliente (Frontend)
    ↓
API Flask (app.py)
    ↓
├─→ Autenticação JWT
├─→ Banco de Dados SQLite
├─→ Binance Client
└─→ Bot Thread (bot.py)
    ↓
Estratégia de Trading
    ↓
Binance Exchange
```

---

## Autenticação

A API utiliza JSON Web Tokens (JWT) para autenticação.

### Fluxo de Autenticação
1. **Registro/Login** → Recebe JWT token
2. **Incluir token** em todas as requisições protegidas
3. **Token expira** após 24 horas

### Header de Autenticação
```http
Authorization: Bearer <seu_jwt_token>
```

### Configuração JWT
- **Secret Key:** Definido via variável de ambiente `JWT_SECRET_KEY`
- **Expiração:** 24 horas
- **Algoritmo:** HS256

---

## Endpoints

### Endpoints de Autenticação

#### POST /api/register
Registra um novo usuário.

**Request Body:**
```json
{
  "username": "usuario@example.com",
  "password": "senha_segura"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "user_id": 1
}
```

**Errors:**
- `400` - Username and password are required
- `400` - Username already exists

---

#### POST /api/login
Autentica um usuário existente.

**Request Body:**
```json
{
  "username": "usuario@example.com",
  "password": "senha_segura"
}
```

**Response (200):**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "user_id": 1
}
```

**Errors:**
- `400` - Username and password are required
- `401` - Invalid credentials

---

### Endpoints de Portfolio

#### GET /api/portfolio
Retorna o portfolio completo do usuário com valores atualizados.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "portfolio": [
    {
      "asset": "BTC",
      "symbol": "BTCUSDT",
      "quantity": 0.005,
      "current_price": 42000.50,
      "value_usdt": 210.0025,
      "invested": 200.00,
      "return_amount": 10.0025,
      "return_percentage": 5.00125,
      "media_curta": 41950.25,
      "media_longa": 41800.75
    }
  ],
  "total_value": 1250.50,
  "total_invested": 1000.00,
  "total_return": 250.50,
  "total_return_percentage": 25.05
}
```

**Funcionalidades:**
- Busca saldo atual na Binance para cada ativo habilitado
- Calcula valor investido baseado no histórico de transações
- Calcula retorno (valor atual - investido)
- Calcula médias móveis (curta: 7 períodos, longa: 40 períodos)
- Usa `recvWindow=60000` para evitar problemas de timestamp

**Errors:**
- `400` - API keys not configured
- `500` - Error accessing Binance account

---

### Endpoints de Transações

#### GET /api/transactions
Retorna histórico de transações do usuário.

**Headers:**
```http
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (opcional): Número de transações (padrão: 50)

**Response (200):**
```json
{
  "transactions": [
    {
      "asset": "BTCUSDT",
      "type": "BUY",
      "quantity": 0.005,
      "price": 40000.00,
      "total": 200.00,
      "timestamp": "2025-11-02T10:30:00"
    },
    {
      "asset": "ETHUSDT",
      "type": "SELL",
      "quantity": 0.1,
      "price": 2500.00,
      "total": 250.00,
      "timestamp": "2025-11-02T09:15:00"
    }
  ]
}
```

---

#### POST /api/sync-transactions
Sincroniza transações históricas da Binance.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Synced 15 new transactions",
  "count": 15
}
```

**Comportamento:**
- Busca últimas 500 transações de cada ativo habilitado
- Evita duplicatas verificando timestamp, quantidade e preço
- Processa apenas novos trades não registrados no banco

**Errors:**
- `400` - API keys not configured

---

#### POST /api/reset-transactions
Reseta todas as transações e snapshots do portfolio.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Transactions and portfolio data reset successfully. Total invested and return will be recalculated from new transactions."
}
```

**Ações realizadas:**
- Deleta todas as transações do usuário
- Deleta todos os portfolio snapshots
- Reseta cálculos de investimento e retorno

**Errors:**
- `400` - Cannot reset transactions while bot is running. Please stop the bot first.

---

### Endpoints de Estatísticas

#### GET /api/stats
Retorna estatísticas gerais do usuário.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "usdt_balance": 1500.75,
  "total_invested": 1000.00,
  "total_transactions": 25,
  "active_positions": 3
}
```

**Campos:**
- `usdt_balance`: Saldo disponível em USDT na Binance
- `total_invested`: Total investido (soma de compras - vendas)
- `total_transactions`: Número total de transações
- `active_positions`: Número de ativos com saldo > 0

**Errors:**
- `400` - API keys not configured
- `500` - Error accessing Binance account

---

### Endpoints de API Keys

#### GET /api/api-keys
Verifica se o usuário possui API keys configuradas.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "has_keys": true,
  "api_key_masked": "12345678...abcd"
}
```

ou

```json
{
  "has_keys": false
}
```

---

#### POST /api/api-keys
Salva ou atualiza as API keys da Binance.

**Headers:**
```http
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "api_key": "sua_api_key_binance",
  "api_secret": "seu_api_secret_binance"
}
```

**Response (200):**
```json
{
  "message": "API keys saved successfully"
}
```

**Segurança:**
- API Secret é criptografada usando Fernet (criptografia simétrica)
- Validação das keys fazendo chamada de teste para Binance
- API Secret nunca é retornada em GET requests

**Errors:**
- `400` - API key and secret are required
- `400` - Chaves de API inválidas (falha na validação com Binance)
- `400` - Erro de sincronização de tempo (timestamp issues)

---

### Endpoints de Bot

#### GET /api/bot/status
Retorna o status atual do bot.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "is_running": true,
  "started_at": "2025-11-02T10:00:00",
  "stopped_at": null
}
```

**Verificações:**
- Verifica se a thread do bot está ativa
- Sincroniza estado do banco de dados com estado real da thread
- Corrige inconsistências automaticamente

---

#### POST /api/bot/start
Inicia o bot de trading para o usuário.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Bot started successfully"
}
```

**Comportamento:**
1. Verifica se API keys estão configuradas
2. Descriptografa API secret
3. Carrega configurações do usuário (intervalo de verificação)
4. Carrega ativos habilitados do usuário
5. Cria thread daemon para executar o bot
6. Atualiza status no banco de dados

**Errors:**
- `400` - Bot is already running
- `400` - API keys not configured
- `400` - API keys encryption error

---

#### POST /api/bot/stop
Para o bot de trading do usuário.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Bot stopped successfully"
}
```

**Comportamento:**
1. Define flag de parada
2. Aguarda thread finalizar (timeout: 5 segundos)
3. Remove referências da thread
4. Atualiza status no banco de dados

---

### Endpoints de Configurações

#### GET /api/bot/settings
Retorna configurações do bot.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "check_interval_minutes": 30
}
```

---

#### POST /api/bot/settings
Atualiza configurações do bot.

**Headers:**
```http
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "check_interval_minutes": 60
}
```

**Response (200):**
```json
{
  "message": "Settings saved successfully",
  "check_interval_minutes": 60
}
```

**Validações:**
- Intervalo deve estar entre 1 e 1440 minutos (24 horas)
- Bot deve estar parado para alterar configurações

**Errors:**
- `400` - check_interval_minutes is required
- `400` - Interval must be between 1 and 1440 minutes
- `400` - Cannot change settings while bot is running

---

### Endpoints de Ativos

#### GET /api/assets
Lista todos os ativos disponíveis.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "assets": [
    {"symbol": "BTCUSDT", "name": "Bitcoin (BTC)"},
    {"symbol": "ETHUSDT", "name": "Ethereum (ETH)"},
    {"symbol": "BNBUSDT", "name": "Binance Coin (BNB)"},
    {"symbol": "SOLUSDT", "name": "Solana (SOL)"},
    {"symbol": "XRPUSDT", "name": "Ripple (XRP)"},
    {"symbol": "ADAUSDT", "name": "Cardano (ADA)"},
    {"symbol": "DOGEUSDT", "name": "Dogecoin (DOGE)"},
    {"symbol": "MATICUSDT", "name": "Polygon (MATIC)"},
    {"symbol": "DOTUSDT", "name": "Polkadot (DOT)"},
    {"symbol": "AVAXUSDT", "name": "Avalanche (AVAX)"}
  ]
}
```

---

#### GET /api/assets/settings
Retorna configurações de ativos do usuário.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "assets": [
    {
      "symbol": "BTCUSDT",
      "name": "Bitcoin (BTC)",
      "enabled": true,
      "investment_amount": 50.0
    },
    {
      "symbol": "ETHUSDT",
      "name": "Ethereum (ETH)",
      "enabled": false,
      "investment_amount": 0.0
    }
  ]
}
```

**Campos:**
- `enabled`: Se o ativo está habilitado para trading
- `investment_amount`: Valor em USDT a investir por operação

---

#### POST /api/assets/settings
Salva configurações de ativos.

**Headers:**
```http
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "assets": [
    {
      "symbol": "BTCUSDT",
      "name": "Bitcoin (BTC)",
      "enabled": true,
      "investment_amount": 50.0
    },
    {
      "symbol": "ETHUSDT",
      "name": "Ethereum (ETH)",
      "enabled": true,
      "investment_amount": 30.0
    }
  ]
}
```

**Response (200):**
```json
{
  "message": "Asset settings saved successfully"
}
```

**Validações:**
- Símbolos devem estar na lista de ativos permitidos
- Valores de investimento devem ser positivos
- Bot deve estar parado para alterar configurações

**Errors:**
- `400` - assets must be a list
- `400` - Investment amount must be positive
- `400` - Cannot change asset settings while bot is running

---

## Banco de Dados

### Estrutura das Tabelas

#### users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### transactions
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    asset TEXT NOT NULL,
    type TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    total REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

#### portfolio_snapshots
```sql
CREATE TABLE portfolio_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    asset TEXT NOT NULL,
    quantity REAL NOT NULL,
    value_usdt REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

#### api_keys
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    api_key TEXT NOT NULL,
    api_secret TEXT NOT NULL,  -- Criptografado
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

#### bot_status
```sql
CREATE TABLE bot_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    is_running INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    stopped_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

#### bot_settings
```sql
CREATE TABLE bot_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    check_interval_minutes INTEGER DEFAULT 30,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

#### asset_settings
```sql
CREATE TABLE asset_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    asset_symbol TEXT NOT NULL,
    asset_name TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    investment_amount REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, asset_symbol)
);
```

---

## Bot de Trading

### Estratégia de Trading

O bot utiliza uma estratégia baseada em **médias móveis**:

#### Indicadores
- **Média Móvel Curta:** 7 períodos
- **Média Móvel Longa:** 40 períodos
- **Timeframe:** 30 minutos

#### Sinais de Trading

**Sinal de Compra:**
```python
if media_curta > media_longa and (not_positioned or valor_em_usdt < 5):
    # Executar compra
```

**Sinal de Venda:**
```python
if media_curta <= media_longa and is_totally_positioned:
    # Executar venda
```

### Fluxo de Execução

```
Iniciar Bot
    ↓
Carregar Configurações
    ↓
Para cada ativo habilitado:
    ↓
    1. Buscar dados históricos (30min)
    ↓
    2. Calcular médias móveis
    ↓
    3. Verificar posição atual
    ↓
    4. Avaliar sinal de trading
    ↓
    5. Executar ordem (se necessário)
    ↓
    6. Registrar transação no banco
    ↓
Aguardar intervalo configurado
    ↓
Repetir (ou parar se flag de stop for ativada)
```

### Gerenciamento de Risco

1. **Quantidade de Compra:**
   ```python
   quantidade = investment_amount / preco_atual
   ```
   
2. **Precisão e Limites:**
   - Respeita `LOT_SIZE` filter da Binance
   - Ajusta precisão decimal conforme `step_size`
   - Valida quantidade mínima (`min_qty`)

3. **Venda Segura:**
   ```python
   quantidade_venda = floor(saldo_disponivel / step_size) * step_size
   ```

### Tratamento de Erros

- **Timestamp Issues:** Usa `recvWindow=60000` em todas as chamadas
- **Sincronização de Tempo:** Verifica offset com servidor Binance
- **Exceções por Ativo:** Erros em um ativo não interrompem processamento dos outros
- **Thread Safety:** Usa flags compartilhadas para controle de parada

---

## Segurança

### Criptografia de API Secrets

**Algoritmo:** Fernet (criptografia simétrica)

**Fluxo:**
1. Chave de criptografia gerada/carregada de `.encryption_key`
2. API Secret criptografada antes de salvar no banco
3. API Secret descriptografada apenas quando necessário
4. API Secret nunca exposta em logs ou responses

```python
def encrypt_secret(secret):
    return cipher_suite.encrypt(secret.encode()).decode()

def decrypt_secret(encrypted_secret):
    return cipher_suite.decrypt(encrypted_secret.encode()).decode()
```

### Hash de Senhas

**Algoritmo:** Werkzeug PBKDF2

```python
password_hash = generate_password_hash(password)
check_password_hash(stored_hash, provided_password)
```

### CORS Configuration

```python
CORS(app, 
     resources={r"/api/*": {"origins": "*"}},
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=False,
     send_wildcard=True)
```

### JWT Configuration

```python
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
```

---

## Deploy

### Variáveis de Ambiente

```env
# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production

# Criptografia
ENCRYPTION_KEY=your-fernet-key

# Binance (opcional - fallback para .env)
KEY_BINANCE=your_api_key
SECRET_BINANCE=your_api_secret

# Render
PORT=8000
RENDER=true  # Define database path
```

### Procfile (Render/Heroku)

```
web: gunicorn app:app
```

### Runtime

```
python-3.11.6
```

### Database Path

```python
# Render: /opt/render/project/src/cryptobot.db
# Local: ./cryptobot.db
DB_DIR = os.environ.get('RENDER') and '/opt/render/project/src' or os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, 'cryptobot.db')
```

---

## Exemplos de Uso

### Fluxo Completo com cURL

**1. Registrar usuário:**
```bash
curl -X POST https://cryptobot-api-jcrn.onrender.com/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"senha123"}'
```

**2. Login:**
```bash
curl -X POST https://cryptobot-api-jcrn.onrender.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"senha123"}'
```

**3. Configurar API Keys:**
```bash
curl -X POST https://cryptobot-api-jcrn.onrender.com/api/api-keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -d '{"api_key":"sua_api_key","api_secret":"seu_api_secret"}'
```

**4. Configurar ativos:**
```bash
curl -X POST https://cryptobot-api-jcrn.onrender.com/api/assets/settings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -d '{
    "assets": [
      {"symbol":"BTCUSDT","name":"Bitcoin (BTC)","enabled":true,"investment_amount":50},
      {"symbol":"ETHUSDT","name":"Ethereum (ETH)","enabled":true,"investment_amount":30}
    ]
  }'
```

**5. Iniciar bot:**
```bash
curl -X POST https://cryptobot-api-jcrn.onrender.com/api/bot/start \
  -H "Authorization: Bearer SEU_TOKEN"
```

**6. Verificar portfolio:**
```bash
curl -X GET https://cryptobot-api-jcrn.onrender.com/api/portfolio \
  -H "Authorization: Bearer SEU_TOKEN"
```

---

## Troubleshooting

### Erro de Timestamp (-1021)

**Problema:** `Timestamp for this request was 1000ms ahead of the server's time`

**Solução:**
- API usa `recvWindow=60000` automaticamente
- Sincronização de tempo na inicialização do bot
- Verificar relógio do sistema

### Erro de Descriptografia

**Problema:** `Failed to decrypt API secret`

**Causa:** `ENCRYPTION_KEY` foi alterada

**Solução:**
1. Reconfigurar API keys no frontend
2. Ou restaurar `ENCRYPTION_KEY` original do arquivo `.encryption_key`

### Bot não inicia

**Checklist:**
- [ ] API keys configuradas?
- [ ] API keys válidas (testadas com Binance)?
- [ ] Bot já está rodando?
- [ ] Verificar logs do servidor

---

## Códigos de Status HTTP

| Código | Significado |
|--------|-------------|
| 200 | Sucesso |
| 201 | Recurso criado |
| 400 | Requisição inválida |
| 401 | Não autenticado |
| 403 | Não autorizado |
| 404 | Não encontrado |
| 500 | Erro interno do servidor |

---

## Contato

**Desenvolvedor:** Marcos Laine  
**Email:** marcospslaine@gmail.com  
**Repositório:** [GitHub - CryptoBot](https://github.com/MarcosLaine/CryptoBot)

