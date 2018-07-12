test: run do_test kill

run:
	./main.py --device /dev/tty.usbmodem1421 --baud 9600 --host localhost --port 1234 --log DEBUG &

do_test:
	sleep 3
	echo '$$' |cat> /dev/tty.usbmodem1421
	sleep 2
	echo 'foo test' | nc localhost 1234
	sleep 6

kill:
	ps -a|grep '[P]ython.*main.py'|awk '{print $$1}'|xargs kill

.PHONY: test run do_test kill