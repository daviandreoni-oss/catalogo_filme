import sqlite3

DB_NAME = 'filmes.db'

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome (como RealDictCursor)
    return conn

def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS filmes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            genero TEXT,
            ano INTEGER,
            url_capa TEXT
        )
    ''')

    conn.commit()
    conn.close()
