"""This is an example of performing concurrent tasks on IKA RCT digital hotplate.

Usage: python concurrent_tasks.py <duration of test in minutes, optional>

Three tasks are defined - printing out temperature, printing out stirring speed,
and setting stirring speed to a random value.
First, logging is set up, device object is created and initialized.
Default parameters are set.
Then three task threads are created, started and the main thread sleeps for the
defined amount of time. After that all background tasks are stopped simultaneously
and device is disconnected.
"""

import logging
import random
import sys
import time

from PyLabware import RCTDigitalHotplate

filename = "testing_log_" + time.strftime("%H-%M-%S", time.localtime()) + ".log"

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(thread)d %(levelname)-8s %(message)s',
    level=logging.INFO,
    filename=filename,
    datefmt='%H:%M:%S')

log = logging.getLogger()


def print_temperature():
    log.critical("temp:read:%s", ika.get_temperature())


def print_stirring_speed():
    log.critical("speed:read:%s", ika.get_speed())


def random_set_speed():
    speed = random.choice(range(100, 500, 20))
    ika.set_speed(speed)
    log.critical("speed:write:%s", speed)


if __name__ == "__main__":

    # PyLabware device object
    ika = RCTDigitalHotplate(device_name="IKA hotplate", port=4443, connection_mode="tcpip", address="130.209.220.161")
    log.error("Device created and connected.")
    ika.initialize_device()

    log.error("Init done.")

    # Set temperature
    ika.set_temperature(50)
    ika.set_speed(50)
    ika.start()

    t1 = ika.start_task(interval=1, method=print_temperature, args=None)
    log.error("Temperature monitoring started.")
    id1 = t1.ident
    t2 = ika.start_task(interval=2, method=print_stirring_speed, args=None)
    log.error("Speed monitoring started.")
    id2 = t2.ident
    t3 = ika.start_task(interval=8, method=random_set_speed, args=None)
    log.error("Random speed setting started.")
    id3 = t3.ident

    # Main thread sleeps
    try:
        sleep_minutes = int(sys.argv[1])
    except (IndexError, ValueError, TypeError):
        sleep_minutes = 1
    time.sleep(sleep_minutes * 60)

    ika.stop_all_tasks()
    log.error("All background tasks stopped.")

    ika.stop()
    ika.disconnect()
    log.error("Device disconnected.")
