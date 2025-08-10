from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from mcstatus import JavaServer
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Замени на случайный ключ
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///minecraft_monitor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

# Модель сервера
class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(150))
    port = db.Column(db.Integer, default=25565)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    added_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Создание БД
with app.app_context():
    db.create_all()

# Главная страница: список серверов с мониторингом
@app.route('/')
def index():
    servers = Server.query.all()
    monitored_servers = []
    for server in servers:
        try:
            mc_server = JavaServer.lookup(f"{server.ip}:{server.port}")
            status = mc_server.status()
            monitored_servers.append({
                'ip': server.ip,
                'port': server.port,
                'online': True,
                'players': status.players.online,
                'max_players': status.players.max,
                'version': status.version.name,
                'added_by': User.query.get(server.added_by).username if server.added_by else 'Аноним'
            })
        except Exception:
            monitored_servers.append({
                'ip': server.ip,
                'port': server.port,
                'online': False,
                'added_by': User.query.get(server.added_by).username if server.added_by else 'Аноним'
            })
    return render_template('index.html', servers=monitored_servers, user=current_user)

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Пользователь уже существует!')
            return redirect(url_for('register'))
        new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация успешна! Войдите.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Логин
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверные данные!')
    return render_template('login.html')

# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Добавление сервера
@app.route('/add_server', methods=['GET', 'POST'])
@login_required
def add_server():
    if request.method == 'POST':
        ip = request.form.get('ip')
        port = request.form.get('port') or 25565
        new_server = Server(ip=ip, port=port, added_by=current_user.id)
        db.session.add(new_server)
        db.session.commit()
        flash('Сервер добавлен!')
        return redirect(url_for('index'))
    return render_template('add_server.html')

if __name__ == '__main__':
    app.run(debug=True)
