import os, json
from datetime import datetime
from flask import Flask, render_template, request, redirect, session
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Sequence
from werkzeug.utils import secure_filename

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'admin'
app.config['UPLOAD_FOLDER'] = params['folder_path']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['username'],
    MAIL_PASSWORD = params['password']
)

mail = Mail(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://flask_user:examplePwd@localhost/exampleFlask'
db = SQLAlchemy(app) 



class Contact(db.Model):
    id = db.Column(db.Integer, Sequence('contact_id_seq'), primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable = False)
    phone_num = db.Column(db.String(12), nullable = False)
    msg = db.Column(db.String(120), nullable = False)
    date = db.Column(db.String(12), nullable = False)
    email = db.Column(db.String(50), nullable = True)

class Post(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(80), nullable = False)
    slug = db.Column(db.String(50), nullable = False)
    content = db.Column(db.String(500), nullable = False)
    date = db.Column(db.String(20), nullable = False)
    image = db.Column(db.String(50), nullable = False)
    author = db.Column(db.String(50), default = "Rahul Prajapati")



@app.route('/')
def home():
    posts = Post.query.all()[0:5]
    return render_template('index.html', params = params, posts = posts)

@app.route('/about')
def about():
    return render_template('about.html', params=params)

@app.route('/contact', methods = ['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']

        entry = Contact(name=name, phone_num = phone, email = email, date = datetime.now(), msg = message)
        db.session.add(entry)
        db.session.commit()

        mail.send_message(
            'Received mail from' + name,
            sender = email,
            # recipients = [params['username']],
            recipients = [email],
            body = message + "\n" + phone
        )

        return redirect('contact')

    return render_template('contact.html', params=params)

@app.route('/post/<string:post_slug>', methods = ['GET'])
def post_info(post_slug):
    post = Post.query.filter_by(slug = post_slug).first()
    return render_template('post.html', params=params, post = post)

@app.route('/dashboard', methods = ['GET', 'POST'])
def dashboard():
    posts = Post.query.all()

    if 'user' in session and session['user'] == params['admin_username']:
        return render_template('dashboard.html', params = params, posts = posts)


    if request.method == 'POST':
        username = request.form['uname']
        password = request.form['pass']

        if username == params['admin_username'] and password == params['admin_password']:
            session['user'] = username

            return render_template('dashboard.html', params = params, posts = posts)
    
    return render_template('login.html', params = params)

@app.route('/edit/<string:sno>', methods = ['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_username']:
        if request.method == 'POST':
            title = request.form['title']
            slug = request.form['slug']
            content = request.form['content']
            image = request.form['image']
            author = request.form['author']

            if sno == '0':
                post = Post(title = title, slug = slug, content = content, image = image, author = author, date = datetime.now())
                db.session.add(post)
                db.session.commit()

            else:
                post_info = Post.query.filter_by(sno=sno).first()
                post_info.title = request.form['title']
                post_info.slug = request.form['slug']
                post_info.content = request.form['content']
                post_info.image = request.form['image']
                post_info.author = request.form['author']

                db.session.commit()

                return redirect('/edit/' + sno)
            
        post = Post.query.filter_by(sno=sno).first()

        return render_template('edit.html', params = params, post = post, sno=sno)
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route('/uploader', methods = ['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_username']:
        if request.method == 'POST':
            file = request.files['file']
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
            return "Uploaded Successfully"
        return "Please upload file"
    else:
        return redirect('/')
    
@app.route('/delete/<int:sno>')
def delete(sno):
    if 'user' in session and session['user'] == params['admin_username']:
        post = Post.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return "Delete Successfully"

app.run(debug=True)