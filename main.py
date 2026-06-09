from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import date, datetime, timedelta
from typing import Optional, List
import os
 
# ── Config ──────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "changeme-super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

DATABASE_URL = "sqlite:///./expense_tracker.db"

# ── DB Setup ─────────────────────────────────────────────
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ── Models ───────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email    = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Expense(Base):
    __tablename__ = "expenses"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"))
    title       = Column(String)
    amount      = Column(Float)
    category    = Column(String)
    date        = Column(Date)
    note        = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

# ── Security ─────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ── Pydantic Schemas ─────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    class Config: orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ExpenseCreate(BaseModel):
    title: str
    amount: float
    category: str
    date: date
    note: Optional[str] = None

class ExpenseOut(ExpenseCreate):
    id: int
    user_id: int
    class Config: orm_mode = True

class ExpenseSummary(BaseModel):
    category: str
    total: float

# ── DB Dependency ─────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# ── App ───────────────────────────────────────────────────
app = FastAPI(title="Expense Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ── Auth Routes ───────────────────────────────────────────
@app.post("/auth/register", response_model=UserOut, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user

# ── Expense Routes ────────────────────────────────────────
@app.get("/expenses", response_model=List[ExpenseOut])
def list_expenses(
    category: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Expense).filter(Expense.user_id == current_user.id)
    if category:
        q = q.filter(Expense.category == category)
    if month:
        q = q.filter(Expense.date.month == month)
    if year:
        q = q.filter(Expense.date.year == year)
    return q.order_by(Expense.date.desc()).all()

@app.post("/expenses", response_model=ExpenseOut, status_code=201)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_expense = Expense(**expense.dict(), user_id=current_user.id)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.put("/expenses/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int,
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_expense = db.query(Expense).filter(
        Expense.id == expense_id, Expense.user_id == current_user.id
    ).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    for key, val in expense.dict().items():
        setattr(db_expense, key, val)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_expense = db.query(Expense).filter(
        Expense.id == expense_id, Expense.user_id == current_user.id
    ).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(db_expense)
    db.commit()

@app.get("/expenses/summary", response_model=List[ExpenseSummary])
def expense_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import func
    results = db.query(
        Expense.category,
        func.sum(Expense.amount).label("total")
    ).filter(Expense.user_id == current_user.id).group_by(Expense.category).all()
    return [{"category": r[0], "total": round(r[1], 2)} for r in results]

@app.get("/")
def root():
    return {"message": "Expense Tracker API is running!"}
