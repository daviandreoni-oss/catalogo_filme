import os
import uuid
from flask import Flask, request, jsonify, render_template, redirect, url_for
from database import get_connection, create_table

app = Flask(__name__)

# --- CONFIGURAÇÕES DE UPLOAD ---
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# ------------------------------

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "API de catálogo de filmes"}), 200

@app.route('/ping', methods=['GET'])
def ping():
    # FIX: não fecha a conexão antes de usá-la na resposta
    try:
        conn = get_connection()
        conn.close()
        return jsonify({"message": "pong! API Rodando!", "db": "SQLite conectado com sucesso!"}), 200
    except Exception as ex:
        return jsonify({"message": "Erro ao conectar ao banco", "erro": str(ex)}), 500

@app.route('/filmes', methods=['GET'])
def listar_filmes():
    sql = "SELECT * FROM filmes"
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        filmes = cursor.fetchall()
        conn.close()
        return render_template("index.html", filmes=filmes)
    except Exception as ex:
        print('erro: ', str(ex))
        return render_template("erro.html", erro="Erro ao listar filmes")

@app.route("/novo_filme", methods=["GET", "POST"])
def novo_filme():
    if request.method == "POST":
        try:
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]
            file = request.files.get("url_capa")

            if file and allowed_file(file.filename):
                extensao = file.filename.rsplit('.', 1)[1].lower()
                nome_hash = f"{uuid.uuid4().hex}.{extensao}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_hash))
                url_capa = f"uploads/{nome_hash}"

                sql = "INSERT INTO filmes (titulo, genero, ano, url_capa) VALUES (?, ?, ?, ?)"
                params = [titulo, genero, ano, url_capa]

                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()  # FIX: commit antes de fechar
                conn.close()
                return redirect(url_for("listar_filmes"))

            return render_template("erro.html", erro="Arquivo inválido ou não enviado")
        except Exception as ex:
            print('erro: ', str(ex))
            return render_template("erro.html", erro="Erro ao cadastrar filme")

    return render_template("novo_filme.html")

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar_filme(id):
    # FIX: conexão aberta dentro de cada bloco separado, sem vazamento
    try:
        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]
            file = request.files.get("url_capa")

            conn = get_connection()
            cursor = conn.cursor()

            # Busca a imagem atual para manter caso não envie nova
            cursor.execute("SELECT url_capa FROM filmes WHERE id = ?", [id])
            filme_atual = cursor.fetchone()

            url_capa = filme_atual['url_capa']  # Mantém a antiga por padrão

            if file and allowed_file(file.filename):
                extensao = file.filename.rsplit('.', 1)[1].lower()
                nome_hash = f"{uuid.uuid4().hex}.{extensao}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_hash))
                url_capa = f"uploads/{nome_hash}"

            sql_update = "UPDATE filmes SET titulo = ?, genero = ?, ano = ?, url_capa = ? WHERE id = ?"
            cursor.execute(sql_update, [titulo, genero, ano, url_capa, id])
            conn.commit()
            conn.close()
            return redirect(url_for("listar_filmes"))

        # GET: carrega página de edição
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM filmes WHERE id = ?", [id])
        filme = cursor.fetchone()
        conn.close()

        if filme is None:
            return redirect(url_for("listar_filmes"))
        return render_template("editar_filme.html", filme=filme)

    except Exception as ex:
        print('erro: ', str(ex))
        return render_template("erro.html", erro="Erro ao editar filme")

@app.route("/deletar/<int:id>", methods=["POST"])
def deletar_filme(id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM filmes WHERE id = ?", [id])
        conn.commit()
        conn.close()
        return redirect(url_for("listar_filmes"))
    except Exception as ex:
        print('erro: ', str(ex))
        return render_template("erro.html", erro="Erro ao deletar filme")

# Cria a tabela ao iniciar a aplicação
create_table()

if __name__ == '__main__':
    app.run(debug=True)
