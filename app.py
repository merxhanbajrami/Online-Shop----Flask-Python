from flask import Flask, render_template, url_for, request, flash, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename
import os
import re
import json
import jsonpickle
from json import JSONEncoder

import datetime

app = Flask(__name__)

# sessions
app.secret_key = "123nikola4tiasxtesla314"

# database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///onlineshop.db'
db = SQLAlchemy(app)
# bcrypt
bcrypt = Bcrypt(app)


# MODELS
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    surname = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    points = db.Column(db.Integer)
    telephone_number = db.Column(db.String(13), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    address = db.Column(db.String(100), nullable=False)

    def __init__(self, name, surname, username, password, points, telephone_number, email, address):
        self.name = name
        self.username = username
        self.surname = surname
        self.password = password
        self.points = points
        self.telephone_number = telephone_number
        self.email = email
        self.address = address

    def __repr__(self):
        return "<User %s>" % self.name


class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    info = db.Column(db.String(200))

    def __init__(self, name, brand, price, info):
        self.name = name
        self.brand = brand
        self.price = price
        self.info = info

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def __repr__(self):
        return "<Product %s> " % self.name


class Order(db.Model):
    order_number = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.Date, nullable=False)
    handling_cost = db.Column(db.Float, nullable=False)
    order_address = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

    def __init__(self, order_date, handling_cost, order_address, user_id):
        self.order_date = order_date
        self.handling_cost = handling_cost
        self.order_address = order_address
        self.user_id = user_id

    def __repr__(self):
        return "<Order %s> " % self.order_number


class order_product(db.Model):
    order_number = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)

    def __init__(self, order_number, product_id, quantity):
        self.order_number = order_number
        self.product_id = product_id
        self.quantity = quantity

    def __repr__(self):
        return "<order_product %s> " % self.order_number


@app.route("/")
def homepage():
    products = Product.query.all()
    my_products = [products[i] for i in range(4,8)]
    return render_template('homepage.html', products=my_products)


@app.route("/products")
def products():
    my_products = Product.query.all()
    return render_template('products.html', products=my_products)


@app.route("/products/<int:product_id>")
def product(product_id):
    pr = Product.query.get_or_404(product_id)
    return render_template('product.html', product=pr)


@app.route("/products/shoes")
def product_shoes():
    result = Product.query.filter(Product.info.endswith('40-44')).all()
    #return redirect(url_for('products', products=result))
    return render_template('products.html', products=result)

@app.route("/products/hoodies")
def product_hoodies():
    # result = Product.query.filter(Product.info.match(p)).all()
    result = Product.query.filter(Product.info.endswith(',Hoodie')).all()
    return render_template('products.html', products=result)


@app.route("/profile")
def profile():
    result_wish_list = session['wish_list']
    orders = Order.query.filter_by(user_id=session['user_id']).all()

    decode1 = []
    load1 = []
    for el in result_wish_list:
        decode1.append(jsonpickle.decode(el))

    for el in decode1:
        load1.append(json.loads(el))

    my_user = User.query.filter_by(username=session['username']).first()

    return render_template('profile.html', orders=orders, wish_list=load1, user=my_user)


