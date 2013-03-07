#! /usr/bin/env python

import asyncore
import socket
import sys
import evdev

import mouse

class Sender(asyncore.dispatcher):

    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        self.address = address
        self.buffer = ""
        self.connect_socket()

    def connect_socket(self):
        print "attempting to connect..."
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect(self.address)
        except socket.error as e:
            print e
            sys.exit(1)

    def handle_error(self):
        raise

    def handle_connect(self):
        print "connected"

    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

    def send_event(self, event_str):
        self.buffer += (event_str + "\r\n")

    def readable(self):
        return False

    def writable(self):
        return len(self.buffer) > 0


sender = Sender((raw_input("Please enter address to connect to: "), 49425))

print "adding the following devices:"
mouse_devices = mouse.find_mouse_devs()
mouse.print_device_list(mouse_devices)

for dev in mouse_devices:
    capabilities = dev.capabilities(absinfo=False)
    if evdev.ecodes.EV_REL in capabilities:
        mouse_channel = mouse.RelativeDispatcher(dev, sender)
    elif evdev.ecodes.EV_ABS in capabilities:
        mouse_channel = mouse.AbsoluteDispatcher(dev, sender)

print "starting loop.."
asyncore.loop()
