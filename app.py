import sqlite3

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "chave_secreta_feirinha_digital"

BANCO = "banco.db"


def conectar_banco():
    """Abre uma conexão com o banco de dados SQLite."""
    conexao = sqlite3.connect(BANCO)
    # Permite acessar as colunas pelo nome (ex: produto['nome'])
    conexao.row_factory = sqlite3.Row
    # Ativa o suporte a chaves estrangeiras no SQLite
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def inicializar_banco():
    """Cria as tabelas e insere dados de exemplo caso o banco esteja vazio."""
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Tabela 1: Vendedores da feira
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            barraca TEXT NOT NULL,
            telefone TEXT NOT NULL,
            dia_feira TEXT NOT NULL
        )
    """)

    # Tabela 2: Produtos (relacionada com a tabela vendedores via chave estrangeira)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            preco REAL NOT NULL,
            unidade TEXT NOT NULL,
            disponivel INTEGER NOT NULL DEFAULT 1,
            vendedor_id INTEGER NOT NULL,
            FOREIGN KEY (vendedor_id) REFERENCES vendedores (id) ON DELETE CASCADE
        )
    """)

    # Verifica se já existem vendedores cadastrados
    cursor.execute("SELECT COUNT(*) AS total FROM vendedores")
    total_vendedores = cursor.fetchone()["total"]

    if total_vendedores == 0:
        # Dados iniciais de exemplo para a Feirinha do Bairro
        vendedores_exemplo = [
            ("Dona Maria", "Barraca da Horta (Setor A)", "(11) 98765-4321", "Sábado"),
            (
                "Seu João",
                "Pomar do Bairro (Setor B)",
                "(11) 99123-4567",
                "Sábado e Domingo",
            ),
            ("Ana Paula", "Delícias Caseiras (Setor C)", "(11) 97654-3210", "Domingo"),
        ]
        cursor.executemany(
            "INSERT INTO vendedores (nome, barraca, telefone, dia_feira) VALUES (?, ?, ?, ?)",
            vendedores_exemplo,
        )

        produtos_exemplo = [
            ("Alface Crespa Orgânica", "Hortaliças", 3.50, "maço", 1, 1),
            ("Tomate Italiano", "Legumes", 8.90, "kg", 1, 1),
            ("Cenoura Fresca", "Legumes", 6.00, "kg", 1, 1),
            ("Banana Nanica", "Frutas", 7.50, "dúzia", 1, 2),
            ("Maçã Gala", "Frutas", 11.90, "kg", 1, 2),
            ("Morango Selecionado", "Frutas", 10.00, "bandeja", 0, 2),
            ("Queijo Minas Frescal", "Laticínios e Caseiros", 28.00, "unidade", 1, 3),
            ("Pão de Milho Caseiro", "Laticínios e Caseiros", 14.00, "unidade", 1, 3),
        ]
        cursor.executemany(
            """INSERT INTO produtos
               (nome, categoria, preco, unidade, disponivel, vendedor_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            produtos_exemplo,
        )

    conexao.commit()
    conexao.close()


# ==========================================
# ROTA 1: Página Inicial (Vitrine com JOIN)
# ==========================================
@app.route("/")
def index():
    categoria_filtro = request.args.get("categoria", "")

    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Consulta utilizando INNER JOIN entre produtos e vendedores
    if categoria_filtro:
        cursor.execute(
            """
            SELECT produtos.*, vendedores.nome AS vendedor_nome,
                   vendedores.barraca AS vendedor_barraca,
                   vendedores.telefone AS vendedor_telefone,
                   vendedores.dia_feira AS vendedor_dia
            FROM produtos
            INNER JOIN vendedores ON produtos.vendedor_id = vendedores.id
            WHERE produtos.categoria = ?
            ORDER BY produtos.nome
            """,
            (categoria_filtro,),
        )
    else:
        cursor.execute(
            """
            SELECT produtos.*, vendedores.nome AS vendedor_nome,
                   vendedores.barraca AS vendedor_barraca,
                   vendedores.telefone AS vendedor_telefone,
                   vendedores.dia_feira AS vendedor_dia
            FROM produtos
            INNER JOIN vendedores ON produtos.vendedor_id = vendedores.id
            ORDER BY produtos.nome
            """
        )

    produtos = cursor.fetchall()
    conexao.close()

    categorias = ["Frutas", "Legumes", "Hortaliças", "Laticínios e Caseiros", "Outros"]
    return render_template(
        "index.html",
        produtos=produtos,
        categorias=categorias,
        categoria_selecionada=categoria_filtro,
    )


# ==========================================
# ROTA 2: Cadastrar Novo Produto (GET e POST)
# ==========================================
@app.route("/produtos/novo", methods=["GET", "POST"])
def novo_produto():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        categoria = request.form["categoria"]
        preco = float(request.form["preco"])
        unidade = request.form["unidade"]
        disponivel = 1 if "disponivel" in request.form else 0
        vendedor_id = int(request.form["vendedor_id"])

        cursor.execute(
            """
            INSERT INTO produtos (nome, categoria, preco, unidade, disponivel, vendedor_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (nome, categoria, preco, unidade, disponivel, vendedor_id),
        )
        conexao.commit()
        conexao.close()

        flash("Produto cadastrado com sucesso!", "sucesso")
        return redirect(url_for("index"))

    # Se for GET, busca os vendedores para preencher o campo <select>
    cursor.execute("SELECT * FROM vendedores ORDER BY nome")
    vendedores = cursor.fetchall()
    conexao.close()

    categorias = ["Frutas", "Legumes", "Hortaliças", "Laticínios e Caseiros", "Outros"]
    return render_template(
        "novo_produto.html", vendedores=vendedores, categorias=categorias
    )


# ==========================================
# ROTA 3: Editar Produto (GET e POST)
# ==========================================
@app.route("/produtos/editar/<int:id>", methods=["GET", "POST"])
def editar_produto(id):
    conexao = conectar_banco()
    cursor = conexao.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        categoria = request.form["categoria"]
        preco = float(request.form["preco"])
        unidade = request.form["unidade"]
        disponivel = 1 if "disponivel" in request.form else 0
        vendedor_id = int(request.form["vendedor_id"])

        cursor.execute(
            """
            UPDATE produtos
            SET nome = ?, categoria = ?, preco = ?, unidade = ?, disponivel = ?, vendedor_id = ?
            WHERE id = ?
            """,
            (nome, categoria, preco, unidade, disponivel, vendedor_id, id),
        )
        conexao.commit()
        conexao.close()

        flash("Produto atualizado com sucesso!", "sucesso")
        return redirect(url_for("index"))

    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
    produto = cursor.fetchone()

    cursor.execute("SELECT * FROM vendedores ORDER BY nome")
    vendedores = cursor.fetchall()
    conexao.close()

    categorias = ["Frutas", "Legumes", "Hortaliças", "Laticínios e Caseiros", "Outros"]
    return render_template(
        "editar_produto.html",
        produto=produto,
        vendedores=vendedores,
        categorias=categorias,
    )


# ==========================================
# ROTA 4: Excluir Produto (POST)
# ==========================================
@app.route("/produtos/excluir/<int:id>", methods=["POST"])
def excluir_produto(id):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (id,))
    conexao.commit()
    conexao.close()

    flash("Produto removido da feira!", "aviso")
    return redirect(url_for("index"))


