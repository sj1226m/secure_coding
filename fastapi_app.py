from fastapi import FastAPI, HTTPException
from typing import List, Optional
import sqlite3

app = FastAPI()

def create_connection():
    conn = sqlite3.connect('shopping_mall.db')
    return conn

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            full_name TEXT,
            address TEXT,
            payment_info TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            price REAL,
            thumbnail_url TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchase_history (
            id INTEGER PRIMARY KEY,
            product_name TEXT,
            purchase_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_name TEXT
        )
    ''')
    conn.commit()

def add_user(conn, username, password, role, full_name, address, payment_info):
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO users (username, password, role, full_name, address, payment_info) VALUES (?, ?, ?, ?, ?, ?)',
                   (username, password, role, full_name, address, payment_info))
    conn.commit()
    user = {"username": username, "password": password, "role": role, "full_name": full_name, "address": address, "payment_info": payment_info}
    return {"message": "User created successfully!", "user": user}

def register_admin(conn, username, password, full_name):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)',
                   (username, password, 'admin', full_name))
    conn.commit()
    user = {"username": username, "password": password, "role": 'admin', "full_name": full_name}
    return {"message": "Admin registered successfully!", "user": user}

def authenticate_user(conn, username, password):
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM users WHERE username = "{username}" AND password = "{password}"')
    user = cursor.fetchone()
    if user:
        user_info = {"username": user[1], "password": user[2], "role": user[3], "full_name": user[4], "address": user[5], "payment_info": user[6]}
        return {"message": f"Welcome back, {username}!", "user": user_info}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

def get_all_products(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    return [{"name": product[1], "category": product[2], "price": product[3], "thumbnail_url": product[4]} for product in products]

# 이름 중복 체크 함수 추가
def check_product_name_exists(conn, name):
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM products WHERE name = ?', (name,))
    result = cursor.fetchone()
    if result[0] > 0:
        return True 
    else:
        return False

# 응답 코드 return 에 추가
def add_product(conn, name, category, price, thumbnail_url):
    if check_product_name_exists(conn, name):
        return {"message": "Product with the same name already exists.", "status_code": 400}

    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (name, category, price, thumbnail_url) VALUES (?, ?, ?, ?)', (name, category, price, thumbnail_url))
    conn.commit()
    return {"message": "Product added successfully!", "status_code": 200}

# 상품 삭제 기능 추가
def delete_product(conn, name):
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE name = ?', (name,))
    conn.commit()
    return {"message": "Product deleted successfully!"}

def update_user_info(conn, username, full_name, address, payment_info):
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET full_name = ?, address = ?, payment_info = ? WHERE username = ?', (full_name, address, payment_info, username))
    conn.commit()
    return {"message": "User information updated successfully!"}

def get_user_by_username(conn, username):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cursor.fetchone()

# 구매 기록 추가
def add_purchase_history(conn, product_name, user_name):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO purchase_history (product_name, user_name) VALUES (?, ?)', (product_name, user_name))
    conn.commit()

# 구매 기록 불러오기
def fetch_purchase_history(conn, user_name):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM purchase_history WHERE user_name = ?', (user_name,))
    purchase_history = cursor.fetchall()
    return [{"product_name": purchase[1], "purchase_time": purchase[2]} for purchase in purchase_history]

@app.on_event("startup")
async def startup_event():
    conn = create_connection()
    create_tables(conn)
    if not get_user_by_username(conn, "admin"):
        register_admin(conn, "admin", "admin", "Admin User")
    conn.close()

@app.get("/register")
async def register_user(username: str, password: str, role: str, full_name: str, address: Optional[str] = None, payment_info: Optional[str] = None):
    conn = create_connection()
    result = add_user(conn, username, password, role, full_name, address, payment_info)
    conn.close()
    return result

@app.get("/login")
async def login(username: str, password: str):
    conn = create_connection()
    result = authenticate_user(conn, username, password)
    conn.close()
    return result

@app.get("/products", response_model=List[dict])
async def get_products():
    conn = create_connection()
    products = get_all_products(conn)
    conn.close()
    return products

# 구매 기록 추가
@app.post("/purchase/{product_name}")
async def purchase_product(product_name: str, user_name: str):
    conn = create_connection()
    add_purchase_history(conn, product_name, user_name) 
    conn.close()
    return {"message": "Purchase history added successfully!"}

# 구매 기록 불러오기
@app.get("/purchase_history/{user_name}", response_model=List[dict])
async def get_purchase_history(user_name: str):
    conn = create_connection()
    purchase_history = fetch_purchase_history(conn, user_name)
    conn.close()
    return purchase_history

@app.get("/add_product")
async def add_new_product(name: str, category: str, price: float, thumbnail_url: str):
    conn = create_connection()
    result = add_product(conn, name, category, price, thumbnail_url)
    conn.close()
    return result

@app.delete("/delete_product/{product_name}")
async def delete_exist_product(product_name: str):
    conn = create_connection()
    result = delete_product(conn, product_name)
    conn.close()
    return result

@app.get("/update_user_info")
async def update_user_info_endpoint(username: str, full_name: str, address: str, payment_info: str):
    conn = create_connection()
    result = update_user_info(conn, username, full_name, address, payment_info)
    conn.close()
    return result
