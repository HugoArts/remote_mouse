#! /usr/bin/env python

import asyncore
import asynchat
import socket
import sys
import ctypes

class ChannelDispatcher(asyncore.dispatcher):
    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        self.address = address
        self.connect_socket()

    def connect_socket(self):
        print "listening for incoming connections..."
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.set_reuse_addr()
            self.bind(self.address)
            self.listen(5)
        except socket.error as e:
            print e
            sys.exit(1)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print "Incoming connection from {}".format(addr)
            handler = Handler(sock, addr)


class Handler(asynchat.async_chat):
    def __init__(self, socket, address):
        asynchat.async_chat.__init__(self, socket)
        self.data = []
        self.address = address
        self.set_terminator("\r\n")

    def collect_incoming_data(self, data):
        self.data.append(data)

    def found_terminator(self):
        message = ''.join(self.data).strip("\r\n")
        self.data = []
        msg = message.split()
        if msg[0] == "MOV":
            x, y = map(int, message.split()[1:])
            self.mouse_move(x, y)
        print message

    def handle_close(self):
        print "closing connection from {}".format(self.address)
        self.close()


class WindowsHandler(Handler):
    MOUSEEVENTF_MOVE      = 0x0001

    mouse_event = ctypes.windll.user32.mouse_event

    def mouse_move(self, x, y):
        mouse_event(MOUSEEVENTF_MOVE, x, y, 0, 0)

    def mouse_button(self, t):
        event_map = {"LU": 0x0002,
                     "LD": 0x0004,
                     "RU": 0x0008,
                     "RD": 0x0010}
        mouse_event(event_map[t], 0, 0, 0, 0)

dispatcher = ChannelDispatcher(("", 49425))
asyncore.loop()
