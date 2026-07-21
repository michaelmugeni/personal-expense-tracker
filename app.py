import matplotlib.pyplot as plt
import os
import csv
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from flask import send_file
from openpyxl import Workbook
import tempfile
from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import timedelta, datetime
import sqlite3
from chatbot import get_bot_response

app = Flask(__name__)

# Secret key for sessions
app.secret_key = "expense_tracker_secret"

# How long a "Remember me" session stays logged in
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# ==========================
# NEW: PROFILE PICTURE UPLOAD CONFIG
# ==========================
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==========================
# HOME PAGE
# ==========================
@app.route('/')
def home():
    return render_template('index.html')

# ==========================
# REGISTER USER
# ==========================
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        username = request.form['username']
        email = request.form['email']
        raw_password = request.form['password']
        confirm_password = request.form.get('confirm_password')

        if confirm_password is not None and raw_password != confirm_password:

            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': 'Passwords do not match.'
                }), 400

            return "Passwords do not match."

        password = generate_password_hash(raw_password)

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO users(username, email, password)
                VALUES (?, ?, ?)
            """, (
                username,
                email,
                password
            ))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': 'Email already exists. Please use another email.'
                }), 409

            return "Email already exists. Please use another email."

        conn.close()

        if is_ajax:
            return jsonify({
                'success': True,
                'redirect': '/login'
            })

        return redirect('/login')

    return render_template('register.html')
# ==========================
# LOGIN USER
# ==========================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')

        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        user = cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user['password'],
            password
        ):

            session['user_id'] = user['id']
            session['username'] = user['username']
            session.permanent = True if remember else False

            if is_ajax:
                return jsonify({
                    'success': True,
                    'redirect': '/dashboard'
                })

            return redirect('/dashboard')

        if is_ajax:
            return jsonify({
                'success': False,
                'message': 'Invalid email or password.'
            }), 401

        return "Invalid Email or Password"

    return render_template('login.html')

# ==========================
# DASHBOARD
# ==========================
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # FILTER CODE
    selected_category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search = request.args.get('search')

    # SORT CODE (additive — defaults reproduce the previous hardcoded behavior)
    sort_by = request.args.get('sort_by', 'date')
    order = request.args.get('order', 'desc')

    query = """
        SELECT expenses.*,
           categories.name AS category_name
        FROM expenses
        LEFT JOIN categories
            ON expenses.category_id = categories.id
        WHERE expenses.user_id = ?
    """

    params = [session['user_id']]

    if selected_category:
       query += " AND categories.id = ?"
       params.append(selected_category)

    if start_date:
       query += " AND expenses.expense_date >= ?"
       params.append(start_date)

    if end_date:
       query += " AND expenses.expense_date <= ?"
       params.append(end_date)

    if search:
       query += """
           AND (
           expenses.description LIKE ?
           OR categories.name LIKE ?
           )
       """
       params.append(f"%{search}%")
       params.append(f"%{search}%")

    sort_columns = {
        'date': 'expenses.expense_date',
        'amount': 'expenses.amount'
    }

    sort_column = sort_columns.get(sort_by, 'expenses.expense_date')
    sort_direction = 'ASC' if order == 'asc' else 'DESC'

    query += f" ORDER BY {sort_column} {sort_direction}"

    expenses = cursor.execute(
       query,
       params
    ).fetchall()

    total_expenses = cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = ?
    """, (
        session['user_id'],
    )).fetchone()[0]
    total_records = cursor.execute("""
        SELECT COUNT(*)
        FROM expenses
        WHERE user_id = ?
    """, (
        session['user_id'],
    )).fetchone()[0]

    highest_expense = cursor.execute("""
    SELECT COALESCE(MAX(amount), 0)
    FROM expenses
    WHERE user_id = ?
    """, (
    session['user_id'],
    )).fetchone()[0]

    total_categories = cursor.execute("""
    SELECT COUNT(*)
    FROM categories
    """).fetchone()[0]

    categories = cursor.execute("""
        SELECT *
        FROM categories
    """).fetchall()

    
    category_totals = cursor.execute("""
        SELECT categories.name,
               COALESCE(SUM(expenses.amount), 0) AS total
        FROM expenses
        LEFT JOIN categories
            ON expenses.category_id = categories.id
        WHERE expenses.user_id = ?
        GROUP BY categories.name
        ORDER BY total DESC
    """, (
        session['user_id'],
    )).fetchall()

    monthly_totals = cursor.execute("""
        SELECT
            strftime('%Y-%m', expense_date) AS month,
            SUM(amount) AS total
        FROM expenses
        WHERE user_id = ?
        GROUP BY month
        ORDER BY month
    """, (
        session['user_id'],
    )).fetchall()
    months = []
    totals = []

    for row in monthly_totals:
       months.append(row['month'])
       totals.append(float(row['total']))

    # MONTHLY TREND CHART

    if totals:

        plt.figure(figsize=(8, 4))

        plt.plot(
            months,
            totals,
            marker='o'
       )

        plt.title("Monthly Spending Trend")
        plt.xlabel("Month")
        plt.ylabel("Amount (KES)")
        plt.grid(True)

        trend_chart_path = os.path.join(
            'static',
            'charts',
            'monthly_trend.png'
        )

        plt.savefig(trend_chart_path)
        plt.close()

    # ==========================
    # NEW: MONTH BUDGET REMAINING
    # ==========================

    current_month_key = datetime.now().strftime('%Y-%m')
    current_month_label = datetime.now().strftime('%B %Y')

    monthly_spending = cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = ?
        AND strftime('%Y-%m', expense_date) = ?
    """, (
        session['user_id'],
        current_month_key
    )).fetchone()[0]

    budget_row = cursor.execute("""
        SELECT monthly_budget
        FROM users
        WHERE id = ?
    """, (
        session['user_id'],
    )).fetchone()

    monthly_budget = budget_row['monthly_budget'] if budget_row and budget_row['monthly_budget'] is not None else 0

    budget_remaining = monthly_budget - monthly_spending

    conn.close()

    return render_template(
        'dashboard.html',
        total_records=total_records,
        highest_expense=highest_expense,
        total_categories=total_categories,
        monthly_totals=monthly_totals,
        expenses=expenses,
        username=session['username'],
        total_expenses=total_expenses,
        categories=categories,
        selected_category=selected_category,
        start_date=start_date,
        end_date=end_date,
        search=search,
        category_totals=category_totals,
        monthly_spending=monthly_spending,
        monthly_budget=monthly_budget,
        budget_remaining=budget_remaining,
        current_month_label=current_month_label,
        sort_by=sort_by,
        order=order
    )
# ==========================
# ADD EXPENSE
# ==========================
@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():

    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':

        category_id = request.form['category_id']
        amount = request.form['amount']
        description = request.form['description']
        expense_date = request.form['expense_date']

        cursor.execute("""
            INSERT INTO expenses(
                user_id,
                category_id,
                amount,
                description,
                expense_date
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            session['user_id'],
            category_id,
            amount,
            description,
            expense_date
        ))

        conn.commit()
        conn.close()

        return redirect('/dashboard')

    categories = cursor.execute(
        "SELECT * FROM categories"
    ).fetchall()

    conn.close()

    return render_template(
        'add_expense.html',
        categories=categories
    )

