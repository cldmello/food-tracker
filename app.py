from flask import Flask, request, render_template, g

import sqlite3
from datetime import datetime

app = Flask(__name__)

def connect_db():
    sql = sqlite3.connect("food_log.db")
    sql.row_factory = sqlite3.Row
    return sql


def get_db():
    if not hasattr(g, 'sqlite3_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()

    if request.method == 'POST':
        newday = datetime.strptime(request.form['newday'], "%Y-%m-%d")
        db.execute('insert into log_date (entry_date) values (?)', [datetime.strftime(newday, "%Y%m%d")])
        db.commit()

    cur = db.execute('select log_date.entry_date, sum(food.protein) as protein, sum(food.carbohydrates) as carbs, sum(food.fat) as fat, sum(food.calories) as cals from log_date join food_date on log_date.id = food_date.log_date_id join food on food.id = food_date.food_id group by log_date.id order by log_date.entry_date desc')
    results = cur.fetchall()

    pretty_dates = []

    for i in results:
        dates = {}
        dates['entry_date'] = i['entry_date']
        dates['protein'] = i['protein']
        dates['carbs'] = i['carbs']
        dates['fat'] = i['fat']
        dates['cals'] = i['cals']
        d = datetime.strptime(str(i['entry_date']), "%Y%m%d")
        dates['pretty_date'] = datetime.strftime(d, "%B %d, %Y")
        pretty_dates.append(dates)

    return render_template('home.html', results=pretty_dates)


@app.route('/view/<date>', methods=['GET', 'POST'])
def view(date):
    db = get_db()
    cur = db.execute('select id, entry_date from log_date where entry_date = ?', [date])
    result = cur.fetchone()

    if request.method == 'POST':
        db.execute('insert into food_date (food_id, log_date_id) values (?, ?)', \
            [request.form['food-select'], result['id']])
        db.commit()

    d = datetime.strptime(str(result['entry_date']), "%Y%m%d")
    pretty_date = datetime.strftime(d, "%B %d, %Y")

    food_cur = db.execute('select id, name from food')
    foods = food_cur.fetchall()

    log_cur = db.execute('select food.* from log_date join food_date on log_date.id = food_date.log_date_id join food on food.id = food_date.food_id where log_date.entry_date = ?', [date])
    logs = log_cur.fetchall()

    totals = {}
    totals['protein'] = 0
    totals['carbohydrates'] = 0
    totals['fat'] = 0
    totals['calories'] = 0

    for log in logs:
        totals['protein'] += log['protein']
        totals['carbohydrates'] += log['carbohydrates']
        totals['fat'] += log['fat']
        totals['calories'] += log['calories']

    return render_template('day.html', entry_date=result['entry_date'], pretty_date=pretty_date, foods=foods, logs=logs, totals=totals)


@app.route('/food', methods=['GET', 'POST'])
def food():
    db = get_db()

    if request.method == 'POST':
        food = request.form['food-name']
        protein = int(request.form['protein'])
        carbs = int(request.form['carbohydrates'])
        fat = int(request.form['fat'])
        calories = protein * 4 + carbs * 4 + fat * 9

        db.execute('insert into food (name, protein, carbohydrates, fat, calories) values (?, ?, ?, ?, ?)', \
            [food, protein, carbs, fat, calories])
        db.commit()

    cur = db.execute('select name, protein, carbohydrates, fat, calories from food')
    res = cur.fetchall()

        # return "Name: {}, Prot: {}, Carbs: {}, Fat: {}".format(food, protein, carbs, fat)
    return render_template('add_food.html', res=res)



if __name__ == '__main__':
    app.run(debug=True)