# ==========================================
# ROTA 5: Listar e Cadastrar Vendedores (GET e POST)
# ==========================================
@app.route("/vendedores", methods=["GET", "POST"])
def vendedores():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        barraca = request.form["barraca"]
        telefone = request.form["telefone"]
        dia_feira = request.form["dia_feira"]

        cursor.execute(
            "INSERT INTO vendedores (nome, barraca, telefone, dia_feira) VALUES (?, ?, ?, ?)",
            (nome, barraca, telefone, dia_feira),
        )
        conexao.commit()
        flash("Vendedor cadastrado com sucesso!", "sucesso")
        return redirect(url_for("vendedores"))

    cursor.execute("SELECT * FROM vendedores ORDER BY nome")
    lista_vendedores = cursor.fetchall()
    conexao.close()

    return render_template("vendedores.html", vendedores=lista_vendedores)


# ==========================================
# ROTA 6: Editar e Excluir Vendedor
# ==========================================
@app.route("/vendedores/editar/<int:id>", methods=["GET", "POST"])
def editar_vendedor(id):
    conexao = conectar_banco()
    cursor = conexao.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        barraca = request.form["barraca"]
        telefone = request.form["telefone"]
        dia_feira = request.form["dia_feira"]

        cursor.execute(
            """
            UPDATE vendedores
            SET nome = ?, barraca = ?, telefone = ?, dia_feira = ?
            WHERE id = ?
            """,
            (nome, barraca, telefone, dia_feira, id),
        )
        conexao.commit()
        conexao.close()

        flash("Dados do vendedor atualizados!", "sucesso")
        return redirect(url_for("vendedores"))

    cursor.execute("SELECT * FROM vendedores WHERE id = ?", (id,))
    vendedor = cursor.fetchone()
    conexao.close()

    return render_template("editar_vendedor.html", vendedor=vendedor)


@app.route("/vendedores/excluir/<int:id>", methods=["POST"])
def excluir_vendedor(id):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM vendedores WHERE id = ?", (id,))
    conexao.commit()
    conexao.close()

    flash("Vendedor e seus produtos foram removidos!", "aviso")
    return redirect(url_for("vendedores"))


# ==========================================
# ROTA 7: Página Sobre o Projeto
# ==========================================
@app.route("/sobre")
def sobre():
    return render_template("sobre.html")


# ==========================================
# ROTA 8: API em JSON (Retorna produtos + vendedor)
# ==========================================
@app.route("/api/produtos")
def api_produtos():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT produtos.id, produtos.nome, produtos.categoria,
               produtos.preco, produtos.unidade, produtos.disponivel,
               vendedores.nome AS vendedor, vendedores.barraca, vendedores.dia_feira
        FROM produtos
        INNER JOIN vendedores ON produtos.vendedor_id = vendedores.id
        ORDER BY produtos.id
        """
    )
    linhas = cursor.fetchall()
    conexao.close()

    # Converte os resultados do banco para uma lista de dicionários Python
    lista_json = []
    for item in linhas:
        lista_json.append(
            {
                "id": item["id"],
                "nome": item["nome"],
                "categoria": item["categoria"],
                "preco": item["preco"],
                "unidade": item["unidade"],
                "disponivel": bool(item["disponivel"]),
                "vendedor": item["vendedor"],
                "barraca": item["barraca"],
                "dia_feira": item["dia_feira"],
            }
        )

    return jsonify(
        {
            "projeto": "FeirinhaDigital",
            "total_produtos": len(lista_json),
            "produtos": lista_json,
        }
    )


# Inicializa o banco de dados ao carregar a aplicação
inicializar_banco()

if __name__ == "__main__":
    app.run(debug=True)
