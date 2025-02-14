from flask import Flask, render_template, request, redirect, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
import sys
from instance.DataBase import *
import requests
import ast
import gpxpy
import simplekml
from io import BytesIO
from PIL import Image
import urllib.parse

# import re


ALLOWED_EXTENSIONS = {'png', 'jpg', 'dng', 'raw', 'ARW', 'mp4', 'avi', 'mov'}
PHOTO_FORMAT = {'png', 'jpg', 'dng', 'raw', 'ARW'}
VIDEO_FORMAT = {'mp4', 'avi', 'mov'}

app = Flask(__name__)
app.secret_key = '79d77d1e7f9348c59a384d4376a9e53f'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['UPLOAD_FOLDER'] = 'static/img'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
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
        print("POST")
        title = request.form.get('title')
        description = request.form.get('description')
        public = 1 if request.form.get('public') else 0
        private = 1 if request.form.get('private') else 0
        status = 0
        if public == 1:
            status = 1
        elif private == 1:
            status = 0
        files = request.files.getlist('files')
        route_coords = ast.literal_eval(request.form.get('routeCoordinates'))
        coords_text = ""
        for p in route_coords:
            coords_text += f"{p[0]};{p[1]}@"
        coords_text = coords_text[:-1]

        route = Routes(title=title, description=description, status=status,
                       user_id=current_user.id, rating=0, route_coords=coords_text, check_admin=0)
        # отправить на почту админу, что созадли новый маршрут, нужно проверить его
        db.session.add(route)
        db.session.commit()
        db.session.refresh(route)
        r = Routes.query.filter_by(id=route.id).first()
        text = ''
        for file in files:
            file.save(os.path.join('static/img', file.filename))
            photo = Photos(route_id=route.id, name=file.filename)
            db.session.add(photo)
            db.session.commit()
            db.session.refresh(photo)
            text += str(photo.id) + "|"
        r.photos_id = text[:-1]
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
        comment = Comments(route_id=id, text=text, user_id=current_user.id, check_admin=0)
        # отправить на почту админу, что созадли новый комментарий, нужно проверить его
        route = Routes.query.filter(Routes.id == id).first()
        try:
            cnt_mrks = route.count_marks
            route.count_marks += 1
            route.rating = ((float(route.rating) * int(cnt_mrks)) + float(mark)) / (cnt_mrks + 1)
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
    photos = {}
    for r in routes:
        ps = Photos.query.filter(Photos.route_id == r.id).all()
        for i in range(len(ps)):
            if r.id in photos.keys():
                photos[r.id].append(ps[i].name)
            else:
                photos[r.id] = [ps[i].name]
    return render_template("all_routes.html", routes=routes, photos=photos)


@app.route('/route/<int:id>', methods=['GET', 'POST'])
def route(id):
    route = Routes.query.filter(Routes.id == id).first()
    comments = Comments.query.filter(Comments.route_id == id).all()
    user = Users.query.filter(Users.id == route.user_id).first()
    photos = Photos.query.filter(Photos.route_id == route.id).all()
    if request.method == 'GET':
        visit = Visit.query.filter(Visit.route_id == route.id and Visit.user_id == current_user.id).all()
        if len(visit) == 0 or visit is None:
            visit = 0
        else:
            visit = 1
        return render_template("route.html", user=user, route=route, comments=comments, photos=photos, visit=visit)
    visit = Visit(user_id=current_user.id, route_id=route.id)
    db.session.add(visit)
    db.session.commit()
    visit = 1
    return render_template("route.html", user=user, route=route, comments=comments, photos=photos, visit=visit)


@app.route('/delete_route/<int:id>')
@login_required
def del_route(id):
    route = Routes.query.filter_by(id=id).first()
    photos = Photos.query.filter(Photos.route_id == route.id).all()
    if current_user.id == route.user_id:
        try:
            db.session.delete(route)
            for photo in photos:
                db.session.delete(photo)
            db.session.commit()
            flash('Маршрут удалён!')
            # отправить на почту,что маршрут удалён
            return redirect("/")
        except Exception as e:
            flash('Ошибка при удалении')
            return redirect("/")
    else:
        flash('Нет доступа')
        return redirect("/")


