from flask import jsonify
import os
import json
from os import walk
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, make_response, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from turbo_flask import Turbo
from werkzeug.exceptions import abort
from flask_httpauth import HTTPTokenAuth
from werkzeug.utils import secure_filename, redirect

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
turbo = Turbo(app)
auth = HTTPTokenAuth(scheme='Bearer')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pref.db'
db = SQLAlchemy(app)


class Tracker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100), nullable=False)
    userId = db.Column(db.String(36), nullable=False, unique=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Tracker %r>' % self.id


def check_auth(login, password):
    return login == 'user' and password == 'password'


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not (auth and check_auth(auth.username, auth.password)):
            return make_response('Auth failed', 401, {'WWW-Authenticate': 
                                                      'Basic realm="Login required"'})
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/user/get_key', methods=['GET'])
@auth.verify_token
def get_key():
    if request.headers.get("token"):
        try:
            Id = request.headers.get("token")
            User = Tracker.query.filter_by(userId=Id).one()
            if User is not None:
                with open("logs/log.txt", "a") as f:
                    f.write(
                        str(datetime.utcnow()) + "->" + request.remote_addr + "->" + str(User.user) + "->" + Id + '\n')
                return jsonify(trackId=User.id)
            else:
                return
        except:
            return
    with open("logs/log.txt", "a") as f:
        f.write(str(datetime.utcnow()) + "->" + request.remote_addr + '\n')
    return


@app.route('/admin', methods=["GET"])
@auth_required
def admin():
    return render_template('admin.html')


@app.route('/admin/apps_list', methods=["GET"])
@auth_required
def apps_list():
    folder = os.path.join(app.config.root_path, 'applications/')
    filenames = next(walk(folder), (None, None, []))[2]  # [] if no file
    return render_template('apps_list.html', apps=filenames)


@app.route('/admin/up', methods=["GET"])
@auth_required
def form():
    folder = os.path.join(app.config.root_path, 'manifests/')
    filenames = next(walk(folder), (None, None, []))[2]  # [] if no file
    return render_template('upload.html', jsons=filenames)


@app.route('/admin/tracker', methods=["GET"])
@auth_required
def tracker():
    Data = Tracker.query.order_by(Tracker.id).all()
    ids = []
    names = []
    for el in Data:
        names.append(el.user)
        ids.append(el.userId)
    return render_template('tracker_preferences.html', data=Data, names=names, ids=ids)


@app.route('/admin/tracker/save', methods=["POST"])
@auth_required
def save_track():
    UserName = request.form['user']
    UserUUID = request.form['uid']
    if len(UserName) == 0 or len(UserUUID) < 36:
        return "Ошибка добавления"
    User = Tracker(user=UserName, userId=UserUUID, date=datetime.utcnow())
    try:
        db.session.add(User)
        db.session.commit()
    except:
        return "Ошибка добавления"
    return redirect(url_for('tracker'))


@app.route('/admin/tracker/delete', methods=["POST"])
@auth_required
def delete_track():
    UserName = request.form['user']
    UserUUID = request.form['uid']
    Id = request.form['user_track_id']
    if len(UserName) == 0 or len(UserUUID) < 36:
        return "Ошибка удаления"
    try:
        track = Tracker.query.get(Id)
        db.session.delete(track)
        db.session.commit()
    except:
        return "Ошибка удаления"
    return redirect(url_for('tracker'))


@app.route('/admin/tracker/update', methods=["POST"])
@auth_required
def update_track():
    UserName = request.form['user']
    UserUUID = request.form['uid']
    Id = request.form['user_track_id']
    if len(UserName) == 0 or len(UserUUID) < 36:
        return "Ошибка обновления"
    track = Tracker.query.get(Id)
    track.user = UserName
    track.userId = UserUUID
    track.date = datetime.utcnow()
    try:
        db.session.commit()
    except:
        return "Ошибка обновления"
    return redirect(url_for('tracker'))


@app.route('/admin/upload', methods=['POST'])
@auth_required
def upload():
    file = request.files['file']
    if (file is None) or (not file.filename.endswith(".apk")):
        return "No acceptable file selected"
    else:
        if request.form.get('flexCheckDisabled') is not None and request.form['flexCheckDisabled']:
            if request.form['manifest-select'] == '':
                return "no manifest name provided"
            name = request.form['manifest-select']
        else:
            if request.form['manifest'] == '':
                return "no manifest name provided"
            name = request.form['manifest'] + ".json"

        if request.form['version'] == '':
            return "no version provided"
        if request.form['description'] == '':
            return "no description provided"

        version = request.form['version']
        description = request.form['description']
        file_name = name.replace(".json", "_" + version + ".apk")
        obj = json.dumps(
            {'url': "http://82.162.17.37:2922/applications/" + file_name, 'versionCode': int(version),
             'updateMessage': description}, separators=(', ', ':'), indent=2)
        print(obj)
        obj = obj.replace('/n', '')
        filepath = "manifests/" + name
        with open(filepath, "w", encoding='utf-8') as fp:
            fp.write(obj)
        file.save('applications/' + secure_filename(file_name))
    return redirect(url_for('apps_list'))


@app.route('/applications/<path:path>', methods=['GET'])
def get_apk(path):
    with open("logs/log.txt", "a") as f:
        f.write(str(datetime.utcnow()) + "->" + request.remote_addr + '\n')
    try:
        folder = os.path.join(app.config.root_path, 'applications/')
        return send_from_directory(folder, path)
    except FileNotFoundError:
        abort(404)


@app.route('/admin/files/delete/<path:path>', methods=['GET'])
@auth_required
def delete_file(path):
    os.remove("applications/" + path)
    return redirect(url_for('apps_list'))


@app.route('/manifests/<path:path>', methods=['GET'])
def get_manifest(path):
    with open("logs/log.txt", "a") as f:
        f.write(str(datetime.utcnow()) + "->" + request.remote_addr + '\n')
    try:
        folder = os.path.join(app.config.root_path, 'manifests/')
        return send_from_directory(folder, path)
    except FileNotFoundError:
        abort(404)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2922, threaded=True, debug=False)
