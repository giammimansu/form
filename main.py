from flask import Flask, request, redirect, url_for, render_template_string, flash

app = Flask(__name__)
app.secret_key = "change-me-please"  # Necessario per i messaggi flash

# Eventi configurati
EVENTS = [
    {"id": "mar_avigliano", "label": "Martedì Avigliano"},
    {"id": "gio_avigliano", "label": "Giovedì Avigliano"},
    {"id": "ven_prati", "label": "Venerdì Prati"},
    {"id": "sab_giammi", "label": "Sabato Compleanno Giammi"},
]


# Configurazione database PostgreSQL
import psycopg2
import os
DB_HOST = os.environ.get("DB_HOST", "dpg-d2diqdggjchc73dq0e1g-a")
DB_NAME = os.environ.get("DB_NAME", "form_db_7xzo")
DB_USER = os.environ.get("DB_USER", "form_db_7xzo_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "sZj2g8N6TGu3FrfVtQNfO9PyAn37WIq0")

def get_db_connection():
  conn = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
  )
  return conn

# Inizializza la tabella se non esiste
def init_db():
  conn = get_db_connection()
  cur = conn.cursor()
  cur.execute('''
    CREATE TABLE IF NOT EXISTS submissions (
      id SERIAL PRIMARY KEY,
      name TEXT NOT NULL,
      events TEXT NOT NULL,
      bringing_others BOOLEAN NOT NULL,
      extra_people INTEGER,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  ''')
  conn.commit()
  cur.close()
  conn.close()

init_db()

BASE_HTML = """
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Iscrizione Eventi</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background: #f6f7fb; }
    .card { border: 0; box-shadow: 0 10px 25px rgba(0,0,0,.06); border-radius: 1rem; }
    .form-check { margin-bottom: .35rem; }
  </style>
</head>
<body>
<nav class="navbar navbar-light bg-white border-bottom mb-4">
  <div class="container">
    <a class="navbar-brand" href="{{ url_for('index') }}">📅 Iscrizione Eventi</a>
    <a class="btn btn-outline-secondary" href="{{ url_for('iscritti') }}">Vedi iscritti</a>
  </div>
</nav>
<div class="container">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      {% for category, message in messages %}
        <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
          {{ message }}
          <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
      {% endfor %}
    {% endif %}
  {% endwith %}
  {% block content %}{% endblock %}
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
  // Abilita/disabilita input numero in base al checkbox
  function toggleNumeroPersone() {
    const cb = document.getElementById('bringing_others');
    const num = document.getElementById('extra_people');
    num.disabled = !cb.checked;
    if (!cb.checked) { num.value = ''; }
  }
  document.addEventListener('DOMContentLoaded', toggleNumeroPersone);
</script>
</body>
</html>
"""

FORM_HTML = """
{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-12 col-lg-8">
    <div class="card p-4">
      <h1 class="h3 mb-3">Partecipa agli eventi</h1>
      <p class="text-secondary">Compila il modulo per indicare a quali eventi verrai e se porti altre persone.</p>
      <form method="post" novalidate>
        <div class="mb-3">
          <label for="name" class="form-label">Il tuo nome*</label>
          <input type="text" class="form-control" id="name" name="name" placeholder="Es. Giammi" required value="{{ request.form.get('name','') }}">
        </div>

        <div class="mb-3">
          <label class="form-label">Seleziona gli eventi a cui partecipi*</label>
          {% for ev in events %}
            <div class="form-check">
              <input class="form-check-input" type="checkbox" name="events" id="{{ ev.id }}" value="{{ ev.label }}" {% if ev.label in (request.form.getlist('events') or []) %}checked{% endif %}>
              <label class="form-check-label" for="{{ ev.id }}">{{ ev.label }}</label>
            </div>
          {% endfor %}
        </div>

        <div class="mb-3">
          <div class="form-check form-switch">
            <input class="form-check-input" type="checkbox" role="switch" id="bringing_others" name="bringing_others" onchange="toggleNumeroPersone()" {% if request.form.get('bringing_others') %}checked{% endif %}>
            <label class="form-check-label" for="bringing_others">Porto altre persone con me</label>
          </div>
        </div>

        <div class="mb-3">
          <label for="extra_people" class="form-label">Quante persone in più?</label>
          <input type="number" class="form-control" id="extra_people" name="extra_people" min="1" step="1" placeholder="Es. 2" value="{{ request.form.get('extra_people','') }}">
          <div class="form-text">Compila solo se sopra è attivo. Deve essere un numero intero ≥ 1.</div>
        </div>

        <button class="btn btn-primary">Invia</button>
      </form>
    </div>
  </div>
</div>
{% endblock %}
"""

GRAZIE_HTML = """
{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-12 col-lg-8">
    <div class="card p-4 text-center">
      <h1 class="h3">Grazie, {{ submission.name }}! 🎉</h1>
      <p class="mb-2">Hai confermato la partecipazione ai seguenti eventi:</p>
      <ul class="list-group text-start mb-3">
        {% for e in submission.events %}
          <li class="list-group-item">{{ e }}</li>
        {% endfor %}
      </ul>
      {% if submission.bringing_others %}
        <p>Inoltre porterai <strong>{{ submission.extra_people }}</strong> persona/e in più.</p>
      {% else %}
        <p>Hai indicato che verrai da solo/a.</p>
      {% endif %}
      <a href="{{ url_for('index') }}" class="btn btn-outline-primary mt-3">Compila un altro modulo</a>
    </div>
  </div>
</div>
{% endblock %}
"""

