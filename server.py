""" 
================================================
Title:  server.py
Authors: Abdullah Mahith and Shahbaj Mukul
Description: Server-side code for the stock trading system.
================================================
 """

import socket
import sqlite3
import threading

logged_users = []
# Server config
SERVER_IP = '127.0.0.1'
SERVER_PORT = 38000
shut_down = False

# Create a socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# binding the socket to the server ip and port
server_socket.bind((SERVER_IP, SERVER_PORT))

# Listen for incoming connections
server_socket.listen()
print(f"\nSERVER LISTENING ON {SERVER_IP}:{SERVER_PORT}\n")

# Handle client calls, including login, register, buy, sell, list, balance, and logout
def handle_client(client_socket, client_address):
    user_id = None # user_id is None if the user is not logged in
    global shut_down
# The server will keep listening for commands from the client
    while True:
        # Command will be given in a specific format and it will be broken down into parts to get its parameters
        try:
            command = client_socket.recv(1024).decode('utf-8').strip()
            if not command:
                # No command received, possibly the client disconnected.
                print(f"Client {client_address[0]} logged out or quit\n")
                idx = 0
                for user in logged_users:
                    if user [1] == client_address:
                        break
                    idx = idx + 1
                del logged_users[idx]
                break
            command_parts = command.split()
            if command_parts:
                if command_parts[0] == "LOGIN": # LOGIN Username password
                    if len(command_parts) == 3:
                        user_name, password = command_parts[1], command_parts[2] # ex. LOGIN <username> <password> or LOGIN BMarley VEvwv45684
                        user_id = handle_login(client_socket, user_name, password)
                        if user_id is not None:
                            logged_users.append((user_name,client_address, client_socket))
                    else: # if the command is not in the correct format
                        response = "Error: LOGIN command format is incorrect."
                        client_socket.send(response.encode('utf-8'))
                elif command_parts[0] == "QUIT" or command_parts[0] == "LOGOUT": # if the user wants to logout, we set the user_id to None, but it still can be logged in again
                    user_id = None
                    response = "200 OK"
                    client_socket.send(response.encode('utf-8'))

                # if the user wants to register, we check if the username already exists, if not, we register the user. 
                # for now, we are allowing the client to set the initial balance, but in a real-world scenario, the initial balance should be set by the admin (bank transfer etc)
                # first_name and last_name are also not being requested, but it can be added if needed. 
                elif command_parts[0] == "REGISTER": 
                    if len(command_parts) == 4: 
                        # ex. REGISTER <username> <password> <usd_balance> or 
                        # REGISTER BMarley VEvwv45684 1000
                        user_name, password, usd_balance = command_parts[1], command_parts[2], command_parts[3]

                        # handle_register will return the user_id if the user is successfully registered, otherwise, it will return None
                        # so if the response is not None, user is logged in and response is sent to the client. otherwise the response is already sent by handle_register 
                        user_id = handle_register(client_socket, user_name, password, usd_balance)
                        
                    else:
                        # if the command is not in the correct format
                        response = "Error: REGISTER command format is incorrect." 
                        client_socket.send(response.encode('utf-8'))
            
                elif user_id is not None:
                    # general user commands, such as BUY, SELL, LIST, BALANCE
                   not_quit = handle_user_command(client_socket, command, user_id)
                   print ("Handle command result " +str(not_quit))
                   if not not_quit:
                       shut_down = True
                       break
                else:
                    # if the user is not logged in, we don't allow any commands except for LOGIN, REGISTER, and QUIT
                    response = "Error: You are not logged in."
                    client_socket.send(response.encode('utf-8'))
        except IndexError as e:
            print(f"Error processing command: {e}")
            break  # Break the loop if there's an error
        except Exception as e:
            print(f"Unexpected error: {e}")
            break  # Handle any other unexpected error
