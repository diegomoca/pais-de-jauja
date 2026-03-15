// testing gui
(
    // server gui
    s.makeWindow;
    s.window.alwaysOnTop_(true);


    // node tree graph
    ~plotTree = View(nil, Rect(0, 0, 300, 1000)).front.alwaysOnTop_(true);
    s.plotTreeView(parent: ~plotTree);


    // signal meter
    ~meter = ServerMeter.new(s, 0, 2);
    ~meter.window.alwaysOnTop_(true)
)
// MIDI debug
MIDIFunc.trace(true)
MIDIFunc.trace(false)

x = Environment.make({"instruments/harpa/source/main.scd".loadRelative});
y = Environment.make({"instruments/harpa/source/main.scd".loadRelative});
a.environments(activeEnvironments: [x])
c.free
x
topEnvironment === currentEnvironment
currentEnvironment.pop
Environment.stack
currentEnvironment.pop
while { currentEnvironment !== topEnvironment } { currentEnvironment.pop }

(freq: 761).play


a.([~x])
a = nil
~harpa2.push;
currentEnvironment;

~harpa1
~harpa2

(
// define midi notes to play strings
var stringKeys = [49, 51, 54, 56, 58, 61, 63, 66, 68, 70, 72];

// initial string parameters
// tuning (traditional pentatonic scale)
var striFreq = [100, 112.5, 126.5625, 150.0, 168.75, 200.0, 225.0, 253.125, 300.0, 337.5, 400.0],
    // initial body parameters
    bodVol = [1, 0.5],
    bodFreq = [12.5, 400],
    bodDamp = [0.8, 0.2],
    holdMode = 0;

a = (
    environments: {
        |self, activeEnvironments|
        // MIDIDefs to open and close string's ADSR
        // and to create a new body in case it doesn't exist
        c = MIDIdef.noteOn(\stringGateOpen,{
            |vel, note|
            activeEnvironments.do{
                |environment|
                environment.use{
                    item.postln;
                    // cycle through all the string activating keys and execute triggers
                    // and releases if input from midi keyboard matches one of them
                    stringKeys.do({
                        // item is the item in the arrangement stringKeys and count is a counter
                        arg item, count;
                        if(note == item){
                            // create new bodies if they don't exist
                            ~bodyArr.do({
                                arg item, count;
                                if (item == nil, {
                                    ~bodyArr.put(count, Synth(\body, [
                                        \in, ~bodyBus.subBus(count * 2, 2).index,
                                        // body parameters
                                        \bodVol, bodVol[count],
                                        \bodFreq, bodFreq[count],
                                        \bodStructBus, ~bodStructBus,
                                        \bodBrightBus, ~bodBrightBus,
                                        \bodDamp, bodDamp[count],
                                    ], ~bodiesGroup).onFree({~bodyArr[count] = nil}))
                                });
                            });
                            // create a new voice or retrigger if one already exist
                            if(~keyArr[count] == nil, {
                                // create new string synthdef if it doesn't exist
                                ~keyArr.put(count, Synth(\string, [
                                    // ADSR1 parameters
                                    \attack1Bus, ~attack1Bus,
                                    \decay1Bus, ~decay1Bus,
                                    \sustain1Bus, ~sustain1Bus,
                                    \release1Bus, ~release1Bus,
                                    \curve1Bus, ~curve1Bus,
                                    // string parameters
                                    \striFreq, striFreq[count],
                                    \striVolBus, ~striVolBus,
                                    \accentBus, ~accentBus,
                                    \striStructBus, ~striStructBus,
                                    \striBrightBus, ~striBrightBus,
                                    \striDampBus, ~striDampBus,
                                    // trigger parameters
                                    \trigMethBus, ~trigMethBus,
                                    \trigFreqBus, ~trigFreqBus,
                                    \trigDurBus, ~trigDurBus,

                                    // "routing"
                                    // string panning depending on key
                                    // 0 = -1, 10 = 1 for 11 strings 0-10
                                    \panning, (count * 1/5) * - 1,
                                    // determine which amount of each string goes into each body
                                    \bodySelect, (count * 9/50) - 0.9,

                                    \t_retrigger, ~trigger,
                                    \out, ~bodyBus.index,
                                    \triggerMethod, 0,

                                ], ~stringsGroup).onFree({
                                    // function to run everytime one of the strings are freed
                                    // reset the key index back to nil
                                    x.use{
                                        ~keyArr[count] = nil;
                                        // detect if all the strings are freed and perform the function
                                        if(~keyArr.every({ |item| item == nil }) == true, {
                                            // send message to bodies when all strings are free
                                            ~bodyArr.do({ |item| item.set(\stringsFree, 1)})
                                        })
                                    }
                                }))
                            }, {
                                // if it exist, change its parameter
                                ~keyArr.at(count).set(\t_retrigger, ~trigger, \gate, 1)
                            })
                        };
                    });
                };
                // cycle modes
                if(note == 57){
                    ~oscClient.sendMsg("/mode", "prev")
                };
                if(note == 62){
                    ~oscClient.sendMsg("/mode", "next")
                };
                // transpose by cycle interval "pseudo-octave"
                if(note == 48){
                    ~oscClient.sendMsg("/transposition/cycle_interval", "down")
                };
                if(note == 71){
                    ~oscClient.sendMsg("/transposition/cycle_interval", "up")
                };
                // transpose by generator interval
                if(note == 59){
                    ~oscClient.sendMsg("/transposition/generator_interval/transpositionDirection", "down")
                };
                if(note == 60){
                    ~oscClient.sendMsg("/transposition/generator_interval/transpositionDirection", "up")
                };
                if(note == 52){
                    ~oscClient.sendMsg("/transposition/generator_interval/degreeDirection", "down")
                };
                if(note == 67){
                    ~oscClient.sendMsg("/transposition/generator_interval/degreeDirection", "up")
                };
            }
        });

        MIDIdef.cc(\holdMode, {
            |val, num|
            activeEnvironments.do{
                |item|
                environment.use{
                    if(holdMode == 0, {holdMode = 1}, {holdMode = 0});
                    holdMode.postln
                }
            }
        }, ccNum: 64);

        MIDIdef.noteOff(\stringGateClose, {
            |vel, note|
            activeEnvironments.do{
                |item|
                environment.use{
                    stringKeys.do({
                        arg item, count;
                        if(note == item && {holdMode == 0},{
                            // operate only if synthdef exists
                            if(~keyArr[count]!= nil, {
                                ~keyArr.at(count).set(\gate, 0)
                            })
                        });
                    })
                }
            }
        });
    }
)
)











(Environment.make{
    ~test = 1;
    ~test.postln
})

~test = 0
~test

(Environment.make{
    ~test = 1
}.use{
    ~test.postln
})

(~envTest = Environment.make{
    "testA.scd".loadRelative
})

~envTest.use{~testB.postln}

~testB.postln


~envTest.pop
~envTest.push;
~test.postln
currentEnvironment


// harpa.("harpa-1")
// arturia.("harpa-1", "full")

// Instrument.new(\harpa-1, "harpa", "minilabMKII", "full")
// harpa-1.arturia.knobs.mode("influx")


// (a = (
//     incrementar: {
//         |self| self.numero = self.numero + 1;
//         postln(self.numero)
//     },
//     disminuir: {
//         |self| self.numero = self.numero - 1;
//         postln(self.numero)
//     }
// );)

// (a = {
//     |numero|
//     (
//         numero: numero,
//         incrementar: {
//             |self| self.numero = self.numero + 1;
//             postln(self.numero)
//         },
//         disminuir: {
//             |self| self.numero = self.numero - 1;
//             postln(self.numero)
//         }
//     )
// })



// a.(0)
// a.incrementar
// a.disminuir

// var harpa1 = harpa.("miniLabMKII")
