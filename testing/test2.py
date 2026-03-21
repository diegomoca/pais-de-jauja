import threading
import time
from osc4py3.as_eventloop import * # needed to send and receive OSC
from osc4py3 import oscbuildparse


import instruments.harpa.source.frequencies as harpa

finished = False
# define background event loop to process osc
def oscEventLoop():
    while not finished:
        osc_process()
        time.sleep(0.001)
    osc_terminate()
    print('exited event loop')

# start OSC 
osc_startup()
# set up client to send messages
osc_udp_client('127.0.0.1', 57120, 'scOSCClient')
print("OSC Client started. Ready to send messages!")
# set up OSC server to receive messages
osc_udp_server("127.0.0.1", 57121, 'scOSCServer')
print("OSC Server started. Ready to receive messages!")
# start background osc event loop
threading.Thread(target=oscEventLoop).start()

harpaDict = {}
userInput = input(': ')
while userInput != 'end':
    if userInput == 'test':
        osc_send(oscbuildparse.OSCMessage('/test', None, [userInput]), 'scOSCClient')
        harpaDict['name'] = harpa.Frequencies().startup('test')
    userInput = input(': ')


finished = True






# async def event_loop():
#     print('event loop running')
#     finished = False
#     while not finished:
#         osc_process()
#         await asyncio.sleep(0.001)
#     print('exited event loop')


# async def ui():
#     while input(': ') != 'end':
#         pass

# async def main():
#     eventLoopTask = asyncio.create_task(event_loop())
#     uiTask = asyncio.create_task(ui())
#     await eventLoopTask
#     event_loop.finished = True
    

# osc_startup()
# asyncio.run(main())





# harpaDict = {}

# harpaDict['name'] = subprocess.Popen(
#     ['python', 'instruments/harpa/source/frequencies-test.py', 'oscAdress'],
#     stdout=subprocess.PIPE,
#     text=True
# )



# output = harpaDict['name'].communicate()[0]
# print(output)
