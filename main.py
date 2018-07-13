#!venv/bin/python3
"""
(360/(200step * 8microstep * 5:1 ratio)) * quality_multiplier = accuracy

# G91 ; use relative positioning for the XYZ axes
# G1 X10 F3600 ; move 10mm to the right of the current location
# G1 X10 F3600 ; move another 10mm to the right
"""
import sys
import argparse
import logging
from queue import Queue
import time
from controller import SerialWorker, ServerWorker, DeviceWorker

def main(arguments):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--device', help='Machine serial device', required=True)
    parser.add_argument('--baud', help='Baud Rate', required=True)
    parser.add_argument('--host', help='server host', required=False)
    parser.add_argument('--port', help='server port', required=False)
    parser.add_argument('--log', help='log level', required=False)


    # parser.add_argument('infile', help="Input file", type=argparse.FileType('r'))
    # parser.add_argument('-o', '--outfile', help="Output file",
    #                     default=sys.stdout, type=argparse.FileType('w'))

    args = parser.parse_args(arguments)

    loglevel = args.log if args.log else logging.DEBUG
    logging.basicConfig(
        level=loglevel,
        format='(%(threadName)-9s) %(message)s')

    if args.port:
        address = (str(args.host), int(args.port))
        server = ServerWorker(address)
        server.start()

    if args.device:
        # Start SerialWorker queue and thread
        q_serial_in = Queue()
        serial_worker = SerialWorker(q_serial_in, args.device, args.baud)
        serial_worker.start()

        # Start DeviceWorker thread
        device_worker = DeviceWorker(q_serial_in, x_range=130)
        device_worker.start()

        # Join queue
        q_serial_in.join()

        # Initialize serial connection
        serial_worker.activate()
        serial_worker.write("$X\n".encode())

        ## Begin main Routine
        time.sleep(3)
        device_worker.activate()

    while True:
        time.sleep(0.1)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
