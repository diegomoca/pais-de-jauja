import mido

outport = mido.open_output('mido', virtual=True)

for msg in mido.MidiFile('test.mid').play:
    outport.send(msg)
