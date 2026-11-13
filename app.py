import os, json, uuid
from datetime import datetime, timezone
from functools import wraps

import redis
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from pymongo import MongoClient
from supabase import create_client

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "troque-esta-chave")

# MongoDB: produtos | Redis: cache e recentes | Supabase: login do admin
produtos = MongoClient(os.environ["MONGODB_URI"])[os.getenv("MONGODB_DB", "loja")]["produtos"]
r = redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
CACHE_KEY = "catalogo:lista"


def listar():
    try:
        cache = r.get(CACHE_KEY)
        if cache:
            return json.loads(cache), "HIT"
    except redis.RedisError:
        pass
    lista = [dict(d, _id=str(d["_id"])) for d in produtos.find().sort("createdAt", -1)]
    try:
        r.set(CACHE_KEY, json.dumps(lista), ex=60)
    except redis.RedisError:
        pass
    return lista, "MISS"


def admin_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper


@app.context_processor
def globais():
    return {"loja_nome": os.getenv("LOJA_NOME", "Loja"), "whatsapp": os.getenv("WHATSAPP", "")}


@app.get("/")
def loja():
    return render_template("loja.html")


@app.get("/api/produtos")
def api_produtos():
    lista, status = listar()
    resp = jsonify(lista)
    resp.headers["X-Cache"] = status
    return resp


@app.get("/api/recentes")
def recentes_get():
    sid = session.setdefault("sid", uuid.uuid4().hex)
    return jsonify([json.loads(i) for i in r.lrange(f"recentes:{sid}", 0, 4)])


@app.post("/api/recentes")
def recentes_post():
    sid = session.setdefault("sid", uuid.uuid4().hex)
    p = request.get_json(silent=True) or {}
    if not p.get("_id"):
        return jsonify(erro="Dados inválidos"), 400
    k, v = f"recentes:{sid}", json.dumps(p, sort_keys=True)
    pipe = r.pipeline()
    pipe.lrem(k, 0, v); pipe.lpush(k, v); pipe.ltrim(k, 0, 4); pipe.expire(k, 86400)
    pipe.execute()
    return jsonify(ok=True)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email, senha = request.form["email"].strip(), request.form["senha"]
        try:
            cliente = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
            user = cliente.auth.sign_in_with_password({"email": email, "password": senha}).user
            adm = os.getenv("ADMIN_EMAIL")
            if adm and user.email != adm:
                raise PermissionError
            session["admin"] = user.email
            return redirect(url_for("admin"))
        except Exception:
            flash("E-mail ou senha incorretos.", "err")
    return render_template("login.html")


@app.get("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))


@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    if request.method == "POST":
        f = request.form
        try:
            preco = float(f["preco"].replace(",", "."))
            assert f["nome"].strip() and preco >= 0
        except Exception:
            flash("Informe nome e preço válidos.", "err")
            return redirect(url_for("admin"))
        produtos.insert_one({
            "nome": f["nome"].strip(), "descricao": f.get("descricao", ""), "preco": preco,
            "imagem": f.get("imagem", ""), "categoria": f.get("categoria", ""),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        })
        r.delete(CACHE_KEY)  # invalida o cache: catálogo atualiza na hora
        flash("Produto cadastrado. Já aparece no catálogo.", "ok")
        return redirect(url_for("admin"))
    lista = list(produtos.find().sort("createdAt", -1))
    return render_template("admin.html", lista=lista)


@app.post("/admin/excluir/<pid>")
@admin_required
def excluir(pid):
    if ObjectId.is_valid(pid):
        produtos.delete_one({"_id": ObjectId(pid)})
        r.delete(CACHE_KEY)
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
