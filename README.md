# Arca Ensina

Repositório da matéria **Projetos 2**.

## Stack

- **Backend:** Django 6 + Django REST Framework + SimpleJWT (SQLite em dev)
- **Frontend:** React 18 + TypeScript + Vite 8

## Quero rodar localmente

Veja o [**CONTRIBUTING.md**](./.github/CONTRIBUTING.md) — passo a passo de setup do backend, do frontend e roteiro de smoke test manual.

Resumo rápido (dois terminais):

```bash
# Terminal 1 — backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py runserver        # :8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev                       # :5173
```

Ou com Docker (tudo de uma vez):

```bash
cp .env.example .env
docker compose up
```

Migrations rodam automaticamente na primeira inicialização.

Abra **http://localhost:5173** no navegador.

## Estrutura

```
backend/
  project/       ← configurações Django (settings, urls)
  apps/
    accounts/    ← autenticação (User, login, register, logout)
    audit/       ← auditoria (AuditLog, AuditableMixin)
frontend/        ← SPA React + Vite
docs/            ← planejamento (stories, infra, roadmap)
```

> **Convenção:** cada domínio do produto vira um **app Django próprio** dentro de `backend/apps/`. Ao adicionar protocolos clínicos, repositório acadêmico, bulário, calculadora de doses, etc., crie um app novo em vez de empilhar tudo em `accounts/`. Veja a seção _Adicionando um domínio novo_ no [CONTRIBUTING.md](./.github/CONTRIBUTING.md).
