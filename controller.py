""" Classes for controlling various aspects of a cancer-emitting robot """
from threading import Thread
import socketserver
import time
import logging
import serial

''' Thread controlling device motion (and data capture?) '''
class DeviceWorker(Thread):
    def __init__(self, x_range=120, y_range=90, quality=1, direction='lrud'):
        super().__init__()
        self.name = 'DeviceWorker'
        self.daemon = False
        self.cancelled = False

        self.x_range = x_range
        self.y_range = y_range
        self.quality = quality
        self.direction = direction

    def run(self):
        while not self.cancelled:
            logging.debug('do this')
            time.sleep(3)
            logging.debug('do that')

    def cancel(self):
        self.cancelled = True

    def home_routine(self):
        pass

    def begin_routine(self):
        pass

''' Thread for controlling, reading, and writing to a serial device '''
class SerialWorker(Thread):
    def __init__(self, device, baud):
        super().__init__()
        self.name = 'SerialWorker'
        self.daemon = True
        self.cancelled = False
        # self.queue = queue

        self.device = device
        self.baud = baud

        self.ser = serial.Serial()
        self.currentline = ()
        return

    def run(self): #, queue):
        while not self.cancelled:
            # Grabs chunk from queue
            # chunk = self.queue.get()
            # print(chunk)
            # process chunk
            grbl_out = self.readline() # Wait for response with carriage return
            logging.info('Serial> %s', grbl_out.strip().decode())
            # Signals to queue job is done
            # self.queue.task_done()

    def cancel(self):
        self.cancelled = True

    def readline(self):
        self.currentline = self.ser.readline()
        return self.currentline

    def flush(self):
        self.ser.flushInput()

    def write(self, data_in):
        self.ser.write(data_in)

    def serial_status(self):
        return self.ser.isOpen()

    def serial_connect(self):
        try:
            logging.info('Opening Serial Port: %s', self.device)
            self.ser = serial.Serial(
                port=self.device,
                baudrate=self.baud,
                # bytesize=serial.SEVENBITS,
                # parity=serial.PARITY_EVEN,
                # stopbits=serial.STOPBITS_ONE
            )
            if self.ser.isOpen():
                logging.info("port is opened")
            else:
                raise Exception('Port not opened')
        except IOError as err:
            logging.error("ERROR opening serial: %s", err)

''' Thread controlling SocketServer '''
class ServerWorker(Thread):
    def __init__(self, address):
        super().__init__()
        self.name = 'ServerWorker'
        self.daemon = True
        self.cancelled = False

        self.address = address

    def run(self):
        logging.info('Starting webserver %s', self.address)
        try:
            # server = MyServer(self.address, MyTCPHandler)
            server = socketserver.TCPServer(self.address, MyTCPHandler)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            logging.info('exiting!')
            server.server_close()
        except OSError as err:
            logging.error(err)

    def cancel(self):
        self.cancelled = True

''' Handler for incoming TCP Connections '''
class MyTCPHandler(socketserver.BaseRequestHandler):

    def setup(self):
        logging.info('%s:%s connected', *self.client_address)
        return socketserver.BaseRequestHandler.setup(self)

    def handle(self):
        while True:
            data = self.request.recv(1024)
            if not data:
                break
            # DO SOMETHING WITH DATA HERE
            # probably need a queue to talk to the serial thread

            send = data.strip().upper()
            self.request.sendall(send)

    def finish(self):
        logging.info('%s:%s disconnected', *self.client_address)
        return socketserver.BaseRequestHandler.finish(self)

# class MyServer(socketserver.TCPServer):

#     def serve_forever(self):
#         while True:
#             self.handle_request()
#         return

#     def handle_request(self):
#         return socketserver.TCPServer.handle_request(self)
