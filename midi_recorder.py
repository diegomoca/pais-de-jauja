import time
import mido

inports = [[None]]
initTime = [None]
lastTime = [None]

midiFile = [None]
track = [None]

def on_midi(msg):
    currTime = time.time() - initTime[0]
    deltaTime = currTime - lastTime[0]
    lastTime[0] = currTime
    msg = msg.dict()
    msg["time"] = mido.second2tick(deltaTime, 480, 500000)
    track[0].append(mido.Message(**msg))
    print(msg)

def start_midi_recording():
    initTime[0] = time.time()
    lastTime[0] = 0.0
    midiFile[0] = mido.MidiFile()
    track[0] = mido.MidiTrack()
    midiFile[0].tracks.append(track[0])
    inports[0] = [mido.open_input(name, callback=on_midi) for name in mido.get_input_names()]

def stop_midi_recording(filename):
    for inport in inports[0]:
        inport.close()
    currTime = time.time() - initTime[0]
    deltaTime = currTime - lastTime[0]
    print(deltaTime)
    deltaTime = mido.second2tick(deltaTime, 480, 500000)
    track[0].append(mido.MetaMessage('end_of_track', time=deltaTime))
    midiFile[0].save(filename)
