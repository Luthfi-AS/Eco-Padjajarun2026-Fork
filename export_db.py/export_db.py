import sqlite3
import pandas as pd


conn = sqlite3.connect("db.sqlite3")

tables = pd.read_sql_query(
    "SELECT name FROM sqlite_master WHERE type='table';",
    conn
)

print(tables)

orders = pd.read_sql_query(
    "SELECT * FROM tickets_order",
    conn
)

orders.to_csv("tickets_order.csv", index=False)


users = pd.read_sql_query(
    "SELECT * FROM auth_user",
    conn
)

users.to_csv("users.csv", index=False)

tickets = pd.read_sql_query(
    "SELECT * FROM tickets_ticketcategory",
    conn
)

tickets.to_csv("ticket_categories.csv", index=False)

print("Export CSV berhasil!")