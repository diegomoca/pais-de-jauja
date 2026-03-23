import time
import mido

mid = mido.MidiFile()
track = mido.MidiTrack()
mid.tracks.append(track)

initTime = time.time()
lastTime = [0.0]

def on_midi(msg):
    currTime = time.time() - initTime
    deltaTime = currTime - lastTime[0]
    lastTime[0] = currTime
    data = msg.dict()
    data["time"] = mido.second2tick(deltaTime, 480, 500000)
    track.append(mido.Message(**data))
    print(msg)

inports = [mido.open_input(name, callback=on_midi) for name in mido.get_input_names()]

while True:
    if input() == "end":
        for inport in inports:
            inport.close()
        mid.save("test.mid")
        break
