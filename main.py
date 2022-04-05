import math
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail


with open('config.json','r') as c:
    params = json.load(c)['params']

local_server=params['local_server']

app = Flask(__name__)
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL= True,
    MAIL_USERNAME= params['gmail_user'],
    MAIL_PASSWORD = params['gmail_pwd']
)
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.secret_key = 'super secret key'
mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    phone_num = db.Column(db.String(12), unique=False, nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=False, nullable=False)
    slug = db.Column(db.String(21), unique=False, nullable=False)
    content = db.Column(db.String(120), unique=False, nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(20), nullable=True)
    tagline = db.Column(db.String(50), nullable=True)


@app.route('/')
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page=request.args.get('page')
    if not str(page).isnumeric():
        page=1
    else:
        page= int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page)*int(params['no_of_posts'])]
    #Pagination Logic
    #First
    if page==1:
        prev='#'
        next= "/?page="+ str(page+1)
    #Middle
    elif page==last:
        prev = "/?page=" + str(page-1)
        next = "#"
    #Last
    else:
        prev="/?page=" + str(page-1)
        next="/?page="+ str(page+1)
    return render_template('index.html',params=params, posts=posts, prev=prev,next=next,page=page)


@app.route('/about')
def about():
    return render_template('about.html', params=params)


@app.route('/login')
def login():
    return render_template('login.html', params=params)


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route('/delete/<string:sno>',methods=['POST','GET'])
def delete(sno):
    if 'user' in session and session['user']==params['admin_user']:
        post= Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    print(session)
    if 'user' in session and session['user']==params['admin_user']:
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params, posts=posts)
    if request.method=='POST':
        username = request.form.get('uname')
        pwd = request.form.get('pass')
        if username==params['admin_user'] and pwd==params['admin_pwd']:
            session['user']=username
            posts = Posts.query.all()
            print(posts)
            return render_template('dashboard.html',params=params, posts=posts)
    return render_template('login.html', params=params)


@app.route('/edit/<string:sno>', methods=['GET','POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method=='POST':
            title= request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            if sno=='0':
                post=Posts(title=title,tagline=tagline,slug=slug,content=content,img_file=img_file,date=datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.tagline= tagline
                post.slug=slug
                post.content = content
                post.img_file = img_file
                post.date = datetime.now()
                db.session.commit()
                return redirect('/edit/' + sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,post=post)


@app.route('/uploader', methods=['GET','POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method=='POST':
            f= request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Successfully"


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method in ['POST', 'post']:
        '''Add contact to database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone_num = request.form.get('phone')
        msg = request.form.get('msg')

        entry = Contacts(name=name, email=email, phone_num=phone_num, date=datetime.now(), msg=msg)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New contact created by '+name,sender=email,recipients=[params['gmail_user']],
                          body = msg + '\n' + phone_num )

    return render_template('contact.html', params=params)


@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',post=post, params=params)


app.run(debug=True)
