#!venv/bin/python3
"""
start -> home -> gotoStartPosition
Step 1x (axis, distance, direction) ok -> sample(time, count)
[Axis at max distance? ](yes, no)
     yes: step other axis x1 -> toggle axis direction ->goto step 1x
     no: goto step 1x

(360/(200step * 8microstep * 5:1 ratio)) * quality_multiplier = accuracy

# G91 ; use relative positioning for the XYZ axes
# G1 X10 F3600 ; move 10mm to the right of the current location
# G1 X10 F3600 ; move another 10mm to the right
"""
import sys
import argparse
import logging
# from queue import Queue
import time
from controller import SerialWorker
from controller import ServerWorker
from controller import DeviceWorker

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
        format='(%(threadName)-9s) %(message)s'
        )


    if args.port:
        address = (str(args.host), int(args.port))
        server = ServerWorker(address)
        server.start()

    if args.device:
        # queue = Queue()
        antenna = SerialWorker(args.device, args.baud)
        antenna.serial_connect()
        antenna.start()

        antenna.write("$X\n".encode())

        routine = DeviceWorker(x_range=130)
        routine.start()

    while True:
        time.sleep(1)
        print('.', end='', flush=True)

        # Stream g-code
        # for line in f:
        #     l = removeComment(line)
        #     l = l.strip() # Strip all EOL characters for streaming
        #     if  (l.isspace()==False and len(l)>0) :
        #         print('Sending: ' + l)
        #         s.write(l + '\n') # Send g-code block
        #         grbl_out = s.readline() # Wait for response with carriage return
        #         print(' : ' + grbl_out.strip())
        # s.close()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
