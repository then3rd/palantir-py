#!venv/bin/python3
"""
start -> home -> gotoStartPosition
Step 1x (axis, distance, direction) ok -> sample(time, count)
[Axis at max distance? ](yes, no)
     yes: step other axis x1 -> toggle axis direction ->goto step 1x
     no: goto step 1x

(360/(200step * 8microstep * 5:1 ratio)) * quality_multiplier = accuracy
120 * 

"""
# import os
import sys
import argparse
import socketserver
from controller import MyTCPHandler
from controller import Controller


def main(arguments):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-d', '--device', help='Machine serial device', required=True)
    parser.add_argument('-b', '--baud', help='Baud Rate', required=True)
    parser.add_argument('-p', '--port', help='server port', required=False)

    # parser.add_argument('infile', help="Input file", type=argparse.FileType('r'))
    # parser.add_argument('-o', '--outfile', help="Output file",
    #                     default=sys.stdout, type=argparse.FileType('w'))

    args = parser.parse_args(arguments)
    print(args)

    if args.device:
        antenna = Controller(args.device, args.baud)
        antenna.serialConnect()

    if args.port:
        server_address = ('localhost', int(args.port))
        server = socketserver.TCPServer(server_address, MyTCPHandler)
        print('Starting webserver', server_address)
        server.serve_forever()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
