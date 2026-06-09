# SpendWise — Full-Stack Expense Tracker

A production-grade expense tracking app built with **FastAPI + SQLite + JWT Auth** (backend) and **vanilla HTML/JS + Chart.js** (frontend).

---

## Project Structure

```
expense-tracker/
├── backend/
│   ├── main.py           ← FastAPI app (all routes)
│   └── requirements.txt  ← Python dependencies
└── frontend/
    └── index.html        ← Complete frontend (single file)
```

---

## Setup & Run

### 1. Backend (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --port 8000
```

Backend runs at: **http://localhost:8000**
API docs at:     **http://localhost:8000/docs**

---

### 2. Frontend

Just open `frontend/index.html` in your browser — no build step needed!

```bash
# Option 1: Direct open
open frontend/index.html

# Option 2: Simple server
cd frontend
python -m http.server 3000
# Then visit http://localhost:3000
```

---

## Features

| Feature | Description |
|---|---|
| JWT Auth | Register / Login with secure tokens |
| Add Expense | Title, amount, category, date, note |
| Edit/Delete | Full CRUD on all expenses |
| Dashboard | Metrics + line chart + doughnut chart |
| Reports | Bar chart + pie chart + category table |
| CSV Export | Download all expenses as CSV |
| Filter | Filter by category on expenses page |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /auth/register | Create account |
| POST | /auth/login | Get JWT token |
| GET | /auth/me | Current user |
| GET | /expenses | List expenses |
| POST | /expenses | Add expense |
| PUT | /expenses/{id} | Update expense |
| DELETE | /expenses/{id} | Delete expense |
| GET | /expenses/summary | Category totals |

---

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite, passlib (bcrypt), python-jose (JWT)
- **Frontend**: Vanilla HTML/CSS/JS, Chart.js
- **Auth**: JWT Bearer tokens stored in localStorage

---

## Interview Points to Mention

1. REST API design with FastAPI
2. JWT-based authentication & authorization
3. SQLAlchemy ORM with SQLite
4. Password hashing with bcrypt
5. CORS middleware configuration
6. Pydantic data validation
7. Chart.js data visualization
8. CSV export functionality
9. Responsive single-page UI without any framework
