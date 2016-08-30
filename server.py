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

def groups():
    return db.goals.distinct("group")

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
                "done_today" : 0,
                "group" : "School",
                "priority" : 0,
                "notes" : ""
                }

    if request.method == 'POST':
        for field in ['name', 'units', 'current', 'total', 'notes',
                      'group','priority']:
            if field in request.form:
                new_goal[field] = request.form[field]

        # Update the start/end if value with appropriate times
        for dateType, offset in [('startDate', 'T00:00:00'),
                                 ('endDate', 'T23:59:59')]:
            if dateType in request.form:
                if request.form[dateType]:
                    new_goal[field] = request.form[dateType] + offset

        col.insert(new_goal)
        return redirect('/')


    if request.method == 'GET':
        title = "Ananke - New Goal"
        return render_template('goal.html', title=title, goal=new_goal,
                               groups=groups(), operation='Create')

def handle_current(goal, value, col, match):
    current = goal['current']
    # Tally today's progress
    done_today = int(goal['done_today']) + int(value) - int(current)
    col.update(match, {'$set': {"done_today": done_today}})

    # Update date
    today = datetime.now().date()
    col.update(match, {'$set': {"updated": str(today)}})

@app.route('/goals/<string:goal_id>/clear_today', methods=['POST'])
def clear_today(goal_id):
    print(goal_id)
    col = db.goals
    update = {'$set': {'done_today': 0}}
    col.update({"uid":USER, "_id": ObjectId(goal_id)}, update)
    return redirect('/#' + goal_id)

@app.route('/goals/<string:goal_id>/copy', methods=['POST'])
def copy_goal(goal_id):
    col = db.goals
    goal = col.find_one({"uid":USER, "_id": ObjectId(goal_id)})

    # Insert new goal object with a new _id
    goal['_id'] = ObjectId()
    col.insert(goal)
    return redirect('/')

@app.route('/goals/<string:goal_id>/archive', methods=['POST'])
def archive_goal(goal_id):
    print("ACHIVING")
    col = db.goals
    match = {"uid":USER, "_id": ObjectId(goal_id)}
    update = {'$set': {"archived": True}}
    col.update(match, update)
    return redirect('/')

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

        for field in ['name', 'units', 'current', 'total',
                      'notes', 'group', 'priority']:
            if field in request.form:
                value = request.form[field]
                if field == 'current':
                    handle_current(goal, value, col, match)
                update = {'$set': {field: value}}
                col.update(match, update)

        # Update the start/end if value with appropriate times
        for dateType, offset in [('startDate', 'T00:00:00'),
                                 ('endDate', 'T23:59:59')]:
            if dateType in request.form:
                if request.form[dateType]:
                    value = request.form[dateType] + offset
                    update = {'$set': {dateType: value}}
                    col.update(match, update)

        referrer = request.form['route']
        if "group" in referrer:
            return redirect(referrer)

        return redirect('/#' + goal_id)

    if request.method == 'GET':
        title = "Ananke - " + goal["name"]
        return render_template('goal.html', title=title, goal=goal, groups=groups(),
                               operation='Update')

@app.route('/goals/group/<string:group>', methods=['GET'])
def group(group):
    col = db.goals
    goals = col.find({"uid":USER, "group": group, "archived": {"$ne": True}}).sort([("priority", -1), ("endDate", 1)])

    return render_template('index.html', title="Ananke - Archived Goals", goals=goals, groups=groups(), archive='True')

@app.route('/goals/archived', methods=['GET'])
def archived():
    col = db.goals
    goals = col.find({"uid":USER, "archived": {"$eq": True}}).sort([("priority", -1), ("endDate", 1)])

    return render_template('index.html', title="Ananke - Archived Goals", goals=goals, groups=groups(), archive='True')

@app.route('/')
def index():
    col = db.goals

    # Clear out done_todays from yesterdays
    today = datetime.now().date()
    goals= col.find({"uid":USER})
    for goal in goals:
        updated = goal['updated']
        last_updated = datetime.strptime(updated, '%Y-%m-%d').date()
        if last_updated != today:
            update = {'$set': {'done_today': 0}}
            col.update({"uid":USER, "_id": goal["_id"]}, update)

    goals = col.find({"uid":USER, "archived": {"$ne": True}}).sort([("priority", -1), ("endDate", 1)])

    return render_template('index.html', title="Ananke - Goals", goals=goals, groups=groups())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.debug = True

    uri = os.environ.get('MONGOCLIENT', 'localhost')
    client = pymongo.MongoClient(uri)
    db = client.ananke

    app.run(host='0.0.0.0', port=port)
