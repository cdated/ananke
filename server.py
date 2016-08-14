#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
import pymongo
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

USER="cdated"

def handle_current(goal, value, col, match):
    current = goal['current']
    # Tally today's progress
    done_today = int(goal['done_today']) + int(value) - int(current)
    col.update(match, {'$set': {"done_today": done_today}})

    # Update date
    today = datetime.now().date()
    col.update(match, {'$set': {"updated": str(today)}})

@app.route('/goals/<int:goal_id>', methods=['POST', 'GET'])
def update_progress(goal_id):
    col = db.goals
    goal = col.find_one({"uid":USER, "id":goal_id})

    if request.method == 'POST':
        match = {"uid":USER, "id":goal_id}

        for field in ['name', 'units', 'current', 'total']:
            if field in request.form:
                value = request.form[field]
                if field == 'current':
                    handle_current(goal, value, col, match)
                update = {'$set': {field: value}}
                col.update(match, update)

        # Update the start/end if value with appropriate times
        for dateType, offset in [('startDate', 'T00:00:00Z'),
                                 ('endDate', 'T23:59:59Z')]:
            if dateType in request.form:
                if request.form[dateType]:
                    value = request.form[dateType] + offset
                    update = {'$set': {dateType: value}}
                    col.update(match, update)

        return redirect('/')

    if request.method == 'GET':
        title = "Ananke - " + goal["name"]
        return render_template('goal.html', title=title, goal=goal)

@app.route('/')
def index():
    col = db.goals
    goals= col.find({"uid":USER}).sort("endDate", 1)

    # Clear out done_todays from yesterdays
    today = datetime.now().date()
    for goal in goals:
        updated = goal['updated']
        last_updated = datetime.strptime(updated, '%Y-%m-%d').date()
        if last_updated != today:
            update = {'$set': {'done_today': 0}}
            col.update({"uid":USER, "id": goal["id"]}, update)

    goals= col.find({"uid":USER}).sort("endDate", 1)

    return render_template('index.html', title="Ananke - Goals", goals=goals)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.debug = True

    uri = os.environ.get('MONGOCLIENT', 'localhost')
    client = pymongo.MongoClient(uri)
    db = client.ananke

    app.run(host='0.0.0.0', port=port)
