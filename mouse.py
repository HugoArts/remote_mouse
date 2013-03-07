#! /usr/bin/env python

import evdev
from evdev import ecodes
from asyncore import file_dispatcher


class RelativeDispatcher(file_dispatcher):
    def __init__(self, device, sender):
        file_dispatcher.__init__(self, device)
        self.device = device
        self.sender = sender

        self.last_mov_x = 0
        self.last_mov_y = 0

    def recv(self, ign=None):
        return self.device.read()

    def handle_error(self):
        raise

    def handle_close(self):
        print "closing channel: {}".format(self)

    def handle_read(self):
        for event in self.recv():
            if event.type == ecodes.EV_SYN and event.code == ecodes.SYN_REPORT:
                self.handle_syn(event)
            else:
                self.handle_event(event)

    def handle_syn(self, event):
        self.sender.send_event("MOV {0} {1}".format(self.last_mov_x, self.last_mov_y))

    def handle_event(self, event):
        if event.type == ecodes.EV_REL:
            if event.code == ecodes.REL_X:
                self.last_mov_x = event.value
            elif event.code == ecodes.REL_Y:
                self.last_mov_y = event.value

        if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_MOUSE:
            print event, event.value
            #self.sender.send_event("{}\r\n".format("LU" if event.value else "LD"))


class AbsoluteDispatcher(RelativeDispatcher):
    def __init__(self, device, sender):
        RelativeDispatcher.__init__(self, device, sender)
        self.touching = False
        self.touch_event = False

        self.last_pos_x = 0
        self.last_pos_y = 0

    def handle_event(self, event):
        if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
            self.touch_event = bool(event.value)

        if event.type == ecodes.EV_ABS:
            if event.code == ecodes.ABS_X:
                if self.touching:
                    self.last_mov_x = event.value - self.last_pos_x

                if self.touch_event:
                    self.last_pos_x = event.value

            if event.code == ecodes.ABS_Y:
                if self.touching:
                    self.last_mov_y = event.value - self.last_pos_y

                if self.touch_event:
                    self.last_pos_y = event.value

    def handle_syn(self, event):
        #print "handle_syn: MOV mov={},{} pos={},{} touch_event={} touching={}".format(
        #    self.last_mov_x, self.last_mov_y, self.last_pos_x, self.last_pos_y, self.touch_event, self.touching)
        if self.touching:
            RelativeDispatcher.handle_syn(self, event)
        self.touching = self.touch_event


def can_be_mouse(device):
    caps = device.capabilities(absinfo=False)
    return (ecodes.BTN_MOUSE in caps.get(ecodes.EV_KEY, ()) and
            (ecodes.EV_REL in caps or ecodes.EV_ABS in caps))

def find_mouse_devs():
    devices = map(evdev.InputDevice, evdev.list_devices())
    return filter(can_be_mouse, devices)

def select_mouse():
    devices = find_mouse_devs()
    if len(devices) == 0:
        raise RuntimeError("no suitable mouse devices found")
    elif len(devices) == 1:
        print 'found 1 mouse-like device: "{0}". Selecting automatically.'.format(devices[0].name)
        return devices[0]
    else:
        return choose_mouse(devices)

def choose_mouse(devices):
    print "found several mouse-like devices:"
    print_device_list(devices)

    while True:
        choice = raw_input("which device to capture input from? [default=all]: ")
        try:
            if not choice:
                return devices
            else:
                choice = int(choice)
                return devices[choice]
        except (ValueError, IndexError) as e:
            print "invalid input: '{0}'".format(choice)

def print_device_list(devlist):
    for index, dev in enumerate(devlist):
        print "[{:2d}] {:30} {:30} {:30}".format(index, dev.fn, dev.name, dev.phys)

