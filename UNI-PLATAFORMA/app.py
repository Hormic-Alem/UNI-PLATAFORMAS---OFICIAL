from flask import Flask, render_template, redirect, url_for, request, session
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)
app.secret_key = 'mysecretkey'  # Cambia esto en producción
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Bootstrap(app)
db = SQLAlchemy(app)

# Modelo de Usuarios
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Modelo de Palabras
class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    translation = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(50), nullable=False)
    topic = db.Column(db.String(100), nullable=False)

# Modelo de Preguntas
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200), nullable=False)  # La pregunta
    answer = db.Column(db.String(200), nullable=False)  # La respuesta correcta
    category = db.Column(db.String(100), nullable=False)  # Categoría de la pregunta
    option1 = db.Column(db.String(200), nullable=False)  # Opción 1
    option2 = db.Column(db.String(200), nullable=False)  # Opción 2
    option3 = db.Column(db.String(200), nullable=False)  # Opción 3

# Crear la base de datos
with app.app_context():
    db.create_all()

def add_default_admin():
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password="admin123", is_admin=True)
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username, password=password).first()
    if user:
        session['username'] = username
        session['is_admin'] = user.is_admin
        return redirect(url_for('home'))
    else:
        return render_template('login.html', error="Usuario o contraseña incorrectos.")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not User.query.filter_by(username=username).first():
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            session['is_admin'] = new_user.is_admin
            return redirect(url_for('home'))
        else:
            return "Usuario ya registrado."

    return render_template('register.html')

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('index'))

    return render_template('home.html')

@app.route('/quick_trainer', methods=['GET', 'POST'])
def quick_trainer():
    if 'username' not in session:
        return redirect(url_for('index'))

    all_questions = Question.query.all()

    if not all_questions:
        return render_template('quick_trainer.html', question=None, feedback="No hay preguntas disponibles. Agrega algunas preguntas primero.", options=[])

    random_question = random.choice(all_questions)

    feedback = None
    if request.method == 'POST':
        user_answer = request.form.get('user_answer')
        correct_answer = random_question.answer

        if user_answer and user_answer.strip().lower() == correct_answer.strip().lower():
            feedback = "¡Correcto! 🎉"
        else:
            feedback = f"Incorrecto. La respuesta correcta es: {correct_answer}"

    options = [random_question.option1, random_question.option2, random_question.option3]

    return render_template('quick_trainer.html',
                           question=random_question.question,
                           options=options,
                           feedback=feedback)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/lessons')
def lessons():
    if 'username' not in session:
        return redirect(url_for('index'))

    level_filter = request.args.get('level')
    category_filter = request.args.get('category')

    query = Word.query

    if level_filter:
        query = query.filter_by(level=level_filter)

    if category_filter:
        query = query.filter_by(topic=category_filter)

    words = query.all()

    categories = db.session.query(Word.topic).distinct().all()

    return render_template('lessons.html', words=words, level=level_filter, categories=categories)

@app.route('/add_word', methods=['GET', 'POST'])
def add_word():
    if 'username' not in session or not session['is_admin']:
        return "Acceso denegado. No tienes permisos para agregar palabras."

    if request.method == 'POST':
        word = request.form['word']
        translation = request.form['translation']
        level = request.form['level']
        topic = request.form['topic']

        new_word = Word(word=word, translation=translation, level=level, topic=topic)
        db.session.add(new_word)
        db.session.commit()

    words = Word.query.all()

    return render_template('add_word.html', words=words)

@app.route('/delete_word/<int:id>', methods=['GET'])
def delete_word(id):
    if 'username' not in session or not session['is_admin']:
        return "Acceso denegado. No tienes permisos para eliminar palabras."

    word_to_delete = Word.query.get(id)
    if word_to_delete:
        db.session.delete(word_to_delete)
        db.session.commit()

    return redirect(url_for('add_word'))

@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if 'username' not in session or not session['is_admin']:
        return "Acceso denegado. No tienes permisos para agregar preguntas."

    if request.method == 'POST':
        question = request.form['question']
        answer = request.form['answer']
        category = request.form['category']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']

        new_question = Question(
            question=question,
            answer=answer,
            category=category,
            option1=option1,
            option2=option2,
            option3=option3
        )
        db.session.add(new_question)
        db.session.commit()

    questions = Question.query.all()

    return render_template('add_question.html', questions=questions)

@app.route('/delete_question/<int:id>', methods=['GET'])
def delete_question(id):
    if 'username' not in session or not session['is_admin']:
        return "Acceso denegado. No tienes permisos para eliminar preguntas."

    question_to_delete = Question.query.get(id)
    if question_to_delete:
        db.session.delete(question_to_delete)
        db.session.commit()

    return redirect(url_for('add_question'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'username' not in session or not session.get('is_admin'):
        return "Acceso denegado. Solo los administradores pueden acceder a esta página.", 403

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = 'is_admin' in request.form

        if not User.query.filter_by(username=username).first():
            new_user = User(username=username, password=password, is_admin=is_admin)
            db.session.add(new_user)
            db.session.commit()
        else:
            return "El usuario ya existe."

    users = User.query.all()
    return render_template('admin.html', users=users)

if __name__ == '__main__':
    with app.app_context():
        add_default_admin()
    app.run(debug=True)
