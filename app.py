from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOADED_FILES_DEST'] = os.getcwd() + '//static//images'
db = SQLAlchemy(app)
login_manager = LoginManager(app)

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return self.name

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    desc = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Available')
    seller_name = db.Column(db.String(20), nullable=False)
    seller_email = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return self.name

@login_manager.user_loader
def laod_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        dob = datetime.strptime(request.form['dob'], '%Y-%m-%d')
        email = request.form['email']
        password = request.form['password']
        bcrypt = Bcrypt()
        hashed_pass = bcrypt.generate_password_hash(password).decode('utf-8')
        user = Users(name=name, dob=dob, email=email, password=hashed_pass)
        db.session.add(user)
        db.session.commit()
        return redirect('/')
    else:
        return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    user = Users.query.filter_by(email=email).first()
    bcrypt = Bcrypt()
    if user and bcrypt.check_password_hash(user.password,password):
        login_user(user)
        return redirect('/home')
    else:
        return redirect('/')

@app.route('/home')
def home():
    if current_user.is_authenticated:
        return render_template('/home.html')
    else:
        return redirect('/')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

@app.route('/profile')
def profile():
    if current_user.is_authenticated:
        products = Products.query.filter_by(seller_email=current_user.email).order_by(desc(Products.id)).all()
        return render_template('/profile.html', products=products)
    else:
        return redirect('/')

@app.route('/sell')
def sell():
    if current_user.is_authenticated:
        return render_template('/sell.html')
    else:
        return redirect('/')

@app.route('/add_product', methods=['POST'])
def addproduct():
    pname = request.form['name']
    pdesc = request.form['desc']
    pimage = request.files['image']
    pprice = request.form['price']
    pimage.save(os.path.join(app.config['UPLOADED_FILES_DEST'], pimage.filename))
    product = Products(name=pname, desc=pdesc, image=pimage.filename, price=pprice, seller_name=current_user.name, seller_email=current_user.email)
    db.session.add(product)
    db.session.commit()
    return redirect('/home')

@app.route('/marksold/<int:id>')
def marksold(id):
    if current_user.is_authenticated:
        product = Products.query.get(id)
        product.status = 'Sold'
        db.session.commit()
        return redirect('/profile')
    else:
        return redirect('/')

@app.route('/search')
def search():
    if current_user.is_authenticated:
        search = request.args.get('search')
        search = search.capitalize()
        products = Products.query.filter_by(status='Available').filter(Products.name.contains(search)).filter(Products.seller_email != current_user.email).all()
        return render_template('search.html', products=products)
    else:
        return redirect('/')

if __name__=='__main__':
    app.run(debug=True)