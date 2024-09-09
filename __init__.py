import os

from flask import Flask, redirect, g



def create_app(test_config = None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    UPLOAD_FOLDER = 'uploads/'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    from . import views
    app.register_blueprint(views.bp)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    return app