#!/usr/bin/env python3

# laser-companion, v1.0 / March 20, 2021, by melyux
# -------------------------------------------------
# A companion script to communicate with Wainlux (or related) laser
# engravers and cutters. Motivated by the Wainlux app removing the
# ability to connect the engraver to Wi-Fi networks.
#
# Currently supports:
#
# 1.  Setting the Wi-Fi name and password for the engraver to connect to
#
# 2.  Resetting the Wi-Fi to connect to a hotspot (usually causes the
#     engraver to search for Wi-Fi networks around it and try
#     connecting to them with the password 'aaaabbbb').

import signal
import socket
import string
import os
import threading
import time

def exit_handler(sig, frame):
    print('\nEnding program.')
    os._exit(0)

# Keep receiving until there is a pause of timeout+ seconds.
def recv_timeout(the_socket, timeout=2):
    the_socket.setblocking(0)
    total_data = [];
    data = '';
    begin = time.time()
    while 1:
        # If you got some data, then break after timeout seconds
        if total_data and time.time() - begin > timeout:
            break
        # If you got no data at all, wait a little longer
        elif time.time() - begin > timeout * 2:
            break
        try:
            data = the_socket.recv(8192)
            if data:
                total_data.append(data)
                begin = time.time()
            else:
                time.sleep(0.1)
        except:
            time.sleep(0.1)
            pass
    return b''.join(total_data)

# Accept connection from engraver and start the reception loop.
def receive():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as incoming:
        global conn, connected, last_received_time, last_received
        incoming.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        incoming.bind((our_ip, our_port))
        incoming.listen(1)
        conn, addr = incoming.accept()
        with conn:
            connected = True
            print(f"\nDiscovered the engraver, it is at {addr[0]}.")
            # Receive loop
            while True:
                data = recv_timeout(conn, timeout=1)
                if data:
                    last_received = data
                    last_received_time = time.time()
                elif time.time() - last_received_time > 20:
                    print("\nNo response from engraver for 20+ seconds.")
                    os._exit(0)

# Prompt the engraver to send a heartbeat every 8 seconds, unless the user
# sends other commands in the meantime that cause the wait to be reset.
def heartbeat():
    global last_sent_time
    heartbeat_request = bytes.fromhex("0b 00 0b") + bytes(8)
    while True:
        while last_sent_time < 8:
            time.sleep(1)
        conn.send(heartbeat_request)
        last_sent_time = time.time()
        time.sleep(8)

# Initialize program
signal.signal(signal.SIGINT, exit_handler)
conn = None
connected = False
last_received_time = last_sent_time = time.time()
last_received = None

# Get our IP address and port
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
our_ip = s.getsockname()[0]
s.close()
our_port = 12346
print(f"\nOur IP address is {our_ip}.")

# Start listening for connection and data from engraver
rt = threading.Thread(target=receive)
rt.start()

# Start leaving discovery messages
print("Discovering the engraver.", end="")
while not connected:
    discovery_payload = f'IPjiakuo"{our_ip}",{our_port}\r\n'
    discovery_header = bytes.fromhex('02') + (len(discovery_payload) + 3).to_bytes(2, 'big')
    discovery_message = discovery_header + bytes(discovery_payload, 'ascii')

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as discovery:
        discovery.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        discovery.settimeout(0.1)
        discovery.sendto(discovery_message, ("255.255.255.255", 12345))
        last_sent_time = time.time()
    print('.', end="", flush=True)

    time.sleep(2)
print('')

# Start heartbeat check
ht = threading.Thread(target=heartbeat)
ht.start()

# Wait until we've received a heartbeat from the engraver at least once
print("Waiting for the engraver to be ready. (If it never becomes ready, try restarting it.) .", end="")
while not last_received:
    print('.', end="", flush=True)
    time.sleep(2)
print("\nThe engraver is ready.")

# User-chosen actions
while True:
    choice = input("\n\
What do you want to do?\n\
1. Set Wi-Fi network and password (enter 1)\n\
2. Reset Wi-Fi to connect to any hotspot with password 'aaaabbbb' (enter 2)\n\
3. Do nothing, exit program (enter 3, or do Ctrl+C)\n\n\
Enter: ")
    if choice == '1':
        wifi_name = input("\nEnter the Wi-Fi network name (no special characters allowed): ")
        wifi_password = input("Enter the Wi-Fi network password (no special characters allowed): ")
        length = len(wifi_name) + len(wifi_password) + 19
        change_wifi_request = bytes.fromhex("03 00") + length.to_bytes(1, 'big') + \
            bytes(f'AT+CWJAP="{wifi_name}","{wifi_password}"\r\n', 'ascii')
        conn.send(change_wifi_request)
        last_sent_time = time.time()
        print("\nSent Wi-Fi network settings. The engraver should soon disconnect from us and start connecting to the new network.")
        time.sleep(25)
    elif choice == '2':
        reset_wifi_request = bytes.fromhex("04 00 0b") + bytes(8)
        conn.send(reset_wifi_request)
        last_sent_time = time.time()
        print("\nSent Wi-Fi reset request. The engraver should soon disconnect from us and start looking for hotspots to connect to.")
        time.sleep(25)
    elif choice == '3':
        print("\nEnding program.")
        os._exit(0)
    else:
        print("\nInvalid choice. Try again.")
