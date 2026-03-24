import threading
import subprocess
import time
from pathlib import Path

from rich.prompt import Prompt
from rich.console import Console
from osc4py3 import oscbuildparse
from osc4py3.as_eventloop import *
from osc4py3 import oscmethod as osm # needed to receive OSC

import instruments.harpa.source.frequencies as harpa
from midi_recorder import start_midi_recording, stop_midi_recording
from midi_playback import start_midi_playback, stop_midi_playback, outport

console = Console()

class Input(Prompt):
    prompt_suffix = ": "
    default_console = console

console.rule('[bold]WELLCOME')

instrList = ['harpa']
commands = ['create', 'destroy', 'keyboard', 'cc', 'activate',
            'deactivate', 'midi', 'recording', 'playback', 'play', 'stop']
names = []
instrDict = {}
# set() is list without duplicates and order
registered_addresses = set()

def invalidNames():
    return instrList + commands + names

# function to calculate frequencies once instrument was successfully
# created in supercollider
created_flag = [False]
def instFreqsCalc(address, msg):
    instanceAddress = address
    instanceName = instanceAddress.split('/')[-1]
    flag = msg

    if flag == 'created':
        instrDict[instanceName] = {
            'freqsCalc': harpa.Frequencies().startup(instanceAddress + '/freqs'),
            'keyboardActivated': False,
            'ccActivated': False,
            'instanceAddress': instanceAddress
        }
        names.append(instanceName)
        created_flag[0] = True


# function to determin wwhether osc connection with instruments was successful
instruments_ready_flag = [False]
instruments_confirm_flag = [False]
def instrumentsConfirmation(msg):
    print(msg)
    if msg == 'confirmed':
        instruments_confirm_flag[0] = True
    if msg == 'ready':
        instruments_ready_flag[0] = True
    
    
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
# set up OSC server to receive messages
osc_udp_server("127.0.0.1", 13131, 'scOSCServer')
print("OSC Server started. Ready to receive messages!")
# start background osc event loop
threading.Thread(target=oscEventLoop).start()

# run supercollider script
subprocess.Popen(['sclang', 'main-event.scd'])

# osc confirmation from supercollider
osc_method('/instruments', instrumentsConfirmation)
while not instruments_ready_flag[0]:
    time.sleep(0.01)
# set up client to send messages
osc_udp_client('127.0.0.1', 13130, 'scOSCClient')
osc_send(oscbuildparse.OSCMessage('/instruments', ',s', ['ready']), 'scOSCClient')
# osc reconfirmation from supercollider
while not instruments_confirm_flag[0]:
    time.sleep(0.01)
print("OSC Client started. Ready to send messages!")
console.print(f'[green]󰼁 OSC connection successfull![/green]\n')

