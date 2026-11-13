# Case Store (Python/Flask) — Projeto de Banco de Dados, 3ª avaliação

| Banco | Uso |
|---|---|
| Supabase (PostgreSQL) | Login/autenticação do administrador |
| MongoDB Atlas | Cadastro e armazenamento dos produtos |
| Redis (Upstash) | Cache do catálogo (60s, invalidado ao cadastrar) e produtos vistos recentemente |

## Configuração
1. Supabase: Authentication > Users > Add user (e-mail/senha, "Auto confirm"). Copie URL e anon key (Project Settings > API).
2. MongoDB Atlas: cluster gratuito, usuário de banco e IP liberado em Network Access. A coleção `produtos` nasce no primeiro cadastro.
3. Upstash: crie um banco Redis e copie a URL `rediss://...`.
4. `cp .env.example .env` e preencha (`ADMIN_EMAIL` = e-mail do admin; `WHATSAPP` = DDI+DDD+número, só dígitos).

## Executar
```
python -m venv venv
venv\Scripts\activate        # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```
Abra http://localhost:5000 (catálogo) e http://localhost:5000/login (admin).
