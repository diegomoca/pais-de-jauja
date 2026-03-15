(   
    // server gui
    s.makeWindow;
    s.window.alwaysOnTop_(true);


    // node tree graph
    ~plotTree = View(nil, Rect(0, 0, 300, 1000)).front.alwaysOnTop_(true);
    s.plotTreeView(parent: ~plotTree);


    // signal meter
    ~meter = ServerMeter.new(s, 0, 2);
    ~meter.window.alwaysOnTop_(true);
)

(s.waitForBoot{   
    MIDIClient.init;
    MIDIIn.connectAll;

    Require("instruments/harpa/source/main-test");

    // OSC UI for external control
    // dictionary containing instrument objects and OSC receivers
    ~harpas = ();
    // OSC function to call instrument class
    ~oscUI = OSCFunc.newMatching({
        // argument for incomming message
        |msg|

        // OSC address
        var path    = msg[0].asString,
        // command and object id received
            command = msg[1].asString,
            id      = msg[2].asSymbol;

        // if command is "create" then create a new object and an OSC address
        // respective to that object and store them in an array inside dictionary
        switch(command, "create", {
            // dictionary inside dictionary
            ~harpas[id] = (
                //instrument id
                id: id,
                // instrument object
                harpa: ~makeHarpa.(id),

                instrumentOSC: nil,
                // OSC functions listening to new object's address
                oscFunctions: {
                    |self|
                    self.instrumentOSC = [
                        OSCdef.newMatching((UniqueID.next).asSymbol, {
                            // incoming message to instrument instance's address
                            |msg|

                            var command, oscFunc;

                            // command
                            command = msg[1].asSymbol;

                            if(command == \destroy, {
                                // deactivate controls
                                self.harpa.keyboardDeactivate;
                                self.harpa.ccDeactivate;
                                // remove synths and groups
                                self.harpa.removeSynths;
                                // cut osc communication
                                // self.instrumentOSC.do{ |item| item.free };
                                // self.instrumentOSC = nil;
                                // remove instrument instance
                                // ~harpas.removeAt(self.id);
                                // self.harpa.postln;

                                // warn if "command" is unknown
                            }, {["unknown command", self.id, command].warn})
                        // path for new instance
                        }, (path +/+ self.id.asString).asSymbol),

                        OSCdef.newMatching((UniqueID.next).asSymbol, {
                            |msg|

                            var command;

                            // command
                            command = msg[1].asSymbol;

                            switch(command, \activate, {
                                self.harpa.keyboardActivate
                            }, \deactivate, {
                                self.harpa.keyboardDeactivate
                            }, {
                                ["unknown command", self.id, command].warn
                            })
                        }, (path +/+ self.id.asString +/+ "keyboard").asSymbol),

                        OSCdef.newMatching((UniqueID.next).asSymbol, {
                            |msg|

                            var command;

                            // command
                            command = msg[1].asSymbol;

                            switch(command, \activate, {
                                self.harpa.ccActivate
                            }, \deactivate, {
                                self.harpa.ccDeactivate
                            }, {
                                ["unknown command", self.id, command].warn
                            })
                        }, (path +/+ self.id.asString +/+ "cc").asSymbol)
                    ]
                }
            );
            // runs the oscFunctions method
            ~harpas[id].oscFunctions;
            // ~harpas[id].instrumentOSC.postln
        });
        [command, id].postln
        // path for instrument class
    }, '/instruments/harpa');
})

~test = NetAddr("localhost", 57120);

~test.sendMsg("/instruments/harpa", "create", "harpa1")
~test.sendMsg("**/harpa1/keyboard", "activate")
~test.sendMsg("**/harpa1/keyboard", "deactivate")
~test.sendMsg("**/harpa1/cc", "activate")
~test.sendMsg("**/harpa1/cc", "deactivate")
~test.sendMsg("**/harpa1", "destroy")
~harpas[\harpa1].postln

~test.sendMsg("/instruments/harpa", "create", "harpa2")
~test.sendMsg("**/harpa2/keyboard", "activate")
~test.sendMsg("**/harpa2/keyboard", "deactivate")
~test.sendMsg("**/harpa2/cc", "activate")
~test.sendMsg("**/harpa2/cc", "deactivate")
~test.sendMsg("**/harpa2", "destroy")


OSCFunc({ |msg| msg.postln }, '/test')


~harpas.value(\harpa1)
