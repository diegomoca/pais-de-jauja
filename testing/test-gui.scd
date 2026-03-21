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
