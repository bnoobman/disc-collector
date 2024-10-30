import os
import requests
import logging
from logging.config import dictConfig
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mysqldb import MySQL
from config import DevelopmentConfig, TestingConfig, ProductionConfig
from werkzeug.exceptions import HTTPException

# External API URL
API_BASE_URL = "http://localhost:8069/v1"

# Configure structured logging for Docker
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'formatter': 'default',
        'stream': 'ext://sys.stdout',
    }},
    'root': {
        'level': os.getenv("LOG_LEVEL", "INFO"),
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)

# Configure app based on environment
env = os.getenv('FLASK_ENV', 'development')
if env == 'production':
    app.config.from_object(ProductionConfig)
elif env == 'testing':
    app.config.from_object(TestingConfig)
else:
    app.config.from_object(DevelopmentConfig)

mysql = MySQL(app)


# Log incoming requests
@app.before_request
def log_request_info():
    app.logger.info(f"Request: {request.method} {request.url} - IP: {request.remote_addr}")


# Custom error handling
@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        app.logger.error(f"HTTP error {e.code}: {e.description}")
        return jsonify(error=str(e)), e.code
    app.logger.error("Unexpected error: %s", str(e), exc_info=True)
    return jsonify(error="An unexpected error occurred"), 500


@app.route('/')
def index():
    sort_by = request.args.get('sort_by', 'manufacturer')
    query = request.args.get('query', '')

    search_sql = f"WHERE manufacturer LIKE %s OR mold LIKE %s" if query else ""
    order_sql = f"ORDER BY {sort_by}"

    try:
        cur = mysql.connection.cursor()
        cur.execute(f"""
            SELECT * FROM discs
            {search_sql} {order_sql}
        """, (f'%{query}%', f'%{query}%') if query else ())
        discs = cur.fetchall()
        cur.close()
        return render_template('index.html', discs=discs, query=query, sort_by=sort_by)
    except Exception as e:
        app.logger.error(f"Database query error: {e}", exc_info=True)
        flash("Error fetching disc information.")
        return render_template('index.html', discs=[], query=query, sort_by=sort_by)


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
        weight = request.form.get('weight', type=float)
        is_lost = False

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO discs (manufacturer, mold, plastic, speed, glide, turn, fade, color, notes, type, weight, is_lost) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (manufacturer, mold, plastic, speed, glide, turn, fade, color, notes, disc_type, weight, is_lost))
            mysql.connection.commit()
            cur.close()
            flash('Disc Added Successfully!')
            return redirect(url_for('index'))
        except Exception as e:
            app.logger.error(f"Error adding disc: {e}", exc_info=True)
            flash("Error adding new disc.")
            return redirect(url_for('add_disc'))

    # API call for search results
    search_name = request.args.get('search_name')
    search_results = []
    if search_name:
        api_url = f"{API_BASE_URL}/search_discs_by_name/"
        params = {'name': search_name}
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            search_results = response.json()
        except requests.RequestException as e:
            app.logger.error(f"Error calling external API: {e}", exc_info=True)
            flash("Error retrieving disc information from the API.")

    return render_template('add_disc.html', search_results=search_results)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_disc(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM discs WHERE id = %s", (id,))
        disc = cur.fetchone()
        cur.close()
    except Exception as e:
        app.logger.error(f"Error fetching disc for edit: {e}", exc_info=True)
        flash("Error fetching disc information.")
        return redirect(url_for('index'))

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
        weight = request.form.get('weight', type=float)
        is_lost = request.form.get('is_lost') == 'on'

        try:
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
        except Exception as e:
            app.logger.error(f"Error updating disc: {e}", exc_info=True)
            flash("Error updating disc.")
            return redirect(url_for('edit_disc', id=id))

    return render_template('edit_disc.html', disc=disc)


# Delete disc
@app.route('/delete/<int:id>', methods=['POST'])
def delete_disc(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM discs WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        flash('Disc Deleted Successfully!')
        app.logger.info(f"Disc with ID {id} deleted successfully.")
    except Exception as e:
        app.logger.error(f"Error deleting disc with ID {id}: {e}", exc_info=True)
        flash("Error deleting disc. Please try again.")
        return redirect(url_for('index'))

    return redirect(url_for('index'))


# Mark disc as lost
@app.route('/mark_lost/<int:id>', methods=['POST'])
def mark_lost(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE discs SET is_lost = TRUE WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        flash('Disc Marked as Lost!')
        app.logger.info(f"Disc with ID {id} marked as lost.")
    except Exception as e:
        app.logger.error(f"Error marking disc with ID {id} as lost: {e}", exc_info=True)
        flash("Error marking disc as lost. Please try again.")
        return redirect(url_for('index'))

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)
