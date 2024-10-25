import os

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
# Import the appropriate config class
from config import DevelopmentConfig, TestingConfig, ProductionConfig

app = Flask(__name__)

# Load the configuration based on FLASK_ENV
env = os.getenv('FLASK_ENV', 'development')
if env == 'production':
    app.config.from_object(ProductionConfig)
elif env == 'testing':
    app.config.from_object(TestingConfig)
else:
    app.config.from_object(DevelopmentConfig)

mysql = MySQL(app)

# Home page to view all discs
@app.route('/')
def index():
    # Get URL parameters for sorting and search only
    sort_by = request.args.get('sort_by', 'manufacturer')
    query = request.args.get('query', '')

    # Create SQL for search and sort
    search_sql = f"WHERE manufacturer LIKE %s OR mold LIKE %s" if query else ""
    order_sql = f"ORDER BY {sort_by}"

    # Execute the query to fetch all discs with sorting and filtering, but no pagination
    cur = mysql.connection.cursor()
    cur.execute(f"""
        SELECT * FROM discs
        {search_sql} {order_sql}
    """, (f'%{query}%', f'%{query}%') if query else ())
    discs = cur.fetchall()
    cur.close()

    return render_template('index.html', discs=discs, query=query, sort_by=sort_by)


# Add new disc
@app.route('/add', methods=['GET', 'POST'])
def add_disc():
    if request.method == 'POST':
        manufacturer = request.form['manufacturer']
        mold = request.form['mold']
        plastic = request.form['plastic']
        speed = request.form['speed']
        glide = request.form['glide']
        turn = request.form['turn']
        fade = request.form['fade']
        color = request.form['color']
        notes = request.form['notes']
        disc_type = request.form['type']
        weight = request.form.get('weight', type=float)  # New weight field
        is_lost = False  # New discs are not lost by default

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO discs (manufacturer, mold, plastic, speed, glide, turn, fade, color, notes, type, weight, is_lost) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (manufacturer, mold, plastic, speed, glide, turn, fade, color, notes, disc_type, weight, is_lost))
        mysql.connection.commit()
        cur.close()
        flash('Disc Added Successfully!')
        return redirect(url_for('index'))

    return render_template('add_disc.html')

# Edit disc
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_disc(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM discs WHERE id = %s", (id,))
    disc = cur.fetchone()
    cur.close()

    if request.method == 'POST':
        manufacturer = request.form['manufacturer']
        mold = request.form['mold']
        plastic = request.form['plastic']
        speed = request.form['speed']
        glide = request.form['glide']
        turn = request.form['turn']
        fade = request.form['fade']
        color = request.form['color']
        notes = request.form['notes']
        disc_type = request.form['type']
        weight = request.form.get('weight', type=float)  # New weight field
        is_lost = request.form.get('is_lost') == 'on'

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE discs
            SET manufacturer=%s, mold=%s, plastic=%s, speed=%s, glide=%s, turn=%s, fade=%s, color=%s, notes=%s, type=%s, weight=%s, is_lost=%s
            WHERE id=%s
        """, (manufacturer, mold, plastic, speed, glide, turn, fade, color, notes, disc_type, weight, is_lost, id))
        mysql.connection.commit()
        cur.close()

        flash('Disc Updated Successfully!')
        return redirect(url_for('index'))

    return render_template('edit_disc.html', disc=disc)

# Delete disc
@app.route('/delete/<int:id>', methods=['POST'])
def delete_disc(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM discs WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    flash('Disc Deleted Successfully!')
    return redirect(url_for('index'))

# Mark disc as lost
@app.route('/mark_lost/<int:id>', methods=['POST'])
def mark_lost(id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE discs SET is_lost = TRUE WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    flash('Disc Marked as Lost!')
    return redirect(url_for('index'))

# Search and sort discs
@app.route('/search')
def search():
    query = request.args.get('query')
    sort_by = request.args.get('sort_by', 'manufacturer')  # Default sort by manufacturer
    cur = mysql.connection.cursor()
    if query:
        cur.execute(f"SELECT * FROM discs WHERE manufacturer LIKE %s OR mold LIKE %s ORDER BY {sort_by}",
                    (f'%{query}%', f'%{query}%'))
    else:
        cur.execute(f"SELECT * FROM discs ORDER BY {sort_by}")
    discs = cur.fetchall()
    cur.close()
    return render_template('index.html', discs=discs)

if __name__ == '__main__':
    app.run(debug=True)
