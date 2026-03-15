import subprocess
import time
from osc4py3 import oscbuildparse
from osc4py3.as_eventloop import *

# subprocess.Popen(['sclang', 'event-test.scd'])

# start OSC 
osc_startup()
# set up client to send messages
osc_udp_client('127.0.0.1', 57120, 'scOSCClient')
print("OSC Client started. Ready to send messages!")

try:
    while True:
        oscMSG = input().split()
        if oscMSG[0] == 'address':
            oscAddr = oscMSG[1]
            if len(oscMSG) > 2:
                oscComm = oscMSG[2:]
        elif oscAddr:
            oscComm = oscMSG
        else:
            print('provide OSC address')

        print(oscAddr)
        print(oscComm)

        osc_send(oscbuildparse.OSCMessage(oscAddr, None, oscComm), 'scOSCClient')

        for x in range(10):
            osc_process()
            time.sleep(0.001)
except KeyboardInterrupt:
    osc_terminate()