@app.route("/profile/<int:user_id>")
def profile_info(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    if user_id != session['user_id']:
        return render_template('/errors/404.html')
    return render_template('/user/user.html', my_user=user)


@app.route("/order", methods=["POST"])
def order():
    # total = request.form['shuma']
    result_shopping_cart = session['shopping_cart']
    decode2 = []
    load2 = []

    for el in result_shopping_cart:
        decode2.append(jsonpickle.decode(el))

    for el in decode2:
        load2.append(json.loads(el))
    # order_date, handling_cost, order_address, user_id
    suma = 0
    for pr in load2:
        suma = suma + pr['price']

    username = session['username']
    my_user = User.query.filter_by(username=username).first()
    date_now = datetime.datetime.now()
    my_user.points=my_user.points+5;
    my_order = Order(date_now, suma, my_user.address, my_user.user_id)
    db.session.add(my_order)
    db.session.commit()

    for pr in load2:
        my_order_product = order_product(my_order.order_number, pr['product_id'], 1)
        db.session.add(my_order_product)
        db.session.commit()

    session['shopping_cart'] = []

    return redirect(url_for('profile'))

@app.route("/order/<int:order_number>/details")
def view_order(order_number):
    order_products = order_product.query.filter_by(order_number=order_number).all()
    products_list = []
    user=User.query.filter_by(username=session['username']).first()
    for o_id in order_products:
        product = Product.query.get_or_404(o_id.product_id)
        products_list.append(product)
    return render_template('order_products.html', order_products=products_list,user=user,order_number=order_number)


@app.route("/shop")
def shop():
    result_shopping_cart = session['shopping_cart']
    decode2 = []
    load2 = []

    for el in result_shopping_cart:
        decode2.append(jsonpickle.decode(el))

    for el in decode2:
        load2.append(json.loads(el))

    suma = 0
    for pr in load2:
        suma = suma + pr['price']

    return render_template('shop.html', shopping_cart=load2, total=suma)


@app.route("/remove_item_profile/<int:product_id>")
def remove_item_profile(product_id):
    result_shopping_cart = session['wish_list']
    decode2 = []
    load2 = []
    for el in result_shopping_cart:
        decode2.append(jsonpickle.decode(el))

    for el in decode2:
        load2.append(json.loads(el))

    suma = 0
    i = 0
    index = None
    for product in load2:
        if product['product_id'] == product_id:
            index = i
        else:
            suma = suma + product['price']
        i = i + 1
    lista = []
    load2.pop(index)
    for pr in load2:
        prJSON = jsonpickle.encode(pr, unpicklable=False)
        resultJSON = json.dumps(prJSON, indent=4)
        lista.append(resultJSON)

    session['wish_list'] = lista

    return redirect(url_for('profile'))


@app.route("/remove_item/<int:product_id>")
def remove(product_id):
    result_shopping_cart = session['shopping_cart']
    decode2 = []
    load2 = []
    for el in result_shopping_cart:
        decode2.append(jsonpickle.decode(el))

    for el in decode2:
        load2.append(json.loads(el))

    suma = 0
    i = 0
    index = 0
    for product in load2:
        if product['product_id'] == product_id:
            index = i
        else:
            suma = suma + product['price']
        i = i + 1
    lista = []

    load2.pop(index)
    for pr in load2:
        prJSON = jsonpickle.encode(pr, unpicklable=False)
        resultJSON = json.dumps(prJSON, indent=4)
        lista.append(resultJSON)

    session['shopping_cart'] = lista

    return redirect(url_for('shop'))


@app.route("/add_to_cart_profile/<int:product_id>")
def add_to_cart_profile(product_id):
    pr = Product.query.get_or_404(product_id)
    prJSON = jsonpickle.encode(pr, unpicklable=False)
    resultJSON = json.dumps(prJSON, indent=4)
    lista = session['shopping_cart']
    lista.append(resultJSON)
    session['shopping_cart'] = lista
    return redirect(url_for('profile'))


@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    pr = Product.query.get_or_404(product_id)
    prJSON = jsonpickle.encode(pr, unpicklable=False)
    resultJSON = json.dumps(prJSON, indent=4)
    lista = session['shopping_cart']
    lista.append(resultJSON)
    session['shopping_cart'] = lista
    return redirect(url_for('products'))


@app.route("/add_to_wish_list/<int:product_id>")
def add_to_wish_list(product_id):
    pr = Product.query.get_or_404(product_id)
    prJSON = jsonpickle.encode(pr, unpicklable=False)
    resultJSON = json.dumps(prJSON, indent=4)
    lista = session['wish_list']
    lista.append(resultJSON)
    session['wish_list'] = lista
    # rezultat=json.loads(resultJSON)
    return redirect(url_for('products'))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if not_empty([username, password]):
            if check_user(username):
                my_user = User.query.filter_by(username=username).first()
                if bcrypt.check_password_hash(my_user.password, password):
                    session['is_logged_in'] = True
                    session['username'] = my_user.username
                    session['email'] = my_user.email
                    session['wish_list'] = []
                    session['shopping_cart'] = []
                    session['user_id']=my_user.user_id
                    return redirect(url_for("profile"))
                else:
                    flash('Password is incorrect!')
            else:
                flash('This username does not exist')
        else:
            flash('Please enter your credentials!')
        return redirect(url_for('login'))
    else:
        try:
            if session['is_logged_in'] == True:
                my_user = User.query.filter_by(username=session['username']).first()
                return redirect(url_for('profile'))
        except KeyError:
            session['is_logged_in'] = False
            return redirect(url_for('login'))
        return render_template('/auth/login.html')


@app.route("/logout")
def logout():
    session['is_logged_in'] = False
    session['username'] = ""
    session['email'] = ""
    session['wish_list'] = []
    session['shopping_cart'] = []
    session['user_id'] = None
    return redirect(url_for('homepage'))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form['name']
        surname = request.form['surname']
        date = request.form['date_of_birth']
        email = request.form['email']
        telephone = request.form['telephone']
        username = request.form['username']
        password = request.form['password']
        address = request.form['address']
        confirm_password = request.form['confirm_password']
        if not_empty([name, surname, date, email, telephone, username, password, confirm_password]):
            if validate_mail(email):
                if not check_mail(email):
                    if not check_user(username):
                        if check_password(password, confirm_password):
                            if not check_phone(telephone):
                                password_hash = bcrypt.generate_password_hash(password)
                                new_user = User(name, surname, username, password_hash, 0, telephone, email,address)
                                db.session.add(new_user)
                                db.session.commit()
                                session['is_logged_in'] = True
                                session['username'] = new_user.username
                                session['email'] = new_user.email
                                session['wish_list'] = []
                                session['shopping_cart'] = []
                                session['user_id'] = new_user.user_id
                                return redirect(url_for("profile", user=new_user))
                            else:
                                flash("Please enter a valid telephone number!")
                        else:
                            flash("Password don't match!")
                    else:
                        flash("This username already exists")
                else:
                    flash("This mail is already registered!")
            else:
                flash("Please enter a valid mail!")
        else:
            flash("Please fill all fields!")
        return redirect(url_for('register'))
    else:
        if session['is_logged_in']:
            return redirect(url_for('profile'))
        return render_template('/auth/register.html')


@app.route("/brands")
def brands():
    return "Brands here..."


def validate_mail(mail):
    return re.search("[\w\.\_\-]+\@[\w\-]+\.[a-z]{2,5}", mail) != None


def not_empty(args):
    for arg in args:
        if len(arg) == 0:
            return False
    return True


def check_password(password1, password2):
    if password1 == password2:
        return True
    else:
        return False


def check_mail(mail):
    user = User.query.filter_by(email=mail).first()
    if user:
        return True
    else:
        return False


def check_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return True
    else:
        return False


def check_phone(number):
    return any(char.isalpha() for char in number)


if __name__ == "__main__":
    app.run(debug=True)
