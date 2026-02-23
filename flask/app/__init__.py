import os
from flask import Flask, request, redirect
from werkzeug.debug import DebuggedApplication
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from authlib.integrations.flask_client import OAuth


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


app = Flask(__name__, static_folder='static')
app.url_map.strict_slashes = False


app.jinja_options = app.jinja_options.copy()
app.jinja_options.update({
    'trim_blocks': True,
    'lstrip_blocks': True
})


app.config['DEBUG'] = True
app.config['SECRET_KEY'] = \
    'db2307d2ce4bee5f09a8a759c1712b72bc232c10b8096512'
app.config['JSON_AS_ASCII'] = False


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite://")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['GOOGLE_CLIENT_ID'] = os.getenv("GOOGLE_CLIENT_ID", None)
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv("GOOGLE_CLIENT_SECRET", None)
app.config['GOOGLE_DISCOVERY_URL'] = os.getenv("GOOGLE_DISCOVERY_URL", None)


app.config['CMU_CLIENT_ID'] = os.getenv("CMU_CLIENT_ID", None)
app.config['CMU_CLIENT_SECRET'] = os.getenv("CMU_CLIENT_SECRET", None)
app.config['CMU_CALLBACK_URI'] = os.getenv("CMU_CALLBACK_URI", None)

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 2MB Limit


if app.debug:
    app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)


csrf = CSRFProtect(app)
csrf.init_app(app)


# Creating an SQLAlchemy instance
db = SQLAlchemy(app)
oauth = OAuth(app)


login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.before_request
def remove_trailing_slash():
   # Check if the path ends with a slash but is not the root "/"
    if request.path != '/' and request.path.endswith('/'):
        return redirect(request.path[:-1], code=301)


from app import views  # noqa