""" Classes for controlling various aspects of a cancer-emitting robot """
from threading import Thread
from fractions import Fraction
import socketserver
import time
import logging
import serial

''' Thread controlling device motion (and data capture?) '''
class DeviceWorker(Thread):
    def __init__(self, q_serial_in, x_range=0, y_range=0, ratio=(4, 3), quality=4, order=('y', 'x')):
        super().__init__()
        self.name = __class__.__name__
        self.q_serial_in = q_serial_in
        self.daemon = False
        self.active = False
        self.cancelled = False

        self.ratio = Fraction(*ratio)
        self.range = {
            'x': x_range if x_range != 0 else y_range / self.ratio,
            'y': y_range if y_range != 0 else x_range / self.ratio}
        self.step_size = {
            'x': Fraction(self.range['x'] / ratio[0]),
            'y': Fraction(self.range['y'] / ratio[1])}

        self.quality = quality
        self.order = order

        self.x_min = 0
        self.y_min = 0

        logging.info('ratio: %s -> %s', self.ratio, round(float(self.ratio), 4))
        logging.info('x_range: %s -> %s', self.range['x'], round(float(self.range['x']), 4))
        logging.info('y_range: %s -> %s', self.range['y'], round(float(self.range['y']), 4))
        logging.info('step_size: x: %s, y: %s', self.step_size['x'], self.step_size['y'])

    ''' The actual algorithm that moves things around
    start -> home -> gotoStartPosition
        Step 1x (axis, distance, direction) ok -> sample(time, count)
        [Axis at max distance? ](yes, no)
            yes: step other axis x1 -> toggle axis direction ->goto step 1x
            no: goto step 1x
    '''
    def run(self):
        while not self.cancelled:
            while self.active:
                gcode = Gcode(['G1', -1.1111, 2.222, 3.333]).code
                # gcode = Gcode(['$', None, None, None]).code()
                self.q_serial_in.put(gcode)
                logging.debug('put: \'%s\'', gcode)
                time.sleep(10)

    def gcode_exec(self, gcode):
        # Place gcode into queue to be executed by SerialWorker
        self.q_serial_in.put(gcode.code())

    def cancel(self):
        self.cancelled = True

    def activate(self):
        self.active = True

    def home_routine(self):
        pass

    def begin_routine(self):
        pass

''' Thread for controlling, reading, and writing to a serial device '''
class SerialWorker(Thread):
    def __init__(self, q_serial_in, device, baud):
        super().__init__()
        self.name = __class__.__name__
        self.q_serial_in = q_serial_in
        self.daemon = True
        self.cancelled = False

        self.device = device
        self.baud = baud

        self.ser = serial.Serial()
        self.currentline = ()
        return

    def run(self): #, queue):
        while not self.cancelled:
            while self.ser.isOpen():
                # Check if there is anything in the queue; blocking makes this unreliable?
                if self.q_serial_in.qsize() > 0:
                    gcode = self.q_serial_in.get(block=False)
                    logging.info('gcode: %s', gcode)
                    self.ser.write('{}\n'.format(gcode).encode())
                    self.q_serial_in.task_done()
                # check for response with carriage return
                grbl_out = self.ser.readline()
                if grbl_out:
                    logging.info('serial> %s', grbl_out.strip().decode())
                else:
                    time.sleep(0.1)


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

    def activate(self):
        try:
            logging.info('Opening Serial Port: %s', self.device)
            self.ser = serial.Serial(
                timeout=0, # non-blocking mode
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
        self.name = __class__.__name__
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

class Gcode():
    def __init__(self, coordArray):
        self.cmd = coordArray[0]
        self.x_dist = coordArray[1]
        self.y_dist = coordArray[2]
        self.feed = coordArray[3]
        self.gcode = ''
        self.gencode()

    def gencode(self):
        gcode_a = []
        gcode_a.append(self.cmd)
        if self.x_dist:
            gcode_a.append('X{}'.format(self.x_dist))
        if self.y_dist:
            gcode_a.append('Y{}'.format(self.y_dist))
        if self.feed:
            gcode_a.append('F{}'.format(self.feed))
        self.gcode = ' '.join(gcode_a)

    @property
    def code(self):
        return self.gcode

# class MyServer(socketserver.TCPServer):

#     def serve_forever(self):
#         while True:
#             self.handle_request()
#         return

#     def handle_request(self):
#         return socketserver.TCPServer.handle_request(self)