@app.route('/delete_account/<int:id>')
@login_required
def del_account(id):
    user = Users.query.filter_by(id=id).first()
    try:
        logout_user()
        db.session.delete(user)
        db.session.commit()
        flash('Аккаунт удалён!')
        return redirect("/")
    except Exception as e:
        flash('Ошибка при удалении')
        return redirect("/")


@app.route('/get_coords/<int:id>', methods=['GET', 'POST'])
def get_coords(id):
    route = Routes.query.filter_by(id=id).first()
    route_coords = route.route_coords.split("@")
    res = []
    for point_coords in route_coords:
        res.append(point_coords.split(";"))
    return jsonify(res)


@app.route('/import_coords', methods=['GET', 'POST'])
def import_coords():
    if request.method == 'POST':
        url = request.json['url']
        if "openstreetmap" in url:
            parsed_url = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed_url.query)

            # Извлекаем маршрут
            route_param = query_params.get('route', [])

            if not route_param:
                return jsonify({"error": "Route parameter not found"}), 400

            # Получаем координаты и разделяем их
            route = route_param[0]
            coordinates = route.split(';')

            imp_coord = [tuple(map(float, coord.split(','))) for coord in coordinates]

            return jsonify(imp_coord)
        else:
            if "maps.app.goo.gl" in url:
                r = requests.get(url)
                title_point = []
                imp_coord = []
                geocode_url = "https://geocode-maps.yandex.ru/1.x/"
                api_key = "fc583f53-ce4b-49a8-9926-2cc9b2ac3082"
                for i in range(5, len(r.url.split("/"))):
                    if "@" in urllib.parse.unquote(r.url.split("/")[i]):
                        break
                    else:
                        title_point.append(urllib.parse.unquote(r.url.split("/")[i]).replace("+", " "))
                for title in title_point:
                    response = requests.get(geocode_url,
                                            params={'apikey': api_key, 'geocode': title, 'format': 'json'})
                    data = response.json()
                    coords = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point'][
                        'pos'].split()
                    imp_coord.append([float(coords[1]), float(coords[0])])  # [latitude, longitude]
                return jsonify(imp_coord)
            elif "yandex.ru/maps" in url:
                imp_coord = []
                sp_coords = url.split("mode=routes&rtext=")[1].split("&")[0].split("~")
                for coords in sp_coords:
                    coords = coords.split("%2C")
                    imp_coord.append([float(coords[0]), float(coords[1])])  # [latitude, longitude]
                return jsonify(imp_coord)
            else:
                return jsonify({"error": "Нельзя из такого сервиса импортировать"}), 400



@app.route('/map', methods=['GET', 'POST'])
def maps():
    if request.method == 'POST':
        data = request.json
        points = data['points']

        geocode_url = "https://geocode-maps.yandex.ru/1.x/"
        api_key = "fc583f53-ce4b-49a8-9926-2cc9b2ac3082"

        coordinates = []
        for point in points:
            str_point = f"{point[1]},{point[0]}"
            response = requests.get(geocode_url, params={'apikey': api_key, 'geocode': str_point, 'format': 'json'})
            data = response.json()
            coords = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos'].split()
            coordinates.append([float(coords[1]), float(coords[0])])  # [latitude, longitude]
        return jsonify(coordinates)

    return render_template("map.html")


