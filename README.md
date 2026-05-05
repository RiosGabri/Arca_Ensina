# ARCA Ensina 🩺

![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)
![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

---

## Descrição

Aplicação web multiplataforma para centralizar protocolos médicos e oferecer ferramentas de apoio à prática clínica. Reúne conteúdos da equipe **ARCA Ensina** com funcionalidades que auxiliam na tomada de decisão e organização do fluxo de trabalho médico.

Público-alvo: pediatras intensivistas recém-formados.

---

## Stack

- **Backend:** Django 6 + Django REST Framework + SimpleJWT (SQLite em dev, PostgreSQL em Docker/prod)
- **Frontend:** React 18 + TypeScript + Vite
- **CI/CD:** GitHub Actions + Docker Compose

---

## Quero rodar localmente

Veja o [**CONTRIBUTING.md**](./.github/CONTRIBUTING.md) para o guia completo.

### Docker (recomendado)

```bash
cp .env.example .env
docker compose up
```

Migrations rodam automaticamente na primeira inicialização.

### Manual (dois terminais)

```bash
# Terminal 1 — backend
cp .env.example .env              # obrigatório (SECRET_KEY, etc.)
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

Abra **http://localhost:5173** no navegador.

---

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

> **Convenção:** cada domínio do produto vira um **app Django próprio** dentro de `backend/apps/`. Veja a seção _Adicionando um domínio novo_ no [CONTRIBUTING.md](./.github/CONTRIBUTING.md).

---

## Funcionalidades

- Consulta de protocolos médicos
- Calculadoras de medicamentos
- Interface responsiva
- Modo Offline
- Bulário digital
- Suporte à exportação de dados para pesquisa

---

<details>
<summary><strong>Status Report 1</strong></summary>

### Pesquisa e Análise
- Levantamento de aplicações similares
- Análise comparativa

### Persona
- Definição do perfil do usuário

### Jornada do Usuário
- Mapeamento de interações

### Coleta de Dados
- Aplicação de formulário
- Análise dos resultados

### Ideação
- Divisão em 3 equipes
- Uso de diferentes abordagens

### Priorização (MoSCoW)
- **Must have** – essenciais
- **Should have** – importantes
- **Could have** – desejáveis
- **Won't have** – fora do escopo

### Planejamento Ágil
- Histórias de usuário
- Organização em 3 épicos

### Gestão
- Uso do Jira
- Apresentação de Status Report

</details>

---

## 👨‍💻 Equipe

### Desenvolvedores

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/ariel-cs"><img height="460" src="https://github.com/user-attachments/assets/13d60fdf-6d99-4373-ac76-e441b8ffa840" width="100px;" alt="Ariel"/><br /><sub><b>Ariel</b></sub></a><br /><a href="https://github.com/ArcaEnsina/Arca_Ensina/commits?author=ariel-cs" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Torzinus"><img height="1002" src="https://github.com/user-attachments/assets/d889e425-ea83-4e75-acc2-00cbedef934e" width="100px;" alt="Heitor de Carvalho"/><br /><sub><b>Heitor de Carvalho</b></sub></a><br /><a href="https://github.com/ArcaEnsina/Arca_Ensina/commits?author=Torzinus" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/venici-o"><img height="460" src="https://github.com/user-attachments/assets/cd50eb23-3cc6-4d3d-a24b-20508b26b553" width="100px;" alt="Vinicius"/><br /><sub><b>Vinicius</b></sub></a><br /><a href="https://github.com/ArcaEnsina/Arca_Ensina/commits?author=venici-o" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://larissagiovanna.github.io/LarissaGiovanna/"><img height="850" src="https://github.com/user-attachments/assets/e2e2cf66-2b4a-4145-b129-8f0914e1f318" width="100px;" alt="Larissa Giovanna"/><br /><sub><b>Larissa Giovanna</b></sub></a><br /><a href="https://github.com/ArcaEnsina/Arca_Ensina/commits?author=LarissaGiovanna" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/RiosGabri"><img height="247" src="https://github.com/user-attachments/assets/db01344d-956e-4299-ad36-405d3d55cbc6" width="100px;" alt="Gabriel Parméra"/><br /><sub><b>Gabriel Parméra</b></sub></a><br /><a href="https://github.com/ArcaEnsina/Arca_Ensina/commits?author=RiosGabri" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/DoctahW"><img height="460" src="https://github.com/user-attachments/assets/3e3fc5df-922b-4fa1-b917-9692f34f8bc8" width="100px;" alt="João Euclides"/><br /><sub><b>João Euclides</b></sub></a><br /><a href="https://github.com/ArcaEnsina/Arca_Ensina/commits?author=DoctahW" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/joaorafaelsga"><img height="460" src="https://github.com/user-attachments/assets/1a12ecd5-2bdd-4847-9e59-befd29925384" width="100px;" alt="João Rafael"/><br /><sub><b>João Rafael</b></sub></a><br /><a href="https://github.com/ArcaEnsina/Arca_Ensina/commits?author=joaorafaelsga" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

### Designers

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><img height="460" src="https://github.com/user-attachments/assets/b54fc7cf-2594-4dbd-9039-c9cda11328ba" width="100px;" alt="Leticia Catunda"/><br /><sub><b>Leticia Catunda</b></sub><br />🎨</td>
      <td align="center" valign="top" width="14.28%"><img height="460" src="https://github.com/user-attachments/assets/ceb0ef58-5c2b-492c-8ffa-eaae9f4f54f9" width="100px;" alt="Maria Fernanda"/><br /><sub><b>Maria Fernanda</b></sub><br />🎨</td>
      <td align="center" valign="top" width="14.28%"><img height="460" src="https://github.com/user-attachments/assets/c28cb8f1-2ac9-4786-9869-e78bf1d22b3c" width="100px;" alt="Helena Nascimento"/><br /><sub><b>Helena Nascimento</b></sub><br />🎨</td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