exit_flag = [False]
midiRec = [False]
midiPlay = [False]
midiRecFileName = [None]
midiPlayFileName = [None]
while True:
    if exit_flag[0]:
        userInput = ['exit']
    else:
        userInput = Input.ask('󰼂', choices=(names + ['create', 'midi', 'exit']), console=console).split()
    match userInput[0]:
        case 'create':
            if len(userInput) == 1:
                userInput = Input.ask('[blue]󰼂 instrument[/blue]', choices=(instrList + ['home', 'exit']), console=console).split()
                if userInput[0] == 'exit':
                    exit_flag[0] = True
                    continue
                elif userInput[0] == 'home':
                    continue
                for instrument in instrList:
                    if userInput[0] == instrument and len(userInput) == 1:
                        userInput = Input.ask('[blue]󰼂 name[/blue]', console=console).split()
                        if userInput[0] == 'exit':
                            exit_flag[0] = True
                            break
                        elif userInput[0] == 'home':
                            continue
                        while len(userInput) != 1: 
                            console.print('[red] no spaces allowed![/red]')
                            userInput = Input.ask('[blue]󰼂 name[/blue]', console=console).split()
                        for name in invalidNames():
                            while userInput[0] == name:
                                console.print('[red] invalid name![/red]')
                                userInput = Input.ask('[blue]󰼂 name[/blue]', console=console).split()
                        
                        # create instrument
                        # build osc address and osc message and send it so supercollider
                        instanceName = userInput[0]
                        classAddress = '/instruments/' + str(instrument)
                        oscMessage = ['create', instanceName]
                        # receive message from supercollider indicating that a new instance was created
                        # and execute python script to calculate and send frequencies
                        instanceAddress = classAddress + f'/{instanceName}'
                        # because osc activated functions/addresses can't be removed they have to be
                        # called and registered only once per session to avoid duplicate receivers
                        if instanceAddress not in registered_addresses:
                            osc_method(instanceAddress, instFreqsCalc, osm.OSCARG_ADDRESS + osm.OSCARG_DATAUNPACK)
                            registered_addresses.add(instanceAddress)
                        # send an OSC message to create a new instance of the instrument in supercollider
                        osc_send(oscbuildparse.OSCMessage(classAddress, ',ss', oscMessage), 'scOSCClient')
                        # wait for confirmation from supercollider
                        while not created_flag[0]:
                            time.sleep(0.01)
                        created_flag[0] = False
                        console.print(f'[green]󰼁 {instanceName} created![/green]\n')

        case 'midi':
            if len(userInput) == 1:
                userInput = Input.ask('[blue]󰼂 midi[/blue]', choices=['recording', 'playback', 'home', 'exit'], console=console).split()
                if userInput[0] == 'exit':
                    exit_flag[0] = True
                    continue
                elif userInput[0] == 'home':
                    continue
                match userInput[0]:
                    case 'recording':
                        if midiRec[0] == False:
                            userInput = Input.ask('[blue]󰼂 midi recording', choices=['start', 'home', 'exit'], console=console).split()
                            if userInput[0] == 'exit':
                                exit_flag[0] = True
                                continue
                            elif userInput[0] == 'home':
                                continue
                            if len(userInput) == 1 and userInput[0] == 'start':
                                userInput[0] = Input.ask('[blue]󰼂 file name', console=console)
                                if userInput[0] == 'exit':
                                    exit_flag[0] = True
                                    continue
                                elif userInput[0] == 'home':
                                    continue
                                midiRecFileName[0] = userInput[0]
                                midiRec[0] = True
                                start_midi_recording()
                                console.print(f'[green]󰼁 midi recording of [italic]\'{midiRecFileName[0]}\'[/green][/italic]: [cyan2 italic]started\n')
                        elif midiRec[0] == True:
                            userInput = Input.ask('[blue]󰼂 midi recording', choices=['stop', 'home', 'exit'], console=console).split()
                            if userInput[0] == 'exit':
                                exit_flag[0] = True
                                continue
                            elif userInput[0] == 'home':
                                continue
                            if len(userInput) == 1 and userInput[0] == 'stop':
                                midiRec[0] = False
                                stop_midi_recording(midiRecFileName[0])
                                console.print(f'[green]󰼁 midi recording of [italic]\'{midiRecFileName[0]}\'[/green][/italic]: [orange1 italic]stopped\n')

                    case 'playback':
                        if midiPlay[0] == False:
                            userInput = Input.ask('[blue]󰼂 midi playback', choices=['start', 'home', 'exit'], console=console).split()
                            if userInput[0] == 'exit':
                                exit_flag[0] = True
                                continue
                            elif userInput[0] == 'home':
                                continue
                            if len(userInput) == 1 and userInput[0] == 'start':
                                userInput[0] = Input.ask('[blue]󰼂 file name', console=console)
                                if userInput[0] == 'exit':
                                    exit_flag[0] = True
                                    continue
                                elif userInput[0] == 'home':
                                    continue
                                # midiPlayFileName[0] = userInput[0]
                                # if file_path.exists():
                                #     start_midi_playback(midiPlayFileName[0])
                                #     midiPlay[0] = True
                                #     console.print(f'[green]󰼁 midi playback of [italic]\'{midiPlayFileName[0]}\'[/green][/italic]: [cyan2 italic]started\n')
                                file_path = Path(userInput[0])
                                while not file_path.exists():
                                    # TODO make it so that you can exit and go back from this and similar submenus
                                    console.print(f'[red][italic]\'{userInput[0]}\'[/italic] does not exist')
                                    userInput = Input.ask('[blue]󰼂 file name', console=console).split()
                                    file_path = Path(userInput[0])
                                midiPlayFileName[0] = userInput[0]
                                threading.Thread(target=start_midi_playback, args=(midiPlayFileName[0],)).start()
                                midiPlay[0] = True
                                console.print(f'[green]󰼁 midi playback of [italic]\'{midiPlayFileName[0]}\'[/green][/italic]: [cyan2 italic]started\n')
                                
                                
                        elif midiPlay[0] == True:
                            userInput = Input.ask('[blue]󰼂 midi playback', choices=['stop', 'home', 'exit'], console=console).split()
                            if userInput[0] == 'exit':
                                exit_flag[0] = True
                                continue
                            elif userInput[0] == 'home':
                                continue
                            if len(userInput) == 1 and userInput[0] == 'stop':
                                stop_midi_playback()
                                midiPlay[0] = False
                                console.print(f'[green]󰼁 midi playback of [italic]\'{midiPlayFileName[0]}\'[/green][/italic]: [orange1 italic]stopped\n')

        case name if name in names:
            if len(userInput) == 1:
                userInput = Input.ask(f'[blue]󰼂 {name}[/blue]', choices=['keyboard', 'cc', 'destroy', 'home', 'exit'], console=console).split()
                if userInput[0] == 'exit':
                    exit_flag[0] = True
                    continue
                elif userInput[0] == 'home':
                    continue
                match userInput[0]:
                    case 'keyboard':
                        address = instrDict[name]['instanceAddress'] + '/keyboard'
                        if instrDict[name]['keyboardActivated'] == False:
                            userInput = Input.ask(f'[blue]󰼂 {name} [bold]\\[keyboard][/bold] (deactivated)[/blue]', choices=['activate', 'home', 'exit'], console=console).split()
                            if userInput[0] == 'exit':
                                exit_flag[0] = True
                                continue
                            elif userInput[0] == 'home':
                                continue
                            if len(userInput) == 1 and userInput[0] == 'activate':
                                osc_send(oscbuildparse.OSCMessage(address, ',s', ['activate']), 'scOSCClient')
                                # TODO make it so that it needs confirmation from supercollider to execute
                                instrDict[name]['keyboardActivated'] = True
                                console.print(f'[green]󰼁 {name} [bold]\\[keyboard][/green][/bold]: [cyan2 italic]activated\n')
                        elif instrDict[name]['keyboardActivated'] == True:
                            userInput = Input.ask(f'[blue]󰼂 {name} [bold]\\[keyboard][/bold] (activated)[/blue]', choices=['deactivate', 'home', 'exit'], console=console).split()
                            if userInput[0] == 'exit':
                                exit_flag[0] = True
                                continue
                            elif userInput[0] == 'home':
                                continue
                            if len(userInput) == 1 and userInput[0] == 'deactivate':
                                osc_send(oscbuildparse.OSCMessage(address, ',s', ['deactivate']), 'scOSCClient')
                                # TODO make it so that it needs confirmation from supercollider to execute
                                instrDict[name]['keyboardActivated'] = False
                                console.print(f'[green]󰼁 {name} [bold]\\[keyboard][/green][/bold]: [orange1 italic]deactivated\n')
                    case 'cc':
                        address = instrDict[name]['instanceAddress'] + '/cc'
                        if instrDict[name]['ccActivated'] == False:
                            userInput = Input.ask(f'[blue]󰼂 {name} [bold]\\[cc][/bold] (deactivated)[/blue]', choices=['activate', 'home', 'exit'], console=console).split()
                            if userInput[0] == 'exit':
                                exit_flag[0] = True
                                continue
                            elif userInput[0] == 'home':
                                continue
                            if len(userInput) == 1 and userInput[0] == 'activate':
                                osc_send(oscbuildparse.OSCMessage(address, ',s', ['activate']), 'scOSCClient')
                                # TODO make it so that it needs confirmation from supercollider to execute
                                instrDict[name]['ccActivated'] = True
                                console.print(f'[green]󰼁 {name} [bold]\\[cc][/green][/bold]: [cyan2 italic]activated\n')
                        elif instrDict[name]['ccActivated'] == True:
                            userInput = Input.ask(f'[blue]󰼂 {name} [bold]\\[cc][/bold] (activated)[/blue]', choices=['deactivate', 'home', 'exit'], console=console).split()
                            if userInput[0] == 'exit':
                                exit_flag[0] = True
                                continue
                            elif userInput[0] == 'home':
                                continue
                            if len(userInput) == 1 and userInput[0] == 'deactivate':
                                osc_send(oscbuildparse.OSCMessage(address, ',s', ['deactivate']), 'scOSCClient')
                                # TODO make it so that it needs confirmation from supercollider to execute
                                instrDict[name]['ccActivated'] = False
                                console.print(f'[green]󰼁 {name} [bold]\\[cc][/green][/bold]: [orange1 italic]deactivated\n')
                    case 'destroy':
                        address = instrDict[name]['instanceAddress']
                        if len(userInput) == 1:
                            osc_send(oscbuildparse.OSCMessage(address, ',s', ['destroy']), 'scOSCClient')
                            # TODO make it so that it needs confirmation from supercollider to execute
                            names.remove(name)
                            del instrDict[name]

        case 'exit':
            outport.panic()
            outport.close()
            if midiRec[0] == True:
                stop_midi_recording(midiRecFileName[0])
                console.print(f'[green]󰼁 midi recording of [italic]\'{midiRecFileName[0]}\'[/green][/italic]: [orange1 italic]stopped\n')
            osc_send(oscbuildparse.OSCMessage('/instruments', ',s', ['kill']), 'scOSCClient')
            time.sleep(1.0)
            finished = True
            # TODO add confirmation from supercollider
            break


# try:
#     while True:
#         userInput = input('󰼂 ').split() # 󰼂󰼁
#         if userInput[0] == 'address':
#             oscAddr = userInput[1]
#             if len(userInput) > 2:
#                 oscComm = userInput[2:]
#         elif oscAddr:
#             oscComm = userInput
#         else:
#             print('provide OSC address')

#         print(oscAddr)
#         print(oscComm)

#         osc_send(oscbuildparse.OSCMessage(oscAddr, None, oscComm), 'scOSCClient')

#         for x in range(10):
#             osc_process()
#             time.sleep(0.001)
# except KeyboardInterrupt:
#     osc_terminate()