@app.route('/edit_data/<int:id>', methods=["POST", "GET"])
def edit_data(id):
    user = Users.query.filter_by(id=id).first()
    if current_user.is_authenticated and (current_user.id == user.id or current_user.admin == 1):
        if request.method == "GET":
            return render_template("edit_data.html", user=user)
        if request.method == "POST":
            email = request.form.get('email')
            username = request.form.get('username')
            try:
                user.email = email
                user.username = username
                db.session.commit()
                flash("Данные изменены")
                return redirect('/profile')
            except:
                flash("Возникла ошибка при изменении данных")
                return redirect('/profile')
    else:
        flash('Нет доступа')
        return redirect('/')


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
            who_edit = ""
            if current_user.admin == 1:
                who_edit = "admin"
            else:
                who_edit = "author"
            try:
                history_route = History(title=route.title, description=route.description, user_id=route.user_id,
                                        rating=route.rating, status=route.status, route_id=route.id, last=1,
                                        who_edit=who_edit)
                past_history = History.query.filter(History.route_id == id and History.last == 1).first()
                if not (past_history is None):
                    past_history.last = 0
                db.session.add(history_route)
                route.title = title
                route.description = description
                route.status = status
                if current_user.admin == 1:
                    route.check_admin = 1
                db.session.commit()
                flash("Маршрут изменён")
                # если изменил админ, отправить на почту автора, что админ изменил его маршрут
                return redirect(f'/route/{id}')
            except:
                flash("Возникла ошибка при изменении маршрута")
                return redirect('/all_routes')
    else:
        flash('Нет доступа')
        return redirect('/')


@app.route('/edit_comment/<int:id>', methods=["POST", "GET"])
def edit_comment(id):
    comment = Comments.query.filter_by(id=id).first()
    if current_user.is_authenticated and (current_user.id == comment.user_id or current_user.admin == 1):
        if request.method == "GET":
            return render_template("edit_comment.html", comment=comment)
        if request.method == "POST":
            text = request.form.get('text')
        try:
            comment.text = text
            if current_user.admin == 1:
                comment.check_admin = 1
            db.session.commit()
            flash("Комментарий изменён")
            # если изменил админ, отправить на почту автора, что админ изменил его комментарий
        except Exception as e:
            flash("Возникла ошибка при изменении комменатрия")
            return redirect('/')
    else:
        flash('Нет доступа')
        return redirect('/')


@app.route('/delete_comment/<int:id>')
@login_required
def del_comment(id):
    comment = Comments.query.filter_by(id=id).first()
    try:
        db.session.delete(comment)
        db.session.commit()
        flash('Комментарий удалён!')
        return redirect("/")
    except Exception as e:
        flash('Ошибка при удалении')
        return redirect("/")


@app.route('/moderation')
def moderation():
    routes = Routes.query.filter(Routes.check_admin == 0).all()
    comments = Comments.query.filter(Comments.check_admin == 0).all()
    return render_template("moderation.html", routes=routes, comments=comments)


@app.route('/history_route/<int:id>', methods=["POST", "GET"])
def history_route(id):
    route = Routes.query.filter_by(id=id).first()
    last_history = History.query.filter(History.route_id == id and History.last == 1).first()
    past_history = History.query.filter(History.route_id == id and History.last == 0).all()
    who_edit = ""
    if last_history.who_edit == "admin":
        who_edit = "администратор"
    else:
        who_edit = "автор"
    no_edit_title = 0
    no_edit_description = 0
    red_text_title = ""
    green_text_title = ""
    just_text_title = ""
    red_text_description = ""
    green_text_description = ""
    just_text_description = ""
    if not (last_history is None):
        if route.title != last_history.title:
            for i in range(max(len(route.title), len(last_history.title))):
                try:
                    if route.title[i] == last_history.title[i]:
                        just_text_title += route.title[i]
                    else:
                        green_text_title += route.title[i]
                        red_text_title += last_history.title[i]
                except Exception as e:
                    if len(route.title) > len(last_history.title):
                        green_text_title += route.title[i:]
                    else:
                        red_text_title += last_history.title[i:]
                    break
        else:
            no_edit_title = 1
        if route.description != last_history.description:
            for i in range(max(len(route.description), len(last_history.description))):
                try:
                    if route.description[i] == last_history.description[i]:
                        just_text_description += route.description[i]
                    else:
                        green_text_description += route.description[i]
                        red_text_description += last_history.description[i]
                except Exception as e:
                    if len(route.description) > len(last_history.description):
                        green_text_description += route.description[i:]
                    else:
                        red_text_description += last_history.description[i:]
                    break
        else:
            no_edit_description = 1
    else:
        no_edit_title = 1
        no_edit_description = 1
    return render_template("history.html", just_text_title=just_text_title, red_text_title=red_text_title,
                           green_text_title=green_text_title, no_edit_title=no_edit_title,
                           just_text_description=just_text_description, red_text_description=red_text_description,
                           green_text_description=green_text_description, no_edit_description=no_edit_description,
                           past_history=past_history, who_edit=who_edit)


