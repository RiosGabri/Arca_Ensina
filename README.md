# Arca Ensina

Repositório da matéria **Projetos 2**.

## Stack

- **Backend:** Django 6 + Django REST Framework + SimpleJWT (SQLite em dev)
- **Frontend:** React 18 + TypeScript + Vite 8

## Quero rodar localmente

Veja o [**CONTRIBUTING.md**](./.github/CONTRIBUTING.md) — passo a passo de setup do backend, do frontend e roteiro de smoke test manual.

Resumo rápido (dois terminais):

```bash
# Terminal 1 — backend (raiz do repo)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver        # :8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev                       # :5173
```

Abra **http://localhost:5173** no navegador.

## Estrutura

```
project/         ← configurações Django (settings, urls)
accounts/        ← app de autenticação (User, login, register, logout)
frontend/        ← SPA React + Vite
```

> **Convenção:** cada domínio do produto vira um **app Django próprio**. Ao adicionar protocolos clínicos, repositório acadêmico, bulário, calculadora de doses, etc., crie um app novo (`python manage.py startapp <nome>`) em vez de empilhar tudo em `accounts/`. Veja a seção _Adicionando um domínio novo_ no [CONTRIBUTING.md](./.github/CONTRIBUTING.md).
