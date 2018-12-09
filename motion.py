#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'aiyprojects-raspbian/src/aiy'))

import gpiozero
import pins
import signal
import time

motion_sensor = gpiozero.MotionSensor(pins.PIN_A, pull_up=True)
motion_sensor.when_motion = lambda: print("Motion detected!")
motion_sensor.when_no_motion = lambda: print("...no motion")

if __name__ == '__main__':
    if '--debug' in sys.argv:
        import ptvsd
        address = ('0.0.0.0', 5678)
        ptvsd.enable_attach(address=address)
        print('Waiting for debugger on {}...'.format(address))
        ptvsd.wait_for_attach()
    print('Waiting for motion...')
    # signal.pause()
    while True:
        print('value: {}'.format(motion_sensor.value))
        time.sleep(0.5)
