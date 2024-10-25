from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
mysql = MySQL(app)
app.secret_key = 'your_secret_key'

# Home page to view all discs
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM discs")
    discs = cur.fetchall()
    cur.close()
    return render_template('index.html', discs=discs)

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
        disc_type = request.form['type']  # Get the type from the dropdown
        is_lost = False  # New discs are not lost by default

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO discs (manufacturer, mold, plastic, speed, glide, turn, fade, color, notes, type, is_lost) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (manufacturer, mold, plastic, speed, glide, turn, fade, color, notes, disc_type, is_lost))
        mysql.connection.commit()
        cur.close()
        flash('Disc Added Successfully!')
        return redirect(url_for('index'))

    return render_template('add_disc.html')

# Edit disc
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_disc(id):
    cur = mysql.connection.cursor()

    # Fetch the existing disc data from the database
    cur.execute("SELECT * FROM discs WHERE id = %s", (id,))
    disc = cur.fetchone()
    cur.close()

    if request.method == 'POST':
        # Get the form data
        manufacturer = request.form.get('manufacturer')
        mold = request.form.get('mold')
        plastic = request.form.get('plastic')
        speed = request.form.get('speed', type=int)  # Ensure this is an integer
        glide = request.form.get('glide', type=int)  # Ensure this is an integer
        turn = request.form.get('turn', type=int)  # Ensure this is an integer
        fade = request.form.get('fade', type=int)  # Ensure this is an integer
        color = request.form.get('color')
        notes = request.form.get('notes')
        disc_type = request.form.get('type')  # Get the disc type from the dropdown
        is_lost = request.form.get('is_lost') == 'on'  # Checkbox handling

        # Validate required fields
        if not manufacturer or not mold or not disc_type:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('edit_disc', id=id))

        # Update the disc information in the database
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE discs
            SET manufacturer=%s, mold=%s, plastic=%s, speed=%s, glide=%s, turn=%s, fade=%s, color=%s, notes=%s, type=%s, is_lost=%s
            WHERE id=%s
        """, (manufacturer, mold, plastic, speed, glide, turn, fade, color, notes, disc_type, is_lost, id))
        mysql.connection.commit()
        cur.close()

        flash('Disc Updated Successfully!', 'success')
        return redirect(url_for('index'))

    # Render the edit_disc template, passing in the current disc data
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
