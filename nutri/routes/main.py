from flask import current_app as app
from flask import make_response, redirect, render_template, request, url_for

from .dishes import list_dishes
from .. import fs, db



@app.route("/")
def index():
    return render_template('index.html', dishes=list_dishes())