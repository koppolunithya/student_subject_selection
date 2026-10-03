# Student Subject Selection System (Flask + SQLite)

## Run in VS Code
```bash
python -m venv venv
venv\Scripts\activate          # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

`database.db` is created automatically with sample data on first run. Delete it to reset.

## Demo logins
- Student: `S101` / `pass123` (also S102 to S105, same password)
- Admin: `admin` / `admin123` (use the same login page)

## How SQLite works here
SQLite is a database stored in one file (`database.db`), accessed through Python's built-in `sqlite3` module, so there's no server to install. `init_db()` creates 3 tables: `students`, `subjects` and `selections` (with foreign keys to both). Selecting a subject inserts a row in `selections` and runs `available_seats - 1`. Removing one deletes the row and adds the seat back. All queries use `?` parameters to prevent SQL injection.

## Greedy algorithm
Students are processed in priority order. Each student's preferences are checked in order, and the first subject with a free seat is allocated. Full subjects are skipped. Time O(S×P), space O(S+M). Try it live at `/algorithm`.

## 1-minute pitch
"Every semester, elective registration turns into chaos: popular subjects overflow and students don't know what's left. Our Student Subject Selection System fixes that. Students log in, search and filter electives, see live seat counts, and select subjects in one click. The system blocks duplicates and full subjects automatically. Admins manage subjects and watch totals from a dashboard. Under the hood we use Flask and SQLite, and for the DAA part we built a greedy allocation algorithm: students are processed by priority and each gets their best available choice in O(S×P) time. It's simple, fair, fast, and easy to explain."