@app.route('/export/gpx/<int:id>', methods=["POST", "GET"])
def export_gpx(id):
    # Создаем GPX файл
    gpx = gpxpy.gpx.GPX()
    route = Routes.query.filter_by(id=id).first()
    route_coords = route.route_coords.split("@")
    i = 1
    for point_coords in route_coords:
        coords = point_coords.split(";")
        gpx.waypoints.append(
            gpxpy.gpx.GPXWaypoint(latitude=float(coords[0]), longitude=float(coords[1]), name=f'Точка {i}'))
        i += 1

    # Сохраняем GPX файл во временный файл
    gpx_file_path = 'temp/output.gpx'
    if not os.path.exists(gpx_file_path):
        return 404
    with open(gpx_file_path, 'w') as f:
        f.write(gpx.to_xml())

    return send_file(gpx_file_path, as_attachment=True)


@app.route('/export/kml/<int:id>', methods=["POST", "GET"])
def export_kml(id):
    # Создаем KML файл
    kml = simplekml.Kml()
    route = Routes.query.filter_by(id=id).first()
    route_coords = route.route_coords.split("@")
    i = 1
    for point_coords in route_coords:
        coords = point_coords.split(";")
        kml.newpoint(name=f"Точка {i}", coords=[(float(coords[1]), float(coords[0]))])  # (longitude, latitude)
        i += 1

    # Сохраняем KML файл во временный файл
    kml_file_path = 'temp/output.kml'
    kml.save(kml_file_path)

    return send_file(kml_file_path, as_attachment=True)


@app.route('/export/kmz/<int:id>', methods=["POST", "GET"])
def export_kmz(id):
    # Создаем KML файл
    kml = simplekml.Kml()
    route = Routes.query.filter_by(id=id).first()
    route_coords = route.route_coords.split("@")
    i = 1
    for point_coords in route_coords:
        coords = point_coords.split(";")
        kml.newpoint(name=f"Точка {i}", coords=[(float(coords[1]), float(coords[0]))])  # (longitude, latitude)
        i += 1

    # Сохраняем KMZ файл во временный файл
    kmz_file_path = 'temp/output.kmz'
    kml.savekmz(kmz_file_path)

    return send_file(kmz_file_path, as_attachment=True)


# @app.route('/export/png/<int:id>', methods=["POST", "GET"])
# def export_png(id):
#     apikey = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
#     route = Routes.query.filter_by(id=id).first()
#     route_coords = route.route_coords.split("@")
#     i = 1
#     pt = ""
#     pl = ""
#     for point_coords in route_coords:
#         coords = point_coords.split(";")
#         org_point = f"{coords[0]},{coords[1]}"
#         pt += f"{org_point},pm2dgl~"
#         pl += f"{org_point},"
#     pl = pl[:-1]
#     pt = pt[:-1]
#
#     # Собираем параметры для запроса к StaticMapsAPI:
#     map_params = {
#         "ll": "56.0184,92.8672",
#         "apikey": apikey,
#         "pt": pt,
#         "pl": pl
#     }
#
#     map_api_server = "https://static-maps.yandex.ru/v1"
#     response = requests.get(map_api_server, params=map_params)
#     print(response.url)
#     im = BytesIO(response.content)
#     opened_image = Image.open(im)
#     png_file_path = "temp/output.png"
#     opened_image.save(png_file_path)
#
#     return send_file(png_file_path, as_attachment=True)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
