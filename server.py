#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    with open('goals.json') as data_file:
        data = json.load(data_file)

        return render_template('test.html', title="yolo", goals=data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)
