""" Classes for controlling various aspects of a cancer-spreading robot """
from threading import Thread
import socketserver
import serial

class SerialWorker(Thread):
    '''Threaded Serial Port Device Controller'''
    def __init__(self, device, baud, x_range=120, y_range=90, quality=1, direction='lrud'):
        super(SerialWorker, self).__init__()
        self.daemon = True
        self.cancelled = False

        # self.queue = queue

        self.ser = serial.Serial()

        self.device = device
        self.baud = baud
        self.x_range = x_range
        self.y_range = y_range
        self.quality = quality
        self.direction = direction

        self.currentline = ()
        return

    def run(self): #, queue):
        while not self.cancelled:
            # Grabs chunk from queue
            # chunk = self.queue.get()
            # print(chunk)
            # process chunk
            grbl_out = self.readline() # Wait for response with carriage return
            print('Serial>', grbl_out.strip().decode())
            # Signals to queue job is done
            # self.queue.task_done()

    def cancel(self):
        self.cancelled = True

    def readline(self):
        self.currentline = self.ser.readline()
        return self.currentline

    def flush(self):
        self.ser.flushInput()

    def write(self, input):
        self.ser.write(input)

    def serialStatus(self):
        return self.ser.isOpen()

    def serialConnect(self):
        print('-->Opening Serial Port: {}'.format(self.device))
        try:
            self.ser = serial.Serial( # set parameters, in fact use your own :-)
                port=self.device,
                baudrate=self.baud,
                # bytesize=serial.SEVENBITS,
                # parity=serial.PARITY_EVEN,
                # stopbits=serial.STOPBITS_ONE
            )
            if self.ser.isOpen():
                print("...port is opened")
            else:
                raise Exception('Port not opened')
        except IOError as err: # if port is already opened, close it and open it again and print message
            print("ERROR opening serial: {}".format(err))
        try:
            self.ser.isOpen()
            return True
        except Exception:
            return False
        return

class ServerWorker(Thread):
    def __init__(self, address):
        super(ServerWorker, self).__init__()
        self.daemon = True
        self.cancelled = False

        self.address = address

    def run(self):
        print('Starting webserver', self.address)
        server = socketserver.TCPServer(self.address, MyTCPHandler)
        server.serve_forever()

    def cancel(self):
        self.cancelled = True

class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The RequestHandler class for our server.
    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print("{} wrote:".format(self.client_address[0]))
        # Print decoded data
        print(self.data.decode('ascii'))
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())
        return

    # def setup(self):
    #     print('--incoming--');
    #     return socketserver.BaseRequestHandler.setup(self)

    # def finish(self):
    #     print('--done--');
    #     return socketserver.BaseRequestHandler.finish(self)

# G91 ; use relative positioning for the XYZ axes
# G1 X10 F3600 ; move 10mm to the right of the current location
# G1 X10 F3600 ; move another 10mm to the right