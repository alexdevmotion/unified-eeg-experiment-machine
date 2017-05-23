/**
 * This is an example from the readme.md
 * On windows you should run with PowerShell not git bash.
 * Install
 *   [nodejs](https://nodejs.org/en/)
 *
 * To run:
 *   change directory to this file `cd examples/debug`
 *   do `npm install`
 *   then `npm start`
 */
var OpenBCIBoard = require('openbci').OpenBCIBoard;
var portPub = 'tcp://127.0.0.1:3004';
var zmq = require('zmq-prebuilt');
var socket = zmq.socket('pair');
var debug = false; // Pretty print any bytes in and out... it's amazing...
var verbose = false; // Adds verbosity to functions
var isDaisy = true;
var withSync = false;

var ourBoard = new OpenBCIBoard({
    boardType: isDaisy ? 'daisy' : 'default',
    debug: debug,
    hardSet: isDaisy,
    verbose: verbose
});

var sampleRate = 0;
var headsetFound = false;
var sendStream = false;

ourBoard.on('error', (err) => {
    console.log(err);
});

var synced = false;
var port = 0;
var notifiedStream = false

var doConnect = portName => {
    if (portName) {
        ourBoard.connect(portName)
            .then(() => {
                ourBoard.once('ready', () => {
                    sampleRate = ourBoard.sampleRate();
                    verbose && console.log(`Sample rate: ${sampleRate}`)
                    var usingVersionTwoFirmware = ourBoard.usingVersionTwoFirmware()
                    verbose && console.log(`Using version 2: ${usingVersionTwoFirmware}`)
                    headsetFound = usingVersionTwoFirmware && ((sampleRate == 125 && isDaisy) || (sampleRate == 250 && !isDaisy));
                    console.log(`Headset found: ${headsetFound}`)
                    ourBoard.streamStart();
                    sendReady(true)
                });
            })
            .catch(err => {
                sendReady(false)
                verbose && console.log(`connect: ${err}`);
            });
    } else {
        sendReady(false)
        verbose && console.log('Unable to auto find OpenBCI board');
    }
}

ourBoard.autoFindOpenBCIBoard().then(doConnect)
    .catch(err => {
        sendReady(false)
        verbose && console.log(`autofind: ${err}`);
    });

var sendReady = ready => {
    sendToPython({ // let python know i'm ready
        command: 'ready',
        message: ready
    });
};

var sampleFunc = sample => {
    if (!synced && withSync) {
        if (verbose) {
            console.log(`trying to sync`)
        }
        ourBoard.syncClocksFull().then(syncObj => {
            // Sync was successful
            if (syncObj.valid) {
                synced = true;
                if (verbose) {
                    console.log(`syncObj`, syncObj);
                }
            } else {
                if (verbose) {
                    console.log(`Was not able to sync... retry!`);
                }
            }
        })
        .catch(err => {
            if (verbose) {
                console.log("Error syncing")
            }
        });
    }

    if (!withSync || sample.timeStamp) { // true after the first successful sync
        if (withSync && sample.timeStamp < 10 * 60 * 60 * 1000) { // Less than 10 hours
            if (verbose) {
                console.log(`Bad time sync ${sample.timeStamp}`);
            }
            synced = false;
        } else  {
            if (!notifiedStream) {
                console.log('Node is ready to stream')
                sendToPython({
                    command: 'stream'
                });
                notifiedStream = true
            }
            if (sendStream) {
                sendToPython({
                    command: 'sample',
                    message: sample
                });
            }
        }
    }
};

// Subscribe to your functions
ourBoard.on('sample', sampleFunc);

// ZMQ fun

socket.bind(portPub, function (err) {
    if (err) throw err;
    console.log(`Node is bound to: ${portPub}`);
});

/**
 * Used to send a message to the Python process.
 * @param  {Object} interProcessObject The standard inter-process object.
 * @return {None}
 */
var sendToPython = (interProcessObject) => {
    if (verbose) {
        console.log(`<- out ${JSON.stringify(interProcessObject)}`);
    }
    if (socket) {
        socket.send(JSON.stringify(interProcessObject));
    }
};

var receiveFromPython = (rawData) => {
    try {
        let body = JSON.parse(rawData); // five because `resp `
        processInterfaceObject(body);
    } catch (err) {
        console.log('in -> ' + 'bad json');
    }
};

socket.on('message', receiveFromPython);

var sendStatus = () => {
    sendToPython({'action': 'active', 'message': 'ready', 'command': 'status'});
};

sendStatus();

/**
 * Process an incoming message
 * @param  {String} body   A stringify JSON object that shall be parsed.
 * @return {None}
 */
var processInterfaceObject = (body) => {
    switch (body.command) {
        case 'status':
            processStatus(body);
            break;
        case 'headset':
            sendToPython({'message': headsetFound, 'command': 'headset'});
            break;
        case 'impedance':
            ourBoard.impedanceTestAllChannels();
            break;
        case 'start':
            sendStream = true;
            console.log('Node will start streaming')
            break;
        case 'stop':
            ourBoard.streamStop()
            console.log('Node will stop streaming')
        default:
            unrecognizedCommand(body);
            break;
    }
};

/**
 * Used to process a status related command from TCP IPC.
 * @param  {Object} body
 * @return {None}
 */
var processStatus = (body) => {
    switch (body.action) {
        case 'started':
            console.log(`python started @ ${body.message}ms`);
            break;
        case 'alive':
            console.log(`python duplex communication test completed @ ${body.message}ms`);
            break;
        default:
            unrecognizedCommand(body);
            break;
    }
};

function unrecognizedCommand(body) {
    console.log(`unrecognizedCommand ${body}`);
}

function exitHandler(options, err) {
    if (options.cleanup) {
        if (verbose) console.log('clean');
        /** Do additional clean up here */
    }
    if (err) console.log(err.stack);
    if (options.exit) {
        if (verbose) console.log('exit');
        ourBoard.disconnect().catch(console.log);
    }
}

if (process.platform === 'win32') {
    const rl = require('readline').createInterface({
        input: process.stdin,
        output: process.stdout
    });

    rl.on('SIGINT', function () {
        process.emit('SIGINT');
    });
}

// do something when app is closing
process.on('exit', exitHandler.bind(null, {
    cleanup: true
}));

// catches ctrl+c event
process.on('SIGINT', exitHandler.bind(null, {
    exit: true
}));

// catches uncaught exceptions
process.on('uncaughtException', exitHandler.bind(null, {
    exit: true
}));
