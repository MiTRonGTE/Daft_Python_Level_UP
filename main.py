# pytest tests.py
# http://127.0.0.1:8000
# uvicorn main:app

from fastapi import FastAPI, HTTPException, Request, Response,  status, Cookie, Depends
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from datetime import timedelta, date
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import hashlib
import string
import secrets
import random
import sqlite3

app = FastAPI()

app.counter = 0
app.id = 0

app.patient_id = {}


class RegisterCovid19(BaseModel):
    name: str
    surname: str


class Categories_item(BaseModel):
    name: str


def try_id_cat(try_id):
    app.db_connection.row_factory = sqlite3.Row
    id_exist = app.db_connection.execute(
        "SELECT 1 FROM Categories WHERE CategoryId = ?", (try_id,)
    ).fetchone()
    if not id_exist:
        raise HTTPException(status_code=404)


@app.api_route(path="/method", methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"], status_code=200)
def read_request(request: Request, response: Response):
    request_method = request.method

    if request_method == "POST":
        response.status_code = status.HTTP_201_CREATED

    return {"method": request_method}


@app.get("/auth")
def check_password(password: str = '', password_hash: str = ''):
    if password == '' or password_hash == '':
        return HTMLResponse(status_code=401)

    password = password.encode('ascii')
    password_try_hash = hashlib.sha512(password).hexdigest()

    if str(password_try_hash) == str(password_hash):
        raise HTTPException(status_code=204)
    else:
        return HTMLResponse(status_code=401)


@app.post("/register")
def register(registercovid19: RegisterCovid19):
    app.id += 1
    register_date = date.today()
    alpha = string.ascii_letters
    name = ''

    for i in registercovid19.name:
        if i in alpha or i in "ńŃśŚćĆóÓżŻźŹęĘąĄłŁ":
            name += i
        else:
            pass

    surname = ''
    for i in registercovid19.surname:
        if i in alpha or i in "ńŃśŚćĆóÓżŻźŹęĘąĄłŁ":
            surname += i
        else:
            pass

    data_vac = date.today() + timedelta(days=len(name)+len(surname))
    item = {"id": app.id,
            "name": registercovid19.name,
            "surname": registercovid19.surname,
            "register_date": str(register_date),
            "vaccination_date": str(data_vac)
            }
    app.patient_id[app.id] = item
    return JSONResponse(status_code=201, content=item)


@app.get("/patient/{id}")
def register_return(reg_id):
    try:
        id_keys = app.patient_id.keys()
        if int(reg_id) in id_keys:
            item = app.patient_id[int(reg_id)]
            return JSONResponse(status_code=200, content=item)
        elif int(reg_id) < 1:
            return HTMLResponse(status_code=400)
        else:
            return HTMLResponse(status_code=404)
    except:
        return HTMLResponse(status_code=404)


@app.get("/hello", response_class=HTMLResponse)
def hello_and_date():
    date_today = date.today()
    return f"""
    <html>
        <head>
        </head>
        <body>
            <h1>Hello! Today date is {date_today}</h1>
        </body>
    </html>
    """


# 3.1
security = HTTPBasic()

app.login_session_last = []
app.login_token_last = []

random.seed(1)


@app.post("/login_session", status_code=201)
def login_session(response: Response,
                  credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "4dm1n")
    correct_password = secrets.compare_digest(credentials.password, "NotSoSecurePa$$")
    if not(correct_password and correct_username):
        raise HTTPException(status_code=401)
    secret_key = str(random.randint(0, 100))
    session_token = hashlib.sha256(f"{credentials.username} + {credentials.password} + {secret_key}".encode()).hexdigest()
    if len(app.login_session_last) >= 3:
        app.login_session_last.pop(0)
    response.set_cookie(key="session_token", value=session_token)
    app.login_session_last.append(session_token)
    return "sesja aktywna"


@app.post("/login_token", status_code=201)
def login_token(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "4dm1n")
    correct_password = secrets.compare_digest(credentials.password, "NotSoSecurePa$$")
    if not(correct_password and correct_username):
        raise HTTPException(status_code=401)
    secret_key = str(random.randint(0, 100))
    session_token = hashlib.sha256(f"{credentials.username} + {credentials.password} + {secret_key}".encode()).hexdigest()
    if len(app.login_token_last) >= 3:
        app.login_token_last.pop(0)
    app.login_token_last.append(session_token)
    return {"token": session_token}


# 3.2
@app.get("/welcome_session")
def welcome_session(format: str = '', session_token=Cookie(None)):
    if session_token not in app.login_session_last:
        return HTMLResponse(status_code=401)
    else:
        if format == 'json':
            item = {"message": "Welcome!"}
            return JSONResponse(status_code=200, content=item)

        elif format == 'html':
            return HTMLResponse(status_code=200, content=f"""
        <html>
            <head>
            </head>
            <body>
                <h1>Welcome!</h1>
            </body>
        </html>
        """)
        else:
            return PlainTextResponse(status_code=200, content="Welcome!")


@app.get('/welcome_token')
def welcome_token(token: str = '', format: str = ''):
    if token not in app.login_token_last or token == '':
        return HTMLResponse(status_code=401)
    else:
        if format == 'json':
            item = {"message": "Welcome!"}
            return JSONResponse(status_code=200, content=item)

        elif format == 'html':
            return HTMLResponse(status_code=200, content=f"""
    <html>
        <head>
        </head>
        <body>
            <h1>Welcome!</h1>
        </body>
    </html>
    """)
        else:
            return PlainTextResponse(status_code=200, content="Welcome!")


# 3.4
@app.delete('/logout_session')
def logout_session(format: str = '', session_token: str = Cookie(None)):
    if session_token not in app.login_session_last:
        return HTMLResponse(status_code=401)
    else:
        app.login_session_last.remove(session_token)
        url = '/logged_out?format=' + format
        return RedirectResponse(status_code=302, url=url)


@app.delete('/logout_token')
def logout_tokenn(format: str = '', token: str = ''):
    if token not in app.login_token_last or token == '':
        return HTMLResponse(status_code=401)
    else:
        app.login_token_last.remove(token)
        url = '/logged_out?format=' + format
        return RedirectResponse(status_code=302, url=url)


@app.get('/logged_out')
def logged_out(format: str = ''):
    if format == 'json':
        return JSONResponse(status_code=200, content={"message": "Logged out!"})
    elif format == 'html':
        return HTMLResponse(status_code=200, content=f"""
            <html>
                <head>
                </head>
                <body>
                    <h1>Logged out!</h1>
                </body>
            </html>
            """)
    else:
        return PlainTextResponse(status_code=200, content='Logged out!')


# 4
@app.on_event("startup")
async def startup():
    app.db_connection = sqlite3.connect("northwind.db")
    app.db_connection.text_factory = lambda b: b.decode(errors="ignore")  # northwind specific


@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()


# 4.1
@app.get("/categories", status_code=200)
async def categories():
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute('''
        SELECT CategoryID, CategoryName FROM Categories ORDER BY CategoryID
        ''').fetchall()
    return {"categories": [{"id": x['CategoryID'], "name": x["CategoryName"]} for x in data]}


@app.get("/customers", status_code=200)
async def customers():
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute('''
    SELECT CustomerID, CompanyName, COALESCE(Address, '') || ' ' || COALESCE(PostalCode, '') || ' ' || COALESCE(City, '') || ' ' || COALESCE(Country, '') AS full_address FROM Customers ORDER BY UPPER(CustomerID)
    ''').fetchall()
    item = {"customers": []}
    for x in data:
        item["customers"].append({"id": x["CustomerID"], "name": x["CompanyName"], "full_address": x["full_address"]})
    return JSONResponse(content=item)


# 4.2
@app.get("/products/{prod_id}", status_code=200)
async def produckt_id(prod_id: int):
    try:
        app.db_connection.row_factory = sqlite3.Row
        data = app.db_connection.execute(
            "SELECT ProductName FROM Products WHERE ProductID = :product_id",
            {'product_id': prod_id}).fetchone()
        item = {"id": id, "name": data[0]}
        return JSONResponse(content=item)
    except:
        raise HTTPException(status_code=404)


# 4.3
@app.get("/employees", status_code=200)
async def employees(limit='', offset='', order=''):
    if limit == '':
        limit = 1
    if offset == '':
        offset = 0
    if order == '':
        order = "EmployeeID"

    if order != "first_name" and order != "last_name" and order != "city" and order != "EmployeeID":
        raise HTTPException(status_code=400)
    else:
        if order == "first_name":
            order = "FirstName"
        if order == "last_name":
            order = "LastName"
        if order == "city":
            order = "City"

        app.db_connection.row_factory = sqlite3.Row
        data = app.db_connection.execute(
            f"SELECT EmployeeID, LastName, FirstName, City FROM Employees ORDER BY ? LIMIT ? OFFSET ?",
            (order, str(limit), str(offset), )).fetchall()
        item = {"employees": []}
        for x in data:
            item["employees"].append({"id": x["EmployeeID"], "last_name": x["LastName"], "first_name": x["FirstName"], "city": x["City"]})
        return JSONResponse(content=item)


# 4.4
@app.get("/products_extended", status_code=200)
async def products_extended():
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute('''
    SELECT Products.ProductID id, Products.ProductName name, Categories.CategoryName category, Suppliers.CompanyName supplier FROM Products 
    JOIN Categories ON Products.CategoryID = Categories.CategoryID JOIN Suppliers ON Products.SupplierID = Suppliers.SupplierID ORDER BY Products.ProductID
    ''').fetchall()
    return {"products_extended": [{"id": x["id"], "name": x["name"], "category": x["category"], "supplier": x["supplier"]} for x in data]}


# 4.5
@app.get('/products/{id}/orders', status_code=200)
async def products_id_orders(prod_id: int):
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute('''
    SELECT Products.ProductID, Orders.OrderID id, Customers.CompanyName customer, [Order Details].Quantity quantity, [Order Details].UnitPrice unitprice, [Order Details].Discount discount 
    FROM Products JOIN [Order Details] ON Products.ProductID = [Order Details].ProductID JOIN Orders ON [Order Details].OrderID = Orders.OrderID JOIN Customers ON Orders.CustomerID = Customers.CustomerID WHERE Products.ProductID = ? ORDER BY Orders.OrderID
    ''', (prod_id, )).fetchall()
    if not data:
        raise HTTPException(status_code=404)
    return {"orders": [{"id": x["id"], "customer": x["customer"], "quantity": x["quantity"], "total_price": round(((x['unitprice'] * x['quantity']) - (x['discount'] * (x['unitprice'] * x['quantity']))), 2)} for x in data]}


# 4.6
@app.post("/categories", status_code=201)
async def post_categories(categories: Categories_item):
    cursor = app.db_connection.execute(
        """INSERT INTO Categories (CategoryName) VALUES (?)""", (categories.name,)
    )
    app.db_connection.commit()
    new_id = cursor.lastrowid
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute(
        """SELECT CategoryId id, CategoryName name FROM categories WHERE CategoryId = ?""", (new_id,)).fetchone()
    return data


@app.put("/categories/{cat_id}", status_code=200)
async def category_update(category: Categories_item, cat_id: int):
    try_id_cat(cat_id)
    cursor = app.db_connection.execute(
        """UPDATE Categories SET CategoryName = ? WHERE CategoryId = ?""", (category.name, cat_id)
    )
    app.db_connection.commit()
    data = app.db_connection.execute(
        """SELECT CategoryId id, CategoryName name FROM categories WHERE CategoryId = ?""",
        (cat_id,)).fetchone()
    return data


@app.delete("/categories/{cat_id}", status_code=200)
async def category_delete(cat_id: int):
    try_id_cat(cat_id)
    cursor = app.db_connection.execute(
        """DELETE FROM Categories WHERE CategoryId = ?""", (cat_id,)
    )
    app.db_connection.commit()
    return {"deleted": cursor.rowcount}

@app.get("/suppliers", status_code=200)
async def suppliers_def():
    app.db_connection.commit()
    data = app.db_connection.execute(
        """SELECT SupplierID, CompanyName FROM Suppliers ORDER BY SupplierID""").fetchall()
    item = []
    for x in data:
        item.append({"SupplierID": x[0], "CompanyName": x[1]})
    return item
