#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
import pymongo
from bson.objectid import ObjectId
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

USER="cdated"

@app.route('/goals/new', methods=['POST', 'GET'])
def new_goal():
    col = db.goals
    now = datetime.now()
    new_goal = {"name"  : "New Goal",
                "uid"   : USER,
                "units" : "Pomodoros",
                "current": 0,
                "total" : 100,
                "startDate" : now.replace(hour=0, minute=0, second=0,
                                          microsecond=0).isoformat(),
                "endDate" : now.replace(year=now.year + 1, hour=23, minute=59,
                                          second=59, microsecond=0).isoformat(),
                "updated" : str(now.date()),
                "done_today" : 0
                }

    if request.method == 'POST':
        for field in ['name', 'units', 'current', 'total']:
            if field in request.form:
                new_goal[field] = request.form[field]

        # Update the start/end if value with appropriate times
        for dateType, offset in [('startDate', 'T00:00:00Z'),
                                 ('endDate', 'T23:59:59Z')]:
            if dateType in request.form:
                if request.form[dateType]:
                    new_goal[field] = request.form[dateType] + offset

        col.insert(new_goal)
        return redirect('/')


    if request.method == 'GET':
        title = "Ananke - New Goal"
        return render_template('goal.html', title=title, goal=new_goal,
                               operation='Create')

def handle_current(goal, value, col, match):
    current = goal['current']
    # Tally today's progress
    done_today = int(goal['done_today']) + int(value) - int(current)
    col.update(match, {'$set': {"done_today": done_today}})

    # Update date
    today = datetime.now().date()
    col.update(match, {'$set': {"updated": str(today)}})

@app.route('/goals/<string:goal_id>/delete', methods=['POST'])
def delete_goal(goal_id):
    col = db.goals
    col.remove(ObjectId(goal_id))
    return redirect('/')

@app.route('/goals/<string:goal_id>', methods=['POST', 'GET'])
def update_progress(goal_id):
    col = db.goals
    goal = col.find_one({"uid":USER, "_id": ObjectId(goal_id)})

    if request.method == 'POST':
        match = {"uid":USER, "_id":ObjectId(goal_id)}

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
        return render_template('goal.html', title=title, goal=goal,
                               operation='Update')

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
            col.update({"uid":USER, "_id": goal["_id"]}, update)

    goals= col.find({"uid":USER}).sort("endDate", 1)

    return render_template('index.html', title="Ananke - Goals", goals=goals)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.debug = True

    uri = os.environ.get('MONGOCLIENT', 'localhost')
    client = pymongo.MongoClient(uri)
    db = client.ananke

    app.run(host='0.0.0.0', port=port)
