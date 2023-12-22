# export FLASK_APP=server

import sys
sys.path.append("/opt/anaconda3/lib/python3.7/site-packages")
from flask import Flask, render_template, request, redirect
# from read import Tech
import yaml
from yaml import SafeLoader, FullLoader

app = Flask(__name__)


@app.route('/', methods=["GET", "POST"])
def home():
    obj1 = navigation()
    obj = obj1.data()

    return render_template('index.jinja2', obj=obj)


if __name__ == '__main__':
    app.run()