//# rdf 10/17
// this is an old version of code that updates the dev table with a new topic from the message queue, deletes the topic, and writes to history collection

const HISTORIANDATATABLE = "ThunderboardHistorian";
var _resp; //Global Resp Object
var _req; //Global Req Object

//Function to Create Device and insert into table

function createSensorDevice(deviceData) {
    
    log("createSensorDevice: DeviceData: " + JSON.stringify(deviceData));
        
    var deviceObject = {
        "active_key": deviceData.deviceid,  
        "type": "",
        "state": "",
        "enabled": false,
        "allow_key_auth": false,
        "allow_certificate_auth": true,
        "ambientlight": deviceData.ambientlight,
        "co2": deviceData.co2,
        "description": "",
        "humidity": deviceData.humidity,
        "pressure": deviceData.pressure,
        "sound": deviceData.sound,
        "battery": deviceData.battery,
        "temperature": deviceData.temperature,
        "voc": deviceData.voc,
        "uvindex": deviceData.uvindex,
        "lastupdate": new Date(Date.now()).toISOString()
    };
    //Check if the device exists, if not create it.
    var devname = deviceData.deviceid ;
    ClearBlade.getDeviceByName(devname, function(err, data) {
        if (err) {
            deviceObject.name = deviceData.deviceid;
            log(deviceObject);
            log("createSensorDevice: Unable to open device: " + JSON.stringify(data));
            ClearBlade.createDevice(devname, deviceObject, true, function(err, data) {
                if (err) {
                    log ("createSensorDevice: Not able to create device" + JSON.stringify(data)) ;
                    _resp.error("Unable to create device: " + JSON.stringify(data));
                } else {
                    log ("createSensorDevice: Created device") ;
                    insertHistoricalRecord();
                }
            });
        } else { //update historical record
            deviceObject.active_key = data.active_key;  // copy in the key to update it
            deviceObject.description = data.description ;
            deviceObject.type = data.type ;
            deviceObject.state = "connected";
            deviceObject.battery = String(deviceObject.battery) ;  /// hack due to Dev table wrong type
            log ("createSensorDevice: Updating device: " + JSON.stringify(deviceObject)) ;
            ClearBlade.updateDevice(devname, deviceObject, true, function(err, data) {
                if (err) {
                    log ("createSensorDevice: Error Updating device" + JSON.stringify(data) ) ;
                    _resp.error("Unable to update device: " + JSON.stringify(data));
                }
            });
        }
    });
}

//Function that can be invoked to insert the sensor data into the "SensorHistorian" data collection
function insertHistoricalRecord(deviceData) {
    var historianCollection = ClearBlade.Collection({ collectionName: HISTORIANDATATABLE });
    deviceData.recorddate = new Date(Date.now()).toISOString();
    log("insertHistoricalRecord: " + JSON.stringify(deviceData));
    historianCollection.create(deviceData, function(err, data) {
        if (err) {
            log("failed to insert into collection: " + JSON.stringify(data));
            _resp.error("failed");
        } else {
            return true; //_resp.success("Record Inserted");
        }
    });
}

//Topic Deletion function
function clearTopic(topic) {
    var timeInSecs = Math.round(new Date().getTime()/1000.0);
    var msg = ClearBlade.Messaging();
    log(topic);
    var callback = function(err, data) {
        if (err) {
            log(JSON.stringify(data));
            _resp.error("clearTopic error: " + JSON.stringify(data));
        } else {
            log("clearTopic: removing " + JSON.stringify(data));
            _resp.success(data);
        }
    };
    // hopefully only process one message
    msg.getAndDeleteMessageHistory(topic, 1, timeInSecs, null, null, callback);
}

//This code service is invoked by the uplinkPublish trigger whenever
// a message is published to the "actility/uplink" messaging topic
/*{
  "sound": 60,
  "co2": 333,
  "temperature": 4,
  "voc": 0,
  "battery": 15,
  "humidity": 70,
  "ambientLight": 26,
  "pressure": 1101,
  "uvIndex": 3
}*/

function ThunderboardMessageProcessor(req, resp) {
    //Assign Global Handlers
    _resp = resp;
    _req = req;
    //-----------------------------
    //log(JSON.stringify(req));
    ClearBlade.init({ request: req });
    var requestPayload = JSON.parse(req.params.body);
    // thunderboard/enivironment/30000 is the format for the message queue
    var topic = req.params.topic;
    var array = topic.split('/'); 
    var deviceid = "0";
    log("topic is" + topic);
    if ( array[0] == "thunderboard" && array[1] == "environment" ) {
        deviceid = array[2];
        log ("got deviceId as: " + deviceid ) ;
    } else {
        _resp.error("ThunderboardMessageProcessor error: " + topic);
    }
    var deviceData = {};
    //Breakout the fields we want into an object
    deviceData.deviceid = deviceid;
    deviceData.ambientlight = requestPayload.ambientLight;
    deviceData.co2 = requestPayload.co2;
    deviceData.humidity = requestPayload.humidity;
    deviceData.pressure = requestPayload.pressure;
    deviceData.sound = requestPayload.sound;
    deviceData.battery = requestPayload.battery;
    deviceData.temperature = requestPayload.temperature;
    deviceData.voc = requestPayload.voc;
    deviceData.uvindex = requestPayload.uvIndex;
    log(JSON.stringify(deviceData));
    log("Creating/Updating Sensor");
    createSensorDevice(deviceData);
    log("Creating Historian Record");
    insertHistoricalRecord(deviceData);
    //log("Delete topic after submission");
    //clearTopic(req.params.topic);
}