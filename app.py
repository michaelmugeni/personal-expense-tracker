import matplotlib.pyplot as plt
import os
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from flask import send_file
from openpyxl import Workbook
import tempfile
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)

# Secret key for sessions
app.secret_key = "expense_tracker_secret"


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

        username = request.form['username']
        email = request.form['email']

        password = generate_password_hash(
            request.form['password']
        )

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

            return "Email already exists. Please use another email."

        conn.close()

        return redirect('/login')

    return render_template('register.html')
# ==========================
# LOGIN USER
# ==========================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

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

            return redirect('/dashboard')

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

    query += " ORDER BY expenses.expense_date DESC"

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

        # GENERATE PIE CHART

    labels = []
    amounts = []

    for item in category_totals:
        if item['total'] > 0:
            labels.append(item['name'])
            amounts.append(item['total'])

    if amounts:

        plt.figure(figsize=(6, 6))

        plt.pie(
            amounts,
            labels=labels,
            autopct='%1.1f%%'
        )

        plt.title("Expenses By Category")

        os.makedirs(
            os.path.join('static', 'charts'),
            exist_ok=True
        )

        chart_path = os.path.join(
            'static',
            'charts',
            'expense_pie.png'
        )

        plt.savefig(chart_path)
        plt.close()

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
        category_totals=category_totals
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
        'edit_expense.html',
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


if __name__ == "__main__":
    app.run(debug=True)
