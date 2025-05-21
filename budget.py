import sqlite3
import hashlib
from datetime import datetime
import csv

# Database setup
conn = sqlite3.connect('budget.db')
cursor = conn.cursor()

# Create users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# Create transactions table
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    type TEXT CHECK(type IN ('income', 'expense')) NOT NULL,
    date TEXT NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')
conn.commit()

# --- User Functions ---

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup():
    username = input("Create username: ").strip()
    password = input("Create password: ").strip()
    hashed = hash_password(password)
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn.commit()
        print("✅ Signup successful. You can now log in.\n")
    except sqlite3.IntegrityError:
        print("❌ Username already exists.\n")

def login():
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    hashed = hash_password(password)
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed))
    result = cursor.fetchone()
    if result:
        print(f"✅ Welcome, {username}!\n")
        return result[0]
    else:
        print("❌ Invalid login.\n")
        return None

# --- Budget Functions ---

def add_transaction(user_id):
    try:
        amount = float(input("Amount: ₹"))
        category = input("Category (e.g., Food, Rent): ").strip()
        t_type = input("Type (income/expense): ").strip().lower()
        if t_type not in ['income', 'expense']:
            print("Invalid type.")
            return
        date = input("Date (YYYY-MM-DD) [default: today]: ").strip()
        if not date:
            date = datetime.today().strftime('%Y-%m-%d')
        cursor.execute("INSERT INTO transactions (amount, category, type, date, user_id) VALUES (?, ?, ?, ?, ?)",
                       (amount, category, t_type, date, user_id))
        conn.commit()
        print("✅ Transaction added.\n")
    except Exception as e:
        print("❌ Error:", e)

def view_transactions(user_id):
    print("\nView options: [1] All  [2] By category  [3] By month")
    opt = input("Choose option: ").strip()
    query = "SELECT * FROM transactions WHERE user_id = ?"
    params = [user_id]

    if opt == '2':
        cat = input("Enter category: ").strip()
        query += " AND category = ?"
        params.append(cat)
    elif opt == '3':
        month = input("Enter month (YYYY-MM): ").strip()
        query += " AND strftime('%Y-%m', date) = ?"
        params.append(month)

    cursor.execute(query + " ORDER BY date DESC", tuple(params))
    rows = cursor.fetchall()

    print("\n--- Transactions ---")
    for row in rows:
        print(f"ID: {row[0]} | ₹{row[1]:.2f} | {row[2]} | {row[3]} | {row[4]}")
    print(f"Total: {len(rows)} transactions\n")

def show_balance(user_id):
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'income' AND user_id = ?", (user_id,))
    income = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'expense' AND user_id = ?", (user_id,))
    expense = cursor.fetchone()[0] or 0
    balance = income - expense
    print("\n--- Financial Summary ---")
    print(f"Total Income : ₹{income:.2f}")
    print(f"Total Expense: ₹{expense:.2f}")
    print(f"Current Balance: ₹{balance:.2f}\n")

def export_csv(user_id):
    filename = input("Enter filename (e.g., my_report.csv): ").strip()
    if not filename.endswith('.csv'):
        filename += '.csv'
    cursor.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC", (user_id,))
    rows = cursor.fetchall()
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Amount', 'Category', 'Type', 'Date', 'User ID'])
        writer.writerows(rows)
    print(f"✅ Exported to {filename}\n")

def monthly_report(user_id):
    month = input("Enter month (YYYY-MM): ").strip()
    cursor.execute("""
        SELECT category, type, SUM(amount)
        FROM transactions
        WHERE strftime('%Y-%m', date) = ? AND user_id = ?
        GROUP BY category, type
    """, (month, user_id))
    rows = cursor.fetchall()
    if not rows:
        print("No data for this month.\n")
        return
    print(f"\n--- Report for {month} ---")
    total_income = total_expense = 0
    for cat, t_type, total in rows:
        print(f"{t_type.title()} | {cat:<15} | ₹{total:.2f}")
        if t_type == 'income':
            total_income += total
        else:
            total_expense += total
    print(f"\nTotal Income : ₹{total_income:.2f}")
    print(f"Total Expense: ₹{total_expense:.2f}")
    print(f"Balance      : ₹{total_income - total_expense:.2f}\n")

# --- Main Menu ---

def user_menu(user_id):
    while True:
        print("=== Budget Menu ===")
        print("1. Add Transaction")
        print("2. View Transactions")
        print("3. Show Balance")
        print("4. Monthly Report")
        print("5. Export CSV")
        print("6. Logout")
        choice = input("Select option: ").strip()
        if choice == '1':
            add_transaction(user_id)
        elif choice == '2':
            view_transactions(user_id)
        elif choice == '3':
            show_balance(user_id)
        elif choice == '4':
            monthly_report(user_id)
        elif choice == '5':
            export_csv(user_id)
        elif choice == '6':
            print("🔒 Logged out.\n")
            break
        else:
            print("Invalid choice.\n")

def main():
    while True:
        print("=== Welcome to Budget Tracker ===")
        print("1. Login")
        print("2. Signup")
        print("3. Exit")
        choice = input("Choose an option: ").strip()
        if choice == '1':
            user_id = login()
            if user_id:
                user_menu(user_id)
        elif choice == '2':
            signup()
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid option.\n")

if __name__ == '__main__':
    main()
