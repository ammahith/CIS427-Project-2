""" 
================================================
Title:  client.py
Authors: Abdullah Mahith and Shahbaj Mukul
Description: Client-side code for the stock trading system.
Run: python client.py 127.0.0.1 38000
================================================
 """
import socket
import sys
import time

# Check for command line arguments to get the server IP and port
# Command to run the code and connect with the server: python client.py 127.0.0.1 38000
if len(sys.argv) >= 3:
    server_ip = sys.argv[1]  
    server_port = int(sys.argv[2])  
else:
    print("Usage: python client.py <server_ip> <server_port>")
    sys.exit(1)


def new_session():
    print("\nWelcome to the Stock Trading System!\n")
    print("Please enter your username and password to login or register a new account.\n Ex. LOGIN <username> <password> or REGISTER <username> <password> <usd_balance>\n")

def print_menu():
    print("\nAvailable Commands:")
    print("LIST - List all stocks")
    print("BUY <symbol> <quantity> - Buy stocks")
    print("SELL <symbol> <quantity> - Sell stocks")
    print("BALANCE - Check your balance")
    print("DEPOSIT <amount> - Add balance")
    print("WHO - Actively Logged in users")
    print("LOOKUP - Lookup the stock")
    print("LOGOUT - Logout the session")
    print("QUIT - Exit the program")
    print("SHUTDOWN - server shutdown and all clients(only root)")

def main():
    s = socket.socket()
    # Using the IP and port from the command line arguments, connect to the server
    try:
        s.connect((server_ip, server_port))
        print(f"Connected to {server_ip} on port {server_port}\n==========================================")
    except Exception as e: # If unable to connect, print the error and exit
        print(f"Unable to connect to {server_ip} on port {server_port}: {e}")
        sys.exit(1)

    new_session()
    while True:       
        command = input("Enter a command: ")    
        if command == "SHUTDOWN":
            s.sendall(command.encode('utf-8'))
            response = s.recv(1024).decode('utf-8')
            if response == "QUIT":
                break
            print("\n------------------------------------------\nServer Response:", response,"\n------------------------------------------")
            print_menu()
        else:
            s.sendall(command.encode('utf-8'))
            response = s.recv(1024).decode('utf-8')
            if command == "QUIT":
                break
            print("\n------------------------------------------\nServer Response:", response,"\n------------------------------------------")
            print_menu()        
    s.close()


if __name__ == "__main__":
    main()
