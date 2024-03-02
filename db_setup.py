""" 
================================================
Title:  db_setup.py
Authors: Abdullah Mahith and Shahbaj Mukul
Description: Database setup for the stock trading system.
================================================
 """

import sqlite3

connection = sqlite3.connect('stock_trading.db')

cursor = connection.cursor()

# StockMarket table to store all the stocks available in the market for people to buy. 
# This does not keep track of the stocks bought by the users, but only the stocks available in the market for them to buy
# A stock MSUT be present in this table for a user to buy it.
# This is easier to manage and keep track of the stocks available in the market.
cursor.execute('''CREATE TABLE IF NOT EXISTS StockMarket (
               stock_symbol VARCHAR(4) PRIMARY KEY,
                stock_name VARCHAR(20) NOT NULL,
                stock_price DOUBLE NOT NULL)'''
)

# Stocks table to keep track of the stocks bought by the users.
# This table has a foreign key to the Users table to keep track of the user who bought the stock.
# Meaning that a same stock can be bought by multiple users and the stocks table will keep track of the stock bought by each user.
cursor.execute('''CREATE TABLE IF NOT EXISTS Stocks
               (ID INTEGER PRIMARY KEY AUTOINCREMENT,
               stock_symbol VARCHAR(4) NOT NULL,
               stock_name VARCHAR(20) NOT NULL,
               stock_quantity DOUBLE NOT NULL, 
               user_id INTEGER,
               FOREIGN KEY (user_id) REFERENCES Users(ID),
                FOREIGN KEY (stock_symbol) REFERENCES StockMarket(stock_symbol))''')   

# Users table to keep track of the users who are registered in the system.
# This table has a unique ID and user_name for each user.   
cursor.execute('''CREATE TABLE IF NOT EXISTS Users
              (ID INTEGER PRIMARY KEY AUTOINCREMENT,
               first_name TEXT,
               last_name TEXT,
               user_name TEXT NOT NULL,
               password TEXT NOT NULL,
               usd_balance DOUBLE NOT NULL DEFAULT 100.00)''')



connection.commit()
connection.close()