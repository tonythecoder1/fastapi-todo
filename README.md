A modern Task Management (To-Do) web app built with FastAPI, Async SQLAlchemy, JWT authentication (via cookies), and Chart.js analytics for task visualization.

🚀 Features

✅ User authentication with JWT stored in HTTP-only cookies
✅ Create, edit, and delete tasks
✅ Interactive Kanban board with drag & drop
✅ Real-time statistics with Chart.js (completed vs. pending)
✅ Asynchronous database (PostgreSQL / SQLite)
✅ Middleware authentication guard
✅ Responsive Jinja2 templates with modern CSS

🧩 Tech Stack
Category	Technology
Backend	FastAPI
Database	SQLAlchemy (async)
Auth	JWT via python-jose
Frontend	Jinja2 + jQuery + Interact.js + Chart.js
Server	Uvicorn
ORM	Async SQLAlchemy
Environment	Python 3.12 + Virtualenv
🛠️ Installation Guide
1️⃣ Clone the repository
git clone https://github.com/YourUsername/TodoApp.git
cd TodoApp

2️⃣ Create and activate a virtual environment
python3 -m venv venv


Activate it:

macOS / Linux

source venv/bin/activate


Windows

venv\Scripts\activate

3️⃣ Install dependencies
pip install -r requirements.txt


If you modify dependencies later:

pip freeze > requirements.txt

4️⃣ Create a .env file
SECRET_KEY=your_secure_key_here
ALGORITHM=HS256
DATABASE_URL=postgresql+asyncpg://user:password@localhost/todo_db


For local testing, you can use SQLite:

DATABASE_URL=sqlite+aiosqlite:///./todo.db

5️⃣ Initialize the database

Run this once to create the tables automatically:

uvicorn main:app --reload

🧠 Folder Structure
TodoApp/
│
├── main.py                  # Main FastAPI app + middleware
├── routers/
│   ├── auth.py              # Login, logout, register
│   ├── todos.py             # CRUD for tasks
│   ├── admin.py             # Admin routes
│   └── users.py             # User management
│
├── models.py                # SQLAlchemy models
├── schema.py                # Pydantic schemas
├── database.py              # Async DB configuration
│
├── templates/               # Jinja2 templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── todo.html
│   └── dashboard.html       # Chart.js analytics
│
├── static/
│   ├── css/
│   ├── js/
│   └── img/
│
├── requirements.txt
└── README.md

📊 Chart.js Integration

The dashboard uses Chart.js to visualize completed vs pending tasks:

<canvas id="tasksChart"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
const ctx = document.getElementById('tasksChart');
new Chart(ctx, {
  type: 'doughnut',
  data: {
    labels: ['Completed', 'Pending'],
    datasets: [{
      data: [12, 8],
      backgroundColor: ['#4CAF50', '#FF7043']
    }]
  },
  options: {
    plugins: { legend: { position: 'bottom' } },
  }
});
</script>

🔐 JWT Authentication Flow

The user logs in → a JWT token is generated.

The token is stored in a secure, HTTP-only cookie:

resp.set_cookie(
    key="access_token",
    value=token,
    httponly=True,
    samesite="lax",
    max_age=1800,  # 30 min
    secure=False   # Set to True in production (HTTPS)
)


The middleware validates the token on each request.

If invalid or missing → redirect to /auth/login-page.

⚙️ Authentication Middleware

Defined in main.py:

@app.middleware("http")
async def auth_guard(request: Request, call_next):
    path = request.url.path

    # Public routes
    if path.startswith("/static") or path.startswith("/auth"):
        return await call_next(request)

    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/auth/login-page")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        request.state.user = payload
    except JWTError:
        return RedirectResponse("/auth/login-page")

    return await call_next(request)

🧾 Requirements
fastapi==0.115.0
uvicorn[standard]==0.30.1
sqlalchemy==2.0.34
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
jinja2==3.1.4
asyncpg==0.29.0
pydantic==2.8.2
python-dotenv==1.0.1
chart.js==5.x (via CDN)

🧰 Useful Commands
Action	Command
Install dependencies	pip install -r requirements.txt
Update dependencies	pip freeze > requirements.txt
Run development server	uvicorn main:app --reload
Update pip	pip install --upgrade pip
Exit virtualenv	deactivate
🖼️ Example Screens

Login Page — clean form with JWT cookie auth

Kanban Board — draggable tasks, editable modals

Dashboard — task analytics chart (Chart.js doughnut)

🧑‍💻 Author

Antony Ferreira
🎯 Application Support Engineer & Full-Stack Developer
📧 GitHub: TonyTheCoder1