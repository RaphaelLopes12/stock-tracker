# Stock Tracker

Sistema pessoal de acompanhamento de ações da B3 com suporte a PWA (Progressive Web App).

## Stack

- **Backend:** Python 3.11+ / FastAPI / SQLAlchemy 2.0
- **Frontend:** Vue 3 / TypeScript / Tailwind CSS / PWA
- **Database:** PostgreSQL 16
- **Cache:** Redis 7

## Features

- Lista de ações da B3 com cotações em tempo real
- Indicadores fundamentalistas (P/L, Dividend Yield, etc.)
- Alertas personalizados de preço e indicadores
- Notícias do mercado financeiro
- Dark mode
- **PWA** - Instale no celular como um app nativo

## Quick Start

### Com Docker (recomendado)

```bash
# Copiar variáveis de ambiente
cp .env.example .env

# Subir os containers
docker-compose up -d

# Acessar
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - Swagger UI: http://localhost:8000/docs
```

### Sem Docker

#### Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# ou: source .venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -e .

# Rodar migrations (requer PostgreSQL rodando)
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Iniciar dev server
npm run dev

# Build para produção
npm run build
```

## Deploy em Produção (Gratuito)

### Opção 1: Vercel (Frontend) + Render (Backend) + Supabase (PostgreSQL)

#### 1. Banco de Dados - Supabase (gratuito)

1. Crie uma conta em [supabase.com](https://supabase.com)
2. Crie um novo projeto
3. Vá em Settings > Database > Connection string
4. Copie a URI de conexão (formato: `postgresql://...`)

#### 2. Backend - Render (gratuito)

1. Crie uma conta em [render.com](https://render.com)
2. Conecte seu repositório GitHub
3. Crie um novo "Web Service"
4. Configure:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -e .`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Adicione as variáveis de ambiente:
   - `DATABASE_URL` - URI do Supabase
   - `REDIS_URL` - (opcional, pode usar Upstash)
   - `SECRET_KEY` - Uma string aleatória longa
   - `APP_ENV` - `production`

#### 3. Frontend - Vercel (gratuito)

1. Crie uma conta em [vercel.com](https://vercel.com)
2. Conecte seu repositório GitHub
3. Configure:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Adicione variável de ambiente:
   - `VITE_API_BASE_URL` - URL do seu backend no Render (ex: `https://seu-app.onrender.com/api`)

### Opção 2: Railway (tudo em um lugar)

1. Crie conta em [railway.app](https://railway.app)
2. Conecte o GitHub
3. Adicione um serviço PostgreSQL
4. Deploy o backend e frontend separadamente
5. Configure as variáveis de ambiente

## PWA - Instalando no Celular

O app funciona como PWA e pode ser instalado em qualquer dispositivo:

### Android (Chrome)
1. Acesse o site
2. Toque no menu (3 pontos) > "Instalar aplicativo"

### iPhone (Safari)
1. Acesse o site
2. Toque no botão compartilhar > "Adicionar à Tela de Início"

### Desktop
1. Acesse o site no Chrome
2. Clique no ícone de instalação na barra de endereço

## Estrutura do Projeto

```
stock-tracker/
├── backend/           # API FastAPI
│   ├── app/
│   │   ├── api/       # Routers (stocks, quotes, alerts, news)
│   │   ├── collectors/# Coletores de dados
│   │   ├── core/      # Config, database
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   └── services/  # Business logic
│   └── tests/
├── frontend/          # Vue 3 SPA + PWA
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   ├── stores/    # Pinia stores
│   │   └── services/  # API clients
│   └── public/        # PWA icons
├── notifier/          # Telegram bot (futuro)
└── docker-compose.yml
```

## Roadmap

- [x] Estrutura inicial
- [x] CRUD de ações
- [x] Collector de preços (yfinance)
- [x] Collector de indicadores
- [x] Dashboard com gráficos
- [x] Dark mode
- [x] Alertas de preço e indicadores
- [x] PWA para mobile
- [ ] Alertas automáticos via Telegram
- [ ] Gestão de carteira
- [ ] Recomendações com IA
