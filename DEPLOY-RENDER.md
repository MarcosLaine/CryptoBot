# Guia de Deploy no Render - CryptoBot

Este guia explica como fazer o deploy do CryptoBot no Render.

## Pré-requisitos

- Conta no [Render](https://render.com)
- Repositório Git com o código (GitHub, GitLab ou Bitbucket)

## Arquitetura do Deploy

O projeto será deployado em dois serviços:

1. **Backend API** (Web Service) - Flask/Python
2. **Frontend** (Static Site) - React

## Passo a Passo

### 1. Preparar o Repositório

Certifique-se de que todos os arquivos de configuração estão no repositório:
- ✅ `render.yaml` - Configuração dos serviços
- ✅ `requirements.txt` - Dependências Python
- ✅ `Procfile` - Comando para iniciar o servidor
- ✅ `runtime.txt` - Versão do Python
- ✅ `frontend/package.json` - Dependências Node.js

### 2. Deploy via Render Dashboard

#### Opção A: Deploy Automático (Recomendado)

1. Acesse [Render Dashboard](https://dashboard.render.com)
2. Clique em "New +" → "Blueprint"
3. Conecte seu repositório Git
4. Selecione o repositório `CryptoBot`
5. O Render detectará automaticamente o `render.yaml`
6. Clique em "Apply" para criar os serviços

#### Opção B: Deploy Manual

**Backend API:**

1. Acesse [Render Dashboard](https://dashboard.render.com)
2. Clique em "New +" → "Web Service"
3. Conecte seu repositório
4. Configure:
   - **Name:** `cryptobot-api`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free

5. Adicione variáveis de ambiente:
   - `PYTHON_VERSION`: `3.11.0`
   - `JWT_SECRET_KEY`: (deixe o Render gerar automaticamente)
   - `ENCRYPTION_KEY`: (deixe o Render gerar automaticamente)

6. Clique em "Create Web Service"

**Frontend:**

1. No Dashboard, clique em "New +" → "Static Site"
2. Conecte o mesmo repositório
3. Configure:
   - **Name:** `cryptobot-frontend`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `build`
   - **Plan:** Free

4. Adicione variável de ambiente:
   - `REACT_APP_API_URL`: `https://cryptobot-api.onrender.com` (URL do backend)

5. Clique em "Create Static Site"

### 3. Configurar CORS no Backend

Após o deploy do frontend, atualize a URL no CORS do backend (se necessário):

No arquivo `app.py`, a configuração já permite todas as origens:
```python
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

### 4. Configurar Persistência do Banco de Dados

O backend usa SQLite. Para persistir os dados:

1. No serviço Backend, vá em "Disks"
2. Clique em "Add Disk"
3. Configure:
   - **Name:** `cryptobot-db`
   - **Mount Path:** `/opt/render/project/src`
   - **Size:** `1 GB`

### 5. URLs dos Serviços

Após o deploy, você terá:

- **API Backend:** `https://cryptobot-api.onrender.com`
- **Frontend:** `https://cryptobot-frontend.onrender.com`

### 6. Testar o Deploy

1. Acesse a URL do frontend
2. Crie uma conta
3. Configure suas chaves de API da Binance
4. Comece a usar o bot!

## Variáveis de Ambiente Importantes

### Backend (Obrigatórias)

- `JWT_SECRET_KEY`: Chave secreta para JWT (gerada automaticamente)
- `ENCRYPTION_KEY`: Chave para criptografar API keys (gerada automaticamente)
- `PORT`: Porta do servidor (definida pelo Render)

### Frontend (Opcional)

- `REACT_APP_API_URL`: URL do backend (padrão: `http://localhost:8000`)

## Troubleshooting

### Erro de Build no Frontend

Se houver erro no build do frontend:
```bash
npm run build
```

Verifique:
- Todas as dependências estão no `package.json`
- Não há erros de linting/compilação

### Erro de Conexão com API

Verifique:
- A variável `REACT_APP_API_URL` está configurada corretamente
- O backend está rodando
- O CORS está permitindo a origem do frontend

### Database não persiste

Certifique-se de que:
- O disco está configurado no serviço backend
- O mount path está correto: `/opt/render/project/src`

### Bot não inicia

Verifique:
- As chaves de API da Binance estão configuradas
- As permissões das chaves incluem leitura e trading
- O backend está rodando corretamente

## Custos

### Plano Free (Recomendado para começar)

- ✅ Backend: Free (suspende após 15 min de inatividade)
- ✅ Frontend: Free
- ✅ Disco: Free (500 MB)

### Plano Starter (Para uso contínuo)

- Backend: $7/mês (não suspende)
- Frontend: Free
- Disco: $1/GB/mês

## Atualizações

O Render faz deploy automático quando você faz push para a branch principal:

```bash
git add .
git commit -m "feat: atualização do bot"
git push origin main
```

## Backup do Banco de Dados

É recomendado fazer backup periódico do arquivo `cryptobot.db`:

1. Acesse o serviço Backend no Render
2. Vá em "Shell"
3. Execute:
```bash
cat cryptobot.db > backup.db
```

## Suporte

Para problemas:
- Verifique os logs no Dashboard do Render
- Consulte a [documentação do Render](https://render.com/docs)
- Abra uma issue no repositório

## Segurança

⚠️ **IMPORTANTE:**

1. Nunca faça commit de arquivos `.env` com credenciais reais
2. Use apenas as variáveis de ambiente do Render
3. Configure permissões mínimas nas chaves de API da Binance
4. Não habilite permissão de saque nas chaves de API

## Links Úteis

- [Render Dashboard](https://dashboard.render.com)
- [Documentação Render](https://render.com/docs)
- [Binance API Documentation](https://binance-docs.github.io/apidocs/)

