const HISTORIANDATATABLE = "ThunderboardHistorian";
//   - if the temperature is > the average of the entire set of messages, then send it to platform
//   - save to Historian Table
//   - remove topic from Queue
function ProcessEnvironment(req, resp){
    //log(JSON.stringify(req));
    ClearBlade.init({ request: req });
    
    /*
    if (! ClearBlade.isEdge()) {  // don't run on platform 
        log ("ProcessEnvironmentTopic: trying to run on the platform. Exiting") ;
        resp.error ("ProcessEnvironmentTopic: trying to run on the platform. Exiting") ;
    }
   */
   
   var topic , rc;
    if (req.params.topic) {
        topic = req.params.topic; //Topic
    } else {
        topic = "thunderboard/environment/20000" ;
    }

    log ("ProcessEnvironment: topic is " + topic) ;
    var msg = ClearBlade.Messaging();

    msg.getAndDeleteMessageHistory(topic, 0, null, null, null, function(err, body) {
	//msg.getMessageHistory(topic, null, 0, function(err, body) {
	    if(err) {
	        // no way to send return codes from functions
	        log ("message history error : " + body) ;
	        resp_error ("Unexpected getMessageHistory error") ;
		} else {
 		    //log(body);
 		    if ( body.length < 1 ) {  // no messages to process, this is a safety check
 		        log("no messages to process...  ") ;
 		        resp.success ("ProcessEnvironment: no messages on topic") ;
 		    } 
 		    var temp=[], sound=[], pressure=[], humidity=[] ;
		    var atemp, asound, apressure, ahumidity ;
            var api = isMessageDelete(body) ;
	        // read all the data points so we can do math on them	    
		    for (var i = 0; i<body.length; i++){
		        var message = body[i];
		        if (api) {
		            message = JSON.parse(message.payload);
		        } else {
                    message = JSON.parse(message.message);
		        }
			    temp.push(message.temperature);
			    sound.push(message.sound);
			    pressure.push(message.pressure);
			    humidity.push(message.humidity);
			}
			// apply statistic library on the data
			atemp = average(temp);
		    asound = average(sound);
		    apressure = average(pressure);
		    ahumidity = average(humidity);
			log("stddev temp = " + stdDev(temp) + " pressure " + stdDev(pressure) + " sound " + stdDev(sound) + " humidity " + stdDev(humidity)) ;
		    log("average temp = " + atemp + " pressure " + apressure + " sound " + asound + " humidity " + ahumidity ) ;
		    // now loop again and send message to platform queue if it passes the threshold
		    var k = 0;
		    topic = topic + "/_platform" ; 
		    for (var j = 0; j<body.length; j++){
		        if (api) {
		            message = JSON.parse(body[j].payload);
			    } else {
		            message = JSON.parse(body[j].message);
		        }
		        if ( message.temperature > atemp || message.sound > asound || message.humidity > ahumidity || message.pressure > apressure ) {
		        //if ( message.temperature > atemp ) {
		                log ("sending message to platform" + JSON.stringify(body[j])) ;
		                k++ ;  // count how many
		                //    message.send-date is the timestamp, like     "send-date": 1507672664 
		                if (api) {
		                    message["send-date"] = body[j]["time"] ;
		                } else {
		                    message["send-date"] = body[j]["send-date"] ;
		                }
		                //log("done:" + b);
		                var c = JSON.stringify(message) ;
		                //log (c );
	                    log("Publishing topic: " + topic + " with payload " + c );
                        msg.publish(topic, c);
		        }
			}
	        log ("Sending [" + k + "] out of [" + body.length + "]") ;
		    // now send to Historian Table
		    m = BuildDeviceCollectionArray ( topic, body) ;
            rc = "ProcessEnvironment: processed " + k + " records" ;
            log("Creating Historian Record");
            insertHistoricalRecord(m);
        } // end of else
        resp.success(rc) ;
	});  // end of function
}

function isMessageDelete (body) {
    // Assume the body is all the same array format
    // the challenge is depending on which API call, the JSON payload is different
    // See GetMessages for which API call is used
    if ( "message" in body[0]) {
        return false;
    } else {
        return true;
    }
}

function BuildDeviceCollectionArray (topic, body) {
	var m = [] ;
	k = 0;
	for (i=0; i < body.length; i++ ) {
		k++ ;
		var deviceData = {};
		var d, t;
		var api = isMessageDelete(body) ;
		// depending on the body payload, parse out what we need
		if (api) {
		    d = JSON.parse(body[i]["payload"]) ;
		    t = body[i]["time"] ;
		} else {
		  	d = JSON.parse(body[i]["message"]) ;  
		  	t = body[i]["send-date"] ;
		}
        //Breakout the fields we want into an object
        deviceData.deviceid = getDeviceId(topic);
        deviceData.recorddate = t ; // set the timestamp from the message
        deviceData.ambientlight = d.ambientLight;
        deviceData.co2 = d.co2;
        deviceData.humidity = d.humidity;
        deviceData.pressure = d.pressure;
        deviceData.sound = d.sound;
        deviceData.battery = d.battery;
        deviceData.temperature = d.temperature;
        deviceData.voc = d.voc;
        deviceData.uvindex = d.uvIndex;
       //log(JSON.stringify(deviceData));
        m.push(deviceData) ;
	}
	return m;
}	

function getDeviceId (topic) {
    var array = topic.split('/'); 
    var deviceid = "0";
    if ( array[0] == "thunderboard" && array[1] == "environment" ) {
        deviceid = array[2];
        //log ("got deviceId as: " + deviceid ) ;
    } else {
        log ("getDeviceId error: " + topic);
        return "unknown" ;
    }
    return deviceid ;
}
//Function that can be invoked to insert the sensor data into the "SensorHistorian" data collection
function insertHistoricalRecord(deviceData) {
    var historianCollection = ClearBlade.Collection({ collectionName: HISTORIANDATATABLE });
    //log("insertHistoricalRecord: " + JSON.stringify(deviceData));
    historianCollection.create(deviceData, function(err, data) {
        if (err) {
            log("failed to insert into collection: " + JSON.stringify(data));
            resp.error("insertHistoricalRecord: failed to insert into collection");
        } else {
            return true; //_resp.success("Record Inserted");
        }
    });
}