@app.route('/edit_expense/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    if request.method == 'POST':

        amount = request.form['amount']
        description = request.form['description']
        expense_date = request.form['expense_date']

        cursor.execute("""
            UPDATE expenses
            SET amount=?,
                description=?,
                expense_date=?
            WHERE id=?
            AND user_id=?
        """, (
            amount,
            description,
            expense_date,
            id,
            session['user_id']
        ))

        conn.commit()
        conn.close()

        return redirect('/dashboard')

    expense = cursor.execute("""
        SELECT *
        FROM expenses
        WHERE id=?
        AND user_id=?
    """, (
        id,
        session['user_id']
    )).fetchone()

    conn.close()

    return render_template(
        'edit_expenses.html',
        expense=expense
    )

@app.route('/delete_expense/<int:id>')
def delete_expense(id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM expenses
        WHERE id=?
        AND user_id=?
    """, (
        id,
        session['user_id']
    ))

    conn.commit()
    conn.close()

    return redirect('/dashboard')

@app.route('/summary')
def summary():

    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    summary = cursor.execute("""
        SELECT
            categories.name AS category_name,
            SUM(expenses.amount) AS total
        FROM expenses
        JOIN categories
            ON expenses.category_id = categories.id
        WHERE expenses.user_id = ?
        GROUP BY categories.name
        ORDER BY total DESC
    """, (
        session['user_id'],
    )).fetchall()

    total_spent = cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = ?
    """, (
        session['user_id'],
    )).fetchone()[0]

    chart_labels = []
    chart_values = []

    for item in summary:
        chart_labels.append(item['category_name'])
        chart_values.append(item['total'])

    conn.close()

    return render_template(
        'summary.html',
        summary=summary,
        total_spent=total_spent,
        chart_labels=chart_labels,
        chart_values=chart_values
    )
# ==========================
# LOGOUT
# ==========================
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

# ==========================
# NEW: UPDATE MONTHLY BUDGET
# ==========================
@app.route('/update_budget', methods=['POST'])
def update_budget():

    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in.'}), 401

    monthly_budget = request.form.get('monthly_budget')

    if monthly_budget is None:
        data = request.get_json(silent=True) or {}
        monthly_budget = data.get('monthly_budget')

    try:
        monthly_budget = float(monthly_budget)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid budget amount.'}), 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET monthly_budget = ?
        WHERE id = ?
    """, (
        monthly_budget,
        session['user_id']
    ))

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'monthly_budget': monthly_budget
    })

# ==========================
# NEW: PROFILE PAGE
# ==========================
@app.route('/profile')
def profile():

    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    user = cursor.execute("""
        SELECT id, username, email, monthly_budget, profile_pic
        FROM users
        WHERE id = ?
    """, (
        session['user_id'],
    )).fetchone()

    total_records = cursor.execute("""
        SELECT COUNT(*)
        FROM expenses
        WHERE user_id = ?
    """, (
        session['user_id'],
    )).fetchone()[0]

    conn.close()

    return render_template(
        'profile.html',
        user=user,
        total_records=total_records
    )

# ==========================
# NEW: UPDATE PROFILE (username / email / profile picture)
# ==========================
@app.route('/update_profile', methods=['POST'])
def update_profile():

    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in.'}), 401

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()

    if not username or not email:
        return jsonify({
            'success': False,
            'message': 'Username and email are required.'
        }), 400

    profile_pic_path = None
    uploaded_file = request.files.get('profile_pic')

    if uploaded_file and uploaded_file.filename:

        if not allowed_file(uploaded_file.filename):
            return jsonify({
                'success': False,
                'message': 'Only PNG, JPG, GIF, or WEBP images are allowed.'
            }), 400

        ext = uploaded_file.filename.rsplit('.', 1)[1].lower()
        safe_name = secure_filename(
            f"user_{session['user_id']}_{int(datetime.now().timestamp())}.{ext}"
        )
        uploaded_file.save(os.path.join(UPLOAD_FOLDER, safe_name))
        profile_pic_path = f"uploads/{safe_name}"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:

        if profile_pic_path:

            cursor.execute("""
                UPDATE users
                SET username = ?,
                    email = ?,
                    profile_pic = ?
                WHERE id = ?
            """, (
                username,
                email,
                profile_pic_path,
                session['user_id']
            ))

        else:

            cursor.execute("""
                UPDATE users
                SET username = ?,
                    email = ?
                WHERE id = ?
            """, (
                username,
                email,
                session['user_id']
            ))

        conn.commit()

    except sqlite3.IntegrityError:

        conn.close()

        return jsonify({
            'success': False,
            'message': 'That email is already in use by another account.'
        }), 409

    conn.close()

    # Keep session username in sync since the sidebar/topbar display it
    session['username'] = username

    response = {
        'success': True,
        'username': username,
        'email': email
    }

    if profile_pic_path:
        response['profile_pic'] = profile_pic_path

    return jsonify(response)

# ==========================
# RUN APP
# ==========================
@app.route('/export_excel')
def export_excel():

    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    expenses = cursor.execute("""
        SELECT expenses.id,
               categories.name AS category_name,
               expenses.amount,
               expenses.description,
               expenses.expense_date
        FROM expenses
        LEFT JOIN categories
            ON expenses.category_id = categories.id
        WHERE expenses.user_id = ?
        ORDER BY expenses.expense_date DESC
    """, (
        session['user_id'],
    )).fetchall()

    wb = Workbook()
    ws = wb.active

    ws.title = "Expenses"

    ws.append([
        "ID",
        "Category",
        "Amount",
        "Description",
        "Date"
    ])

    for expense in expenses:

        ws.append([
            expense['id'],
            expense['category_name'],
            expense['amount'],
            expense['description'],
            expense['expense_date']
        ])

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".xlsx"
    )

    wb.save(temp_file.name)

    conn.close()

    return send_file(
        temp_file.name,
        as_attachment=True,
        download_name="expenses.xlsx"
    )
@app.route('/export_pdf')
def export_pdf():

    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    expenses = cursor.execute("""
        SELECT expenses.id,
               categories.name AS category_name,
               expenses.amount,
               expenses.description,
               expenses.expense_date
        FROM expenses
        LEFT JOIN categories
            ON expenses.category_id = categories.id
        WHERE expenses.user_id = ?
        ORDER BY expenses.expense_date DESC
    """, (
        session['user_id'],
    )).fetchall()

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    pdf = SimpleDocTemplate(temp_file.name)

    data = [
        ["ID", "Category", "Amount", "Description", "Date"]
    ]

    for expense in expenses:
        data.append([
            expense['id'],
            expense['category_name'],
            str(expense['amount']),
            expense['description'],
            str(expense['expense_date'])
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    pdf.build([table])

    conn.close()

    return send_file(
        temp_file.name,
        as_attachment=True,
        download_name="expense_report.pdf"
    )

# ==========================
# NEW: EXPORT CSV
# ==========================
@app.route('/export_csv')
def export_csv():

    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    expenses = cursor.execute("""
        SELECT expenses.id,
               categories.name AS category_name,
               expenses.amount,
               expenses.description,
               expenses.expense_date
        FROM expenses
        LEFT JOIN categories
            ON expenses.category_id = categories.id
        WHERE expenses.user_id = ?
        ORDER BY expenses.expense_date DESC
    """, (
        session['user_id'],
    )).fetchall()

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".csv",
        mode='w',
        newline='',
        encoding='utf-8'
    )

    writer = csv.writer(temp_file)

    writer.writerow(["ID", "Category", "Amount", "Description", "Date"])

    for expense in expenses:
        writer.writerow([
            expense['id'],
            expense['category_name'],
            expense['amount'],
            expense['description'],
            expense['expense_date']
        ])

    temp_file.close()

    conn.close()

    return send_file(
        temp_file.name,
        as_attachment=True,
        download_name="expenses.csv"
    )


# ==========================
# NEW: CHATBOT ASSISTANT
# ==========================
@app.route('/chatbot', methods=['POST'])
def chatbot():

    if 'user_id' not in session:
        return jsonify({
            'reply': "Please log in first so I can help you with your account."
        }), 401

    data = request.get_json(silent=True) or {}
    message = data.get('message', '')

    reply = get_bot_response(message)

    return jsonify({'reply': reply})


if __name__ == "__main__":
    app.run(debug=True)