ISCRITTI_HTML = """
{% extends "base.html" %}
{% block content %}
<div class="row">
  <div class="col-12">
    <div class="card p-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="h4 m-0">Iscritti</h1>
        <a href="{{ url_for('index') }}" class="btn btn-sm btn-secondary">Nuova iscrizione</a>
      </div>
      {% if submissions %}
        <div class="table-responsive">
          <table class="table table-striped align-middle">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Eventi</th>
                <th>Altre persone</th>
                <th>Numero</th>
                <th>Data/ora</th>
              </tr>
            </thead>
            <tbody>
              {% for s in submissions %}
                <tr>
                  <td>{{ s.name }}</td>
                  <td>
                    <ul class="m-0 ps-3">
                      {% for e in s.events %}<li>{{ e }}</li>{% endfor %}
                    </ul>
                  </td>
                  <td>{{ 'Sì' if s.bringing_others else 'No' }}</td>
                  <td>{{ s.extra_people if s.bringing_others else '-' }}</td>
                  <td>{{ s.created_at }}</td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      {% else %}
        <p class="text-secondary">Ancora nessuna iscrizione.</p>
      {% endif %}
    </div>
  </div>
</div>
{% endblock %}
"""

# Registra i template in memoria (senza file .html separati)
from jinja2 import DictLoader
app.jinja_loader = DictLoader({
    'base.html': BASE_HTML,
    'form.html': FORM_HTML,
    'grazie.html': GRAZIE_HTML,
    'iscritti.html': ISCRITTI_HTML,
})

from datetime import datetime
from dataclasses import dataclass
from typing import List

@dataclass
class Submission:
    name: str
    events: List[str]
    bringing_others: bool
    extra_people: int
    created_at: str


def validate_form(form):
    name = (form.get('name') or '').strip()
    selected_events = form.getlist('events')
    bringing_others = form.get('bringing_others') is not None
    extra_people_raw = form.get('extra_people')

    errors = []

    if not name:
        errors.append("Il nome è obbligatorio.")

    if not selected_events:
        errors.append("Seleziona almeno un evento.")

    extra_people = 0
    if bringing_others:
        if not extra_people_raw:
            errors.append("Indica quante persone in più porti.")
        else:
            try:
                extra_people = int(extra_people_raw)
                if extra_people < 1:
                    errors.append("Il numero di persone in più deve essere almeno 1.")
            except ValueError:
                errors.append("Il numero di persone in più deve essere un intero valido.")

    return {
        'valid': len(errors) == 0,
        'data': {
            'name': name,
            'events': selected_events,
            'bringing_others': bringing_others,
            'extra_people': extra_people,
        },
        'errors': errors,
    }



@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == 'POST':
    result = validate_form(request.form)
    if result['valid']:
      conn = get_db_connection()
      cur = conn.cursor()
      cur.execute(
        """
        INSERT INTO submissions (name, events, bringing_others, extra_people)
        VALUES (%s, %s, %s, %s) RETURNING id
        """,
        (
          result['data']['name'],
          ','.join(result['data']['events']),
          result['data']['bringing_others'],
          result['data']['extra_people'] if result['data']['bringing_others'] else None
        )
      )
      new_id = cur.fetchone()[0]
      conn.commit()
      cur.close()
      conn.close()
      return redirect(url_for('grazie', sub_id=new_id))
    else:
      for e in result['errors']:
        flash(e, 'danger')
  return render_template_string(app.jinja_env.get_template('form.html').render(events=EVENTS))



@app.route('/grazie/<int:sub_id>')
def grazie(sub_id):
  conn = get_db_connection()
  cur = conn.cursor()
  cur.execute("SELECT name, events, bringing_others, extra_people, created_at FROM submissions WHERE id = %s", (sub_id,))
  row = cur.fetchone()
  cur.close()
  conn.close()
  if row:
    submission = Submission(
      name=row[0],
      events=row[1].split(','),
      bringing_others=row[2],
      extra_people=row[3] if row[2] else 0,
      created_at=row[4].strftime('%Y-%m-%d %H:%M:%S')
    )
    return render_template_string(app.jinja_env.get_template('grazie.html').render(submission=submission))
  flash('Iscrizione non trovata.', 'warning')
  return redirect(url_for('index'))



@app.route('/iscritti')
def iscritti():
  conn = get_db_connection()
  cur = conn.cursor()
  cur.execute("SELECT name, events, bringing_others, extra_people, created_at FROM submissions ORDER BY created_at DESC")
  rows = cur.fetchall()
  cur.close()
  conn.close()
  submissions = [
    Submission(
      name=row[0],
      events=row[1].split(','),
      bringing_others=row[2],
      extra_people=row[3] if row[2] else 0,
      created_at=row[4].strftime('%Y-%m-%d %H:%M:%S')
    ) for row in rows
  ]
  return render_template_string(app.jinja_env.get_template('iscritti.html').render(submissions=submissions))


if __name__ == '__main__':
    # Avvia il server di sviluppo
    app.run(debug=True, host='0.0.0.0', port=5000)
