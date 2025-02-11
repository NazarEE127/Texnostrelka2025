from flask import Flask, render_template, request, redirect, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
from instance.DataBase import *
import requests


ALLOWED_EXTENSIONS = {'png', 'jpg', 'dng', 'raw', 'ARW', 'mp4', 'avi', 'mov'}
PHOTO_FORMAT = {'png', 'jpg', 'dng', 'raw', 'ARW'}
VIDEO_FORMAT = {'mp4', 'avi', 'mov'}


app = Flask(__name__)
app.secret_key = '79d77d1e7f9348c59a384d4376a9e53f'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['UPLOAD_FOLDER'] = 'static/img'
db.init_app(app)
manager = LoginManager(app)


@manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/profile')
@login_required
def profile():
    user = Users.query.get(current_user.id)
    routes = Routes.query.filter_by(user_id=current_user.id).all()
    return render_template("profile.html", user=user, routes=routes)


"""РЕГИСТРАЦИЯ, ВХОД И ВЫХОД"""


@app.route('/sign-up', methods=["POST", "GET"])
def sign_up():
    if request.method == "GET":
        return render_template("sign-up.html")
    email = request.form.get('email')
    password = request.form.get('password')
    password2 = request.form.get('password2')
    username = request.form.get('username')
    user_email = Users.query.filter_by(email=email).first()
    user_username = Users.query.filter_by(username=username).first()
    file = request.files['file']
    file.save(os.path.join('static/img', file.filename))
    if user_email is not None:
        flash('Email пользователя занят!')
        return render_template("sign-up.html")

    if user_username is not None:
        flash('Имя пользователя занято!')
        return render_template("sign-up.html")

    if password != password2:
        flash("Пароли не совпадают!")
        return render_template("sign-up.html")
    try:
        hash_pwd = generate_password_hash(password)
        new_user = Users(email=email, password=hash_pwd, ava=file.filename, username=username)
        db.session.add(new_user)
        db.session.commit()
        return redirect("/")

    except Exception as e:
        flash("Возникла ошибка при регистрации")
        return render_template("sign-up.html")


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = Users.query.filter_by(email=email).first()
        if user is not None:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect('/')
            else:
                flash('Неверный логин или пароль')
        else:
            flash('Такого пользователя не существует')
    return render_template("login.html")


@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")


@app.route("/add_route", methods=['GET', 'POST'])
@login_required
def add_route():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        public = 1 if request.form.get('public') else 0
        private = 1 if request.form.get('private') else 0
        status = 0
        if public == 1:
            status = 1
        elif private == 1:
            status = 0
        route = Routes(title=title, description=description, status=status, user_id=current_user.id, rating=0)
        db.session.add(route)
        db.session.commit()
        flash("Маршрут успешно создан!")
        return redirect("/")
    return render_template('add_route.html')


@app.route("/evaluate_route/<int:id>", methods=['GET', 'POST'])
@login_required
def evaluate_route(id):
    if request.method == 'POST':
        text = request.form.get('comment')
        mark = request.form.get('mark')
        comment = Comments(route_id=id, text=text, user_id=current_user.id)
        route = Routes.query.filter(Routes.id == id).first()
        try:
            cnt_mrks = route.count_marks
            route.count_marks += 1
            route.rating = ((float(route.rating)*int(cnt_mrks))+float(mark))/(cnt_mrks+1)
            db.session.add(comment)
            db.session.commit()
            flash("Оценка успешно сохранена!")
            return redirect("/")
        except Exception as e:
            flash("Возникла ошибка при оценки маршрута")
    return render_template('evaluate_route.html')


@app.route('/all_routes')
def all_routes():
    routes = Routes.query.all()
    return render_template("all_routes.html", routes=routes)


@app.route('/route/<int:id>')
def route(id):
    route = Routes.query.filter(Routes.id == id).first()
    comments = Comments.query.filter(Comments.route_id == id).all()
    user = Users.query.filter(Users.id == route.user_id).first()
    return render_template("route.html", user=user, route=route, comments=comments)


@app.route('/delete_route/<int:id>')
@login_required
def del_route(id):
    route = Routes.query.filter_by(id=id).first()
    if current_user.id == route.user_id:
        try:
            db.session.delete(route)
            db.session.commit()
            flash('Маршрут удалён!')
            return redirect("/")
        except Exception as e:
            flash('Ошибка при удалении')
            return redirect("/")
    else:
        flash('Нет доступа')
        return redirect("/")


@app.route('/map', methods=['GET', 'POST'])
def map():
    if request.method == 'POST':
        data = request.json
        points = data['points']
        print(data)
        # Запрос к Яндекс Геокодеру для получения координат
        geocode_url = "https://geocode-maps.yandex.ru/1.x/"
        api_key = "fc583f53-ce4b-49a8-9926-2cc9b2ac3082"

        coordinates = []
        for point in points:
            str_point = f"{point[1]},{point[0]}"
            response = requests.get(geocode_url, params={'apikey': api_key, 'geocode': str_point, 'format': 'json'})
            data = response.json()
            print(data)
            coords = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos'].split()
            coordinates.append([float(coords[1]), float(coords[0])])  # [latitude, longitude]
        print(coordinates)
        return jsonify(coordinates)

    return render_template("map.html")


@app.route('/edit_route/<int:id>', methods=["POST", "GET"])
def edit_route(id):
    route = Routes.query.filter_by(id=id).first()
    if current_user.is_authenticated and (current_user.id == route.user_id or current_user.admin == 1):
        if request.method == "GET":
            return render_template("edit_route.html", route=route)
        if request.method == "POST":
            title = request.form.get('title')
            description = request.form.get('description')
            public = 1 if request.form.get('public') else 0
            private = 1 if request.form.get('private') else 0
            if public == 1:
                status = 1
            elif private == 1:
                status = 0
            else:
                status = 0
            try:
                route.title = title
                route.description = description
                route.status = status
                db.session.commit()
                flash("Маршрута изменён")
                return redirect(f'/route/{id}')
            except:
                flash("Возникла ошибка при изменении маршрута")
                return redirect('/all_routes')
    else:
        flash('Нет доступа')
        return redirect('/')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
