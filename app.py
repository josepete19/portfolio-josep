from flask import Flask, render_template, request, redirect, url_for, jsonify, g
import sqlite3
import os
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'data', 'portfolio.db')
os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proyectos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descripcion TEXT,
                tecnologias TEXT,
                github_url TEXT,
                imagen_url TEXT,
                destacado INTEGER DEFAULT 0,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                contenido TEXT,
                tags TEXT,
                fecha_publicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute("SELECT COUNT(*) FROM proyectos")
        if cursor.fetchone()[0] == 0:
            proyectos = [
                ('Servidor GTA V', 'Servidor con más de 200 jugadores activos. Gestión de peticiones y administración de la comunidad.', 'Lua, JavaScript, MySQL, HTML, CSS, C#', 'https://github.com/tuusuario/gta-server', 'https://via.placeholder.com/800x400/2563eb/ffffff?text=GTA+V+Server', 1),
                ('App Cosmocaixa', 'Aplicación móvil para el Cosmocaixa que redujo el tiempo de chequeo de exposiciones. Integración QR, NFC y geolocalización.', 'Visual Basic, SQL, B4A', 'https://github.com/tuusuario/cosmocaixa-app', 'https://via.placeholder.com/800x400/7c3aed/ffffff?text=Cosmocaixa', 0),
                ('Formación COBOL', 'Programas básicos para gestión de archivos y procesamiento de datos en entornos mainframe.', 'COBOL, JCL', 'https://github.com/tuusuario/cobol-learning', 'https://via.placeholder.com/800x400/ec4899/ffffff?text=COBOL', 0)
            ]
            cursor.executemany(
                "INSERT INTO proyectos (titulo, descripcion, tecnologias, github_url, imagen_url, destacado) VALUES (?,?,?,?,?,?)",
                proyectos
            )
        
        cursor.execute("SELECT COUNT(*) FROM posts")
        if cursor.fetchone()[0] == 0:
            posts = [
                ('Certificando juegos de azar', 'Mi trabajo como Source Code Reviewer en BMM Testlabs. He certificado cientos de juegos para mercados internacionales con 0 incidencias en auditorías ENAC.', 'certificación, gaming, ENAC'),
                ('Aprendiendo COBOL', 'Formación autodidacta en COBOL para ampliar competencias en sistemas bancarios y mainframe.', 'COBOL, mainframe, legacy'),
                ('Servidor GTA V', 'Liderando un equipo de 5 programadores para administrar un servidor con más de 200 jugadores activos.', 'Lua, JavaScript, MySQL, FiveM')
            ]
            cursor.executemany(
                "INSERT INTO posts (titulo, contenido, tags) VALUES (?,?,?)",
                posts
            )
        
        db.commit()

@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE destacado = 1 LIMIT 3")
    proyectos_destacados = cursor.fetchall()
    cursor.execute("SELECT * FROM posts ORDER BY fecha_publicacion DESC LIMIT 3")
    posts_recientes = cursor.fetchall()
    return render_template('index.html', proyectos=proyectos_destacados, posts=posts_recientes)

@app.route('/blog')
def blog():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM posts ORDER BY fecha_publicacion DESC")
    posts = cursor.fetchall()
    return render_template('blog.html', posts=posts)

@app.route('/post/<int:id>')
def post(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = ?", (id,))
    post = cursor.fetchone()
    return render_template('post.html', post=post)

@app.route('/proyectos')
def proyectos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM proyectos ORDER BY destacado DESC, fecha_creacion DESC")
    proyectos = cursor.fetchall()
    return render_template('proyectos.html', proyectos=proyectos)

@app.route('/proyecto/<int:id>')
def proyecto(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto = cursor.fetchone()
    return render_template('proyecto.html', proyecto=proyecto)

@app.route('/api/proyectos')
def api_proyectos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, titulo, descripcion, tecnologias, github_url, imagen_url FROM proyectos")
    proyectos = cursor.fetchall()
    return jsonify([{
        'id': p[0],
        'titulo': p[1],
        'descripcion': p[2],
        'tecnologias': p[3].split(', '),
        'github_url': p[4],
        'imagen': p[5]
    } for p in proyectos])

@app.route('/api/posts')
def api_posts():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, titulo, contenido, tags, fecha_publicacion FROM posts")
    posts = cursor.fetchall()
    return jsonify([{
        'id': p[0],
        'titulo': p[1],
        'contenido': p[2],
        'tags': p[3].split(', '),
        'fecha': p[4]
    } for p in posts])

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        db = get_db()
        cursor = db.cursor()
        
        if tipo == 'post':
            titulo = request.form.get('titulo')
            contenido = request.form.get('contenido')
            tags = request.form.get('tags')
            cursor.execute("INSERT INTO posts (titulo, contenido, tags) VALUES (?,?,?)", 
                          (titulo, contenido, tags))
        elif tipo == 'proyecto':
            titulo = request.form.get('titulo')
            descripcion = request.form.get('descripcion')
            tecnologias = request.form.get('tecnologias')
            github_url = request.form.get('github_url')
            imagen_url = request.form.get('imagen_url')
            destacado = 1 if request.form.get('destacado') else 0
            cursor.execute("INSERT INTO proyectos (titulo, descripcion, tecnologias, github_url, imagen_url, destacado) VALUES (?,?,?,?,?,?)",
                          (titulo, descripcion, tecnologias, github_url, imagen_url, destacado))
        
        db.commit()
        return redirect(url_for('admin'))
    
    return render_template('admin.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False)