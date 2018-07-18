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

        self.quality = quality
        self.order = order

        self.ratio = Fraction(*ratio)
        self.range_min = {'x': 0, 'y': 0}
        self.range_max = {
            'x': x_range if x_range != 0 else y_range / self.ratio,
            'y': y_range if y_range != 0 else x_range / self.ratio}
        self.quality_divide = {
            'x': ratio[0] * self.quality,
            'y': ratio[1] * self.quality}
        self.step_size = {
            'x': Fraction(self.range_max['x'] / self.quality_divide['x']),
            'y': Fraction(self.range_max['y'] / self.quality_divide['y'])}
        self.cur_pos = {'x': 0, 'y': 0}
        self.cur_dir = {'x': 1, 'y': 1}

        logging.info('ratio: %s -> %s', self.ratio, round(float(self.ratio), 4))
        logging.info('x_range: %s -> %s', self.range_max['x'], round(float(self.range_max['x']), 4))
        logging.info('y_range: %s -> %s', self.range_max['y'], round(float(self.range_max['y']), 4))
        logging.info('step_size: x: %s, y: %s', self.step_size['x'], self.step_size['y'])
        logging.info('num_points:(%s+1 * %s+1) %s', self.quality_divide['x'], self.quality_divide['y'], (self.quality_divide['x'] + 1) * (self.quality_divide['y'] + 1))

    ''' The actual algorithm that moves things around
    start -> home -> gotoStartPosition
        Step 1x (axis, distance, direction) ok -> sample(time, count)
        [Axis at max distance? ](yes, no)
            yes: step other axis x1 -> toggle axis direction ->goto step 1x
            no: goto step 1x
    '''
    def run(self):
        while not self.cancelled:
            init = True
            path_end = False
            complete = False
            count = 0
            while self.active:
                if complete:
                    logging.debug('Complete! Sampled %s points.', count)
                    self.gcode_exec(Gcode(['G1', 0, 0, 4000]))
                    self.active = False
                    break
                # Do hackrf sampling here
                logging.debug('Sampling at %s, %s, %s...', round(float(self.cur_pos['x']), 4), round(float(self.cur_pos['y']), 4), round(float(self.cur_dir['y']), 4))
                # The first loop is special, don't do these things
                if init is False:
                    if self.cur_pos['y'] == self.range_max['y'] and self.cur_pos['x'] == self.range_max['x']:
                        complete = True
                    elif self.cur_pos['y'] == self.range_min['y'] and self.cur_dir['y'] != 1:
                        self.cur_dir['y'] = 1
                        path_end = True
                    elif self.cur_pos['y'] == self.range_max['y'] and self.cur_dir['y'] != -1:
                        self.cur_dir['y'] = -1
                        path_end = True
                # Incriment the secondary axis when at the end
                if path_end:
                    self.cur_pos['x'] += self.step_size['x'] * self.cur_dir['x']
                    path_end = False
                # Incriment the primary axis
                elif complete is not True:
                    self.cur_pos['y'] += self.step_size['y'] * self.cur_dir['y']
                    path_end = False
                # Create gcode with current positions
                gcode = Gcode(['G1', self.cur_pos['x'], self.cur_pos['y'], 6000])
                self.gcode_exec(gcode)
                count += 1
                time.sleep(1.5)
                if init != False:
                    init = False

    def gcode_exec(self, gcode):
        # Place gcode into queue to be executed by SerialWorker
        logging.debug('put: \'%s\'', gcode.code)
        self.q_serial_in.put(gcode.code)

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
    def __init__(self, args, q_serial_in, device, baud):
        super().__init__()
        self.name = __class__.__name__
        self.q_serial_in = q_serial_in
        self.daemon = True
        self.cancelled = False

        self.args = args
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
                    logging.info('get: %s', gcode)
                    if self.args.simulate:
                        logging.info('write -> %s', gcode)
                    else:
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
        if self.x_dist is not None:
            gcode_a.append('X{}'.format(round(float(self.x_dist), 4)))
        if self.y_dist is not None:
            gcode_a.append('Y{}'.format(round(float(self.y_dist), 4)))
        if self.feed is not None:
            gcode_a.append('F{}'.format(round(float(self.feed), 4)))
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
