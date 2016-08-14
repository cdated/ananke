#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import pymongo
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route('/goals/<int:goal_id>', methods=['POST', 'GET'])
def update_progress(goal_id):
    if request.method == 'POST':
        progress = request.form['progress']
        col = db.goals
        match = {"uid":"cdated", "id":goal_id}
        update = {'$set': {'current': progress}}
        col.update(match, update)

    return redirect('/')

@app.route('/')
def index():
    col = db.goals
    goals= col.find({"uid":"cdated"})
    return render_template('test.html', title="Ananke - Goals", goals=goals)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.debug = True

    uri = os.environ.get('MONGOCLIENT', 'localhost')
    client = pymongo.MongoClient(uri)
    db = client.ananke

    app.run(host='0.0.0.0', port=port)