# handle login. If the user is found in the database, we return the user_id, otherwise, we return None. In each case, we send a response to the client
def handle_login(client_socket, user_name, password):
    with sqlite3.connect('stock_trading.db') as conn:
        c = conn.cursor()
        c.execute("SELECT ID FROM Users WHERE user_name = ? AND password = ?", (user_name, password)) # check against the database if the user exists in teh Users table
        user_id = c.fetchone()
        if user_id:
            print(f"USER{user_id[0]} - {user_name} logged in.\n")
            response = f"Successfully logged in as {user_name}\n."
        else:
            print(f"Invalid login attempt for {user_name}.\n")
            response = "Invalid username or password."
        client_socket.send(response.encode('utf-8'))
        return user_id[0] if user_id else None

# handle register. If the user is successfully registered, we return the user_id, otherwise, we return None. In each case, we send a response to the client    
def handle_register(client_socket, user_name, password, usd_balance):
    with sqlite3.connect('stock_trading.db') as conn:
        c = conn.cursor()
        c.execute("SELECT ID FROM Users WHERE user_name = ?", (user_name,))
        user_id = c.fetchone()
        if user_id: # edge case where the given username already exists
            response = "Username already exists."
            print(f"Attempted registration with existing username: {user_name}")
            user_id = None
        else:
            # if the username is not found, we register the user
            # again, for basic registration, we are allowing the client to set the initial balance It should be set by the admin in a real-world scenario or enhanced security protocols.
            c.execute("INSERT INTO Users (user_name, password, usd_balance) VALUES (?, ?, ?)", ( user_name, password, usd_balance))
            conn.commit()
            user_id = c.lastrowid
            response = "Successfully registered."
            print(f"{user_name} registered with user_id: {user_id}")
        client_socket.send(response.encode('utf-8'))
        return user_id if response == "Successfully registered." else None
    
# handle user commands such as BUY, SELL, LIST, BALANCE. details are in the function
def handle_user_command(client_socket, command, user_id):
    with sqlite3.connect('stock_trading.db') as conn:
        user_name = conn.execute("SELECT user_name FROM Users WHERE ID = ?", (user_id,)).fetchone()[0]
        print(f"user_id {user_id}: Requested: {command} \n")
        command_text = command.split()

        send = True
        if command_text[0] == "LIST":
            response = handle_list(conn, user_id) 
        elif command_text[0] == "BUY":
            response = handle_buy_command(conn, user_id, command_text)
        elif command_text[0] == "SELL":
            response = handle_sell_command(conn, user_id, command_text)
        elif command_text[0] == "BALANCE":
            response = handle_balance(conn, user_id)
        elif command_text[0] == "DEPOSIT":
            response = handle_deposit(conn, user_id, command_text)
        elif command_text[0] == "LOOKUP":
            response = handle_lookup(conn, user_id, command_text)
        elif command_text[0] == "WHO":
            response = handle_who(conn, user_id)
        elif command_text[0] == "SHUTDOWN":
            response = handle_shutdown(conn, user_id)
            print (response)
            if response == "QUIT":
                response = f"" + response
                #print("Sending to users...")
                for user in logged_users:
                    #print(str(user[1]) + " " + str(user[2]))
                    user[2].send(response.encode('utf-8'))
                send = False
            else:
                response = f""+response
        else:
            response = "Unknown command or command not allowed."
        if send:
            client_socket.send(response.encode('utf-8'))
        return send

# handle buy command. If the stock is available (in the stock market) and the user has enough balance, we update the user's balance and stock quantity. In each case, we send a response to the client 
def handle_buy_command(conn, user_id, command_text):
    c = conn.cursor()
    # check if the stock is available
    stock_symbol, req_stock_quantity = command_text[1], int(command_text[2])
    c.execute("SELECT stock_price FROM StockMarket WHERE stock_symbol = ?", (stock_symbol,))
    stock_price = c.fetchone()
    if not stock_price:
        return "Stock not found" # if we don't have the stock, there won't be a price for it since its nonnullable
    
    stock_price = stock_price[0]
    total_price = stock_price * req_stock_quantity

    # check if the user has enough balance
    c.execute("SELECT usd_balance FROM Users WHERE ID = ?", (user_id,))
    user_balance = c.fetchone()
    if not user_balance:
        return f"Balance unavailable" # edge case, we should never reach here because the user_id is already validated
    if user_balance[0] < total_price: # if the user doesn't have enough balance to purchase the stock
        response = f"Insufficient balance. Wallet: ${user_balance[0]} but ${total_price} is needed to buy {req_stock_quantity} shares of {stock_symbol}."
        print(f"{user_id}: {response}.\n")
        return response
    else:
        # user has sufficient balance, update the balance and the stock quantity
        new_balance = user_balance[0] - total_price
        c.execute("UPDATE Users SET usd_balance = ? WHERE ID = ?", (new_balance, user_id))
        update_or_insert_stock(conn, user_id, stock_symbol, stock_price, req_stock_quantity)
        conn.commit()
        response = f"Successfully bought {req_stock_quantity} shares of {stock_symbol} for ${total_price}.\nWallet: ${new_balance}"
        print(f"user_id {user_id}: {response}.\n")
        return response

