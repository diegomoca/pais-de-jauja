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
                // OSC functions listening to new object's address
                oscFunctions: {
                    |self|
                    [
                        OSCFunc.newMatching({
                            // incoming message to instrument instance's address
                            |msg|

                            var command, oscFunc;

                            // command
                            command = msg[1].asSymbol;
                            // this osc function
                            oscFunc = self[\oscFunctions];

                            if(command == \destroy, {
                                self.harpa.keyboardDeactivate;
                                self.harpa.ccDeactivate;
                                oscFunc.do{ |item| item.free };
                                ~harpas.removeAt(self.id)
                                // warn if "command" is unknown
                            }, {["unknown command", self.id, command].warn})
                        // path for new instance
                        }, (path +/+ self.id.asString).asSymbol),

                        OSCFunc.newMatching({
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

                        OSCFunc.newMatching({
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
            // runs the oscFunctions method and stores it as an array at the same key
            ~harpas[id][\oscFunctions] = ~harpas[id].oscFunctions;
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

~test.sendMsg("/instruments/harpa", "create", "harpa2")
~test.sendMsg("**/harpa2/keyboard", "activate")
~test.sendMsg("**/harpa2/keyboard", "deactivate")
~test.sendMsg("**/harpa2/cc", "activate")
~test.sendMsg("**/harpa2/cc", "deactivate")
~test.sendMsg("**/harpa2", "destroy")


OSCFunc({ |msg| msg.postln }, '/test')


