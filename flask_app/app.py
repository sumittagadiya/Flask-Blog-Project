from urllib.error import HTTPError
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, session, redirect, abort
import os
from werkzeug.utils import secure_filename
from datetime import date, datetime
import json
import math

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)

app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']

if params['local_server'] :
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Contacts(db.Model) :
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.DateTime, default = datetime.now())
    email = db.Column(db.String(20), nullable=False)

    def __repr__(self) -> str:
        return "Message from " + self.name + ' - ' + self.email

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    subheading = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.DateTime, default = datetime.now())
    img_file = db.Column(db.String(15), nullable=True)

    def __repr__(self) -> str:
        return self.title

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))

    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    
    if last == 1 :
        prev = "#"
        next = "#"

    elif page==1 :
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route("/dashboard",methods = ['GET', 'POST'])
def dashboard():
    if "email" in session and session['email']==params['email']:
        posts = Posts.query.all()
        return render_template("dashboard.html", params=params, posts=posts)

    if request.method == "POST" :
        email = request.form.get("email")
        password = request.form.get("password")
        if (email==params['email'] and password==params['password']):
            # set the session variable
            session['email']= email
            posts = Posts.query.all()
            return render_template("dashboard.html", params=params, posts=posts)
        else :
            abort(401, description="Unauthorized User !, Please Login with correct credentials...")
    else:
        return render_template("login.html", params=params)



@app.route("/edit/<string:sno>" , methods=['GET', 'POST'])
def edit(sno):
    if "email" in session and session['email']==params['email']:
        if request.method == "POST":
            
            title = request.form.get('title')
            subheading = request.form.get('subheading')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
            
            
            if sno=='0':
                post = Posts(title=title, subheading=subheading, slug=slug, content=content, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.subheading = subheading
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)
        
        post = Posts.query.filter_by(sno=sno).first()
        if not post :
            post = {'sno':sno,'title' : '','subheading' : '','slug':'','content':'','img_file':'','date':datetime.now()}

        return render_template('edit.html', params=params, post=post)

     # if user has not logged in then throw an error
    else :
        abort(401, description="Unauthorized User !, Please Login to edit your posts...")


@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if "email" in session and session['email']==params['email']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')
    else :
        abort(401, description="Unauthorized User !, Please Login to delete your posts...")

@app.route("/uploader" , methods=['GET', 'POST'])
def uploader():
    if "email" in session and session['email']==params['email']:
        if request.method=='POST':
            f = request.files['file1']
            if str(f.filename).endswith(('.jpg','.jpeg','.png')):
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
                return "Uploaded successfully!"
            else :
                return '<h1>Please Upload ".jpg", ".jpeg" or ".png" file </h1>'

@app.route('/logout')
def logout():
    session.pop('email')
    return redirect('/dashboard')


@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num = phone, msg = message, date= datetime.now(),email = email )
        db.session.add(entry)
        db.session.commit()
    return render_template('contact.html', params=params)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)



if __name__ == "__main__":
    app.run(debug=True)