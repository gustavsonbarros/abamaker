import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

# Configuração da aplicação
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cimas_maker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Inicializando o banco de dados
db = SQLAlchemy(app)

# Modelos
class Projeto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    data_submissao = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(50), nullable=False)

class Instituicao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(50), nullable=False)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(50), nullable=False, default="aluno")

# Função para criar tabelas e dados iniciais
def criar_tabelas_e_inserir_dados():
    db.create_all()  # Criação das tabelas
    # Criar usuário admin
    if not Usuario.query.filter_by(email='admin@example.com').first():
        admin = Usuario(
            nome="Administrador",
            email="admin@example.com",
            senha=generate_password_hash("admin123"),
            tipo="admin"
        )
        db.session.add(admin)
    
    # Criar usuário aluno
    if not Usuario.query.filter_by(email='aluno@example.com').first():
        aluno = Usuario(
            nome="Aluno",
            email="aluno@example.com",
            senha=generate_password_hash("aluno123"),
            tipo="aluno"
        )
        db.session.add(aluno)

    # Criar projetos
    if not Projeto.query.first():
        projetos = [
            Projeto(nome="Projeto de Pesquisa A", data_submissao="12/11/2024", status="Pendente"),
            Projeto(nome="Projeto de Pesquisa B", data_submissao="11/11/2024", status="Aprovado")
        ]
        db.session.add_all(projetos)

    # Criar instituições
    if not Instituicao.query.first():
        instituicoes = [
            Instituicao(nome="Instituição X", status="Aprovada"),
            Instituicao(nome="Instituição Y", status="Suspensa")
        ]
        db.session.add_all(instituicoes)

    db.session.commit()

@app.route('/editar_perfil')
def editar_perfil():
    return render_template('editar_perfil.html')

# Rotas e funcionalidades
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session or session.get('tipo') != 'admin':
        flash("Acesso negado. Faça login como admin.", "danger")
        return redirect(url_for('login'))
    projetos = Projeto.query.all()
    instituicoes = Instituicao.query.all()
    return render_template('admin_panel.html', projetos=projetos, instituicoes=instituicoes)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar-senha']

        # Verificar se as senhas coincidem
        if senha != confirmar_senha:
            flash("As senhas não coincidem. Tente novamente.", "danger")
            return redirect(url_for('register'))

        # Verificar se o email já está cadastrado
        if Usuario.query.filter_by(email=email).first():
            flash("Email já cadastrado. Tente outro.", "danger")
            return redirect(url_for('register'))

        # Criptografar a senha antes de salvar
        senha_hash = generate_password_hash(senha)

        usuario = Usuario(nome=nome, email=email, senha=senha_hash, tipo="aluno")
        db.session.add(usuario)
        db.session.commit()

        flash("Cadastro realizado com sucesso!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/aprovar_projeto/<int:id>', methods=['GET'])
def aprovar_projeto(id):
    projeto = Projeto.query.get_or_404(id)
    if projeto.status == 'Pendente':
        projeto.status = 'Aprovado'
        db.session.commit()
        flash(f"Projeto '{projeto.nome}' aprovado com sucesso!", "success")
    else:
        flash("Este projeto já foi aprovado ou rejeitado.", "warning")
    return redirect(url_for('admin_panel'))

@app.route('/rejeitar_projeto/<int:id>', methods=['GET'])
def rejeitar_projeto(id):
    projeto = Projeto.query.get_or_404(id)
    if projeto.status == 'Pendente':
        projeto.status = 'Rejeitado'
        db.session.commit()
        flash(f"Projeto '{projeto.nome}' rejeitado com sucesso!", "danger")
    else:
        flash("Este projeto já foi aprovado ou rejeitado.", "warning")
    return redirect(url_for('admin_panel'))

@app.route('/suspender_instituicao/<int:id>', methods=['GET', 'POST'])
def suspender_instituicao(id):
    # Lógica para suspender a instituição
    return redirect(url_for('admin_panel')) 

@app.route('/reativar_instituicao/<int:id>', methods=['GET', 'POST'])
def reativar_instituicao(id):
    # Lógica para reativar a instituição
    return redirect(url_for('admin_panel')) # ou outra ação apropriada

# Função auxiliar para verificar tipos de arquivo permitidos
def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Rota para upload de arquivos
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('Nenhum arquivo selecionado', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('Nenhum arquivo selecionado', 'danger')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('Arquivo enviado com sucesso', 'success')
        return redirect(url_for('index'))
    
    flash('Tipo de arquivo não permitido', 'danger')
    return redirect(request.url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.senha, senha):
            session['user_id'] = usuario.id
            session['tipo'] = usuario.tipo
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for('admin_panel' if usuario.tipo == 'admin' else 'aluno'))
        flash("Credenciais inválidas.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Você foi desconectado com sucesso.", "info")
    return redirect(url_for('login'))

# Lista para armazenar informações dos arquivos
arquivos = []

@app.route('/alunohtml', methods=['GET', 'POST'])
def alunohtml():
    if request.method == 'POST':
        # Verificar se o arquivo foi enviado
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # Salvar o arquivo com nome seguro
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Adicionar informações do arquivo à lista
            data_envio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            arquivos.append({'nome': filename, 'data': data_envio})
            return redirect(url_for('alunohtml'))

    return render_template('alunohtml.html', arquivos=arquivos)

@app.route('/aluno')
def aluno():
    if 'user_id' not in session or session.get('tipo') != 'aluno':
        flash("Acesso negado. Faça login como aluno.", "danger")
        return redirect(url_for('login'))
    return render_template('aluno.html')




# Inicializar tabelas
with app.app_context():
    criar_tabelas_e_inserir_dados()

if __name__ == '__main__':
    # Verificar e criar diretório de uploads
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