# update or insert stock. If the stock exists, we update its quantity, otherwise, we insert a new record to the db.
def update_or_insert_stock(conn, user_id, stock_symbol, stock_price, req_stock_quantity):
    c = conn.cursor()
    # Ensure to pass stock_symbol as a single-element tuple
    c.execute("SELECT stock_name FROM StockMarket WHERE stock_symbol = ?", (stock_symbol,))
    stock_name_result = c.fetchone()
    if not stock_name_result:
        print(f"Stock {stock_symbol} requested, but not found in the market.\n")
        return "Stock not found"
    stock_name = stock_name_result[0]
    
    c.execute("SELECT stock_quantity FROM Stocks WHERE user_id = ? AND stock_symbol = ?", (user_id, stock_symbol))
    stock = c.fetchone()
    if stock:  # If stock exists, update its quantity
        new_stock_quantity = stock[0] + req_stock_quantity
        c.execute("UPDATE Stocks SET stock_quantity = ? WHERE user_id = ? AND stock_symbol = ?", (new_stock_quantity, user_id, stock_symbol))
    else:  # If stock doesn't exist, insert a new record
        # test
        c.execute("INSERT INTO Stocks (stock_symbol, stock_name, stock_price, user_id, stock_quantity) VALUES (?, ?, ?, ?, ?)", (stock_symbol, stock_name, stock_price, user_id, req_stock_quantity))

    conn.commit() 

# if the user has the stock and enough of it, we update the user's balance and stock quantity. In each case, we send a response to the client
def handle_sell_command(conn, user_id, command_text):
    c = conn.cursor()
    stock_symbol, req_stock_quantity = command_text[1], int(command_text[2])
    c.execute("SELECT stock_price FROM StockMarket WHERE stock_symbol = ?", (stock_symbol,))
    stock_price_result = c.fetchone()
    if stock_price_result is None:
        return "Stock not found in the market."
    stock_price = stock_price_result[0]

   

    # check if user has the stock and enough of it
    c.execute("SELECT stock_quantity FROM Stocks WHERE user_id = ? AND stock_symbol = ?", (user_id, stock_symbol))
    user_stock_info = c.fetchone()
    if user_stock_info is None:
        print(f"user_id: {user_id} does not have this stock.\n")
        return "You don't not have this stock."
    elif user_stock_info[0] < req_stock_quantity:
        response = f"Requested stock quantity exceeds stock balance.\n"
        print(f"user_id: {user_id}: {response}")
        return response
    total_price = stock_price * req_stock_quantity

    # update user's balance
    c.execute("SELECT usd_balance FROM Users WHERE ID = ?", (user_id,))
    user_balance = c.fetchone()[0]
    new_balance = user_balance + total_price
    c.execute("UPDATE Users SET usd_balance = ? WHERE ID = ?", (new_balance, user_id))

    # update user's stock balance
    user_stock_quantity = user_stock_info[0] - req_stock_quantity
    if user_stock_quantity == 0:
        c.execute("DELETE FROM Stocks WHERE user_id = ? AND stock_symbol = ?", (user_id, stock_symbol))
    else:
        c.execute("UPDATE Stocks SET stock_quantity = ? WHERE user_id = ? AND stock_symbol = ?", (user_stock_quantity, user_id, stock_symbol))

    conn.commit()
    response = f"Successfully sold {req_stock_quantity} shares of {stock_symbol} for ${total_price}.\nWallet: ${new_balance}"
    print(f"user_id: {user_id}:" + response + "\n")
    return response
