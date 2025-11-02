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

### 4. Configurar Persistência do Banco de Dados (IMPORTANTE)

⚠️ **ATENÇÃO: No plano gratuito, o banco de dados SQLite NÃO é persistente!**

O serviço gratuito do Render **não suporta discos persistentes**. Isso significa que:
- Os dados serão perdidos quando o serviço reiniciar
- O serviço entra em "sleep" após 15 minutos de inatividade
- Quando acordar, o banco será recriado vazio

#### Opções:

**Opção 1: Upgrade para Plano Pago (Recomendado para produção)**

1. No serviço Backend, vá em "Settings" → "Plan"
2. Upgrade para o plano **Starter ($7/mês)**
3. Vá em "Disks" → "Add Disk"
4. Configure:
   - **Name:** `cryptobot-db`
   - **Mount Path:** `/opt/render/project/src`
   - **Size:** `1 GB` (incluído no plano)

**Opção 2: Usar PostgreSQL (Grátis, mas requer modificação do código)**

Você pode usar o PostgreSQL gratuito do Render (500MB), mas precisará modificar o código para usar PostgreSQL ao invés de SQLite.

**Opção 3: Aceitar a perda de dados (Apenas para testes)**

Se você está apenas testando, pode usar o plano gratuito sabendo que os dados serão perdidos periodicamente.

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

### Erro no render.yaml

Se você receber erros sobre disk ou region:
- **"disks are not supported for free tier"**: Remova a seção `disk` do render.yaml ou faça upgrade para o plano pago
- **"static sites cannot have a region"**: Remova a linha `region` do serviço frontend

### Dados sendo perdidos

No plano gratuito, isso é esperado. Para resolver:
- Faça upgrade para o plano Starter ($7/mês)
- Ou migre para PostgreSQL (gratuito com 500MB)

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

**No plano gratuito, isso é normal!** O SQLite é efêmero.

Para persistir dados:
- **Opção 1:** Upgrade para plano Starter ($7/mês) e adicione um disco
- **Opção 2:** Migre para PostgreSQL (requer mudanças no código)

### Bot não inicia

Verifique:
- As chaves de API da Binance estão configuradas
- As permissões das chaves incluem leitura e trading
- O backend está rodando corretamente

## Custos

### Plano Free (Para testes apenas)

- ✅ Backend: Free (suspende após 15 min de inatividade)
- ✅ Frontend: Free
- ⚠️ **Banco de dados NÃO é persistente** - dados serão perdidos ao reiniciar

### Plano Starter (Recomendado para uso real)

- Backend: **$7/mês** (não suspende + disco persistente de 1GB incluído)
- Frontend: Free
- ✅ Banco de dados persistente

### Plano com PostgreSQL (Alternativa)

- Backend: Free ou $7/mês
- PostgreSQL: Free (500MB) ou $7/mês (10GB)
- Requer modificação do código para usar PostgreSQL

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

