import mido

outport = mido.open_output('mido', virtual=True)
playing_midi = [False]

def start_midi_playback(filename):
    playing_midi[0] = True
    for msg in mido.MidiFile(filename).play():
        outport.send(msg)
        if not playing_midi[0]:
            outport.panic()
            break

def stop_midi_playback():
    playing_midi[0] = False