# handle shutdown. If the user is root, we shut down the server, otherwise, we send a response to the client
def handle_shutdown(conn, user_id):
    user_name = validate_user(conn, user_id)
    if user_name:
        if user_name == "root":
            print("\n\nSHUTTING DOWN SERVER!\n\n")
            return "QUIT"
        else:
            return "403 Not a root user"

# Return the list of stocks in the stock market, if the user is root, otherwise, return the list of stocks for the user
def handle_list(conn, user_id):
    user_name = validate_user(conn,user_id)
    response = ""
    c = conn.cursor()
    if user_name == "root":
        c.execute("SELECT st.stock_symbol, st.stock_quantity, u.user_name FROM Stocks as st,Users as u WHERE st.user_id = u.id")
        details = c.fetchall()
        response = "200 OK\n"
        response += "The list of records in the Stock database:\n"
        id = 1
        for detail in details:
            print(detail)
            response += str(id) + " " + str(detail[0]) + " " + str(detail[1]) + " " + str(detail[2]) + "\n"
            id = id + 1
    else:
        response = "200 OK\n"
        response += "The list of records in the Stock database for " + str(user_name) + ":\n"
        c.execute("SELECT stock_symbol, stock_name, stock_quantity FROM Stocks WHERE user_id = ?", (user_id,))
        user_stocks = c.fetchall()
        id = 1
        for stock in user_stocks:
            response += str(id) + " " + str(stock[0]) + " " + str(stock[2]) + " " + "\n"
            id = id + 1
    result = f""+response
    return result

# Return the user's balance, edge case if the user is not found
def handle_balance(conn, user_id):
    c = conn.cursor()
    c.execute("SELECT usd_balance FROM Users WHERE ID = ?", (user_id,))
    user_balance = c.fetchone()
    if user_balance:
        return f"Your balance is ${user_balance[0]}"
    else:
        return "User not found"

# Deposit money to the user's account (As per requirements, not a good practice), edge case if the user is not found (shouldn't happen)
def handle_deposit(conn, user_id, command_text):
    amount = float(command_text[1])
    c = conn.cursor()
    c.execute("SELECT usd_balance FROM Users WHERE ID = ?", (user_id,))
    user_balance = c.fetchone()
    if user_balance:
        new_balance = user_balance[0] + amount
        c.execute("UPDATE Users set usd_balance=? WHERE ID = ?", (new_balance, user_id,))
        return f"deposit successfully. New balance ${new_balance}"
    else:
        return "User not found"

# Lookup a stock, format: LOOKUP <stockname>, if the stock is found, we return the stock quantity, otherwise, we return a response to the client
def handle_lookup(conn, user_id, command_text):
    stock_symbol = command_text[1]
    c = conn.cursor()
    c.execute("SELECT stock_quantity FROM Stocks WHERE user_id = ? AND stock_symbol = ?", (user_id, stock_symbol))
    stock_quantity = c.fetchone()
    if stock_quantity:
        return f"200 OK\nFound 1 match\n{stock_symbol} {stock_quantity[0]}"
    else:
        return "404 Your search did not match any records."

# internal function to validate the user_id and return the user_name
def validate_user(conn, user_id):
    c = conn.cursor()
    c.execute("SELECT user_name FROM Users WHERE ID = ?", (user_id,))
    user_name = c.fetchone()
    if user_name:
        return user_name[0]
    else:
        return "None"

# accecible only to root user_id return the list of active users that are logged in
def handle_who(conn, user_id):
    c = conn.cursor()
    c.execute("SELECT user_name FROM Users WHERE ID = ?", (user_id,))
    user_name = c.fetchone()
    if user_name:
        if user_name[0] == "root":
            result = ""
            for user in logged_users:
                result = result + str(user[0]) + " " + str(user[1][0]) + "\n"
            return f"200 OK\nThe list of active users:\n" + result
        else:
            return f"403 Not a root user"
    else:
        return "403 Wrong UserID or Password"

# Accept incoming connections
while not shut_down:
    client_socket, client_address = server_socket.accept()
    print(f"\nConnection from {client_address} has been established\n")
    client_thread = threading.Thread(target=handle_client, args=(client_socket,client_address,))
    client_thread.start()