function AddThunderboardDevice(req, resp){
    
    log("AddThunderboardDevice");
    
    ClearBlade.init({request: req});
    
    log(JSON.stringify(req));
    //log("going into parse");
   
    var body ;
    
    if ( req.params.body ) {
        body = JSON.parse(req.params.body) ;  // this is sent by the trigger
        log(req.params.body);  // failing here somewhere
        deviceId = body.deviceId;
        gatewayName = body.topicName ;
    } else {
        //see addDeviceToPlatform in tbscanner.py
        body ={
            "gatewayAddress": "B8:27:EB:26:6E:C8",
            "gatewayName": "ThunderPi",
            "deviceAddress": "00:0b:57:1a:7c:34",
            "deviceType": "Thunder Sense #31796",
            "deviceAddrType": "public",
            "deviceId": "31796",
            "connectionType": "bluetooth",
            "command": "ReadEnv",
            "status": "New",
            "topicName": "thunderboard"
        }
    }

    if ( body.status != "New") {
        log("Unknown command in payload. Expected 'New': " + JSON.stringify(data)) ;
        resp.error("Unknown command in payload. Expected 'New' " + JSON.stringify(data)) ;
    }
    
    // Check device table for the existance of the device. Send 'Authorized in the status to make things happen'

    ClearBlade.getDeviceByName(body.deviceId, function(err, data) {
		if(err){
			log("Unable to get device: " + JSON.stringify(data)) ;
			resp.error("Unable to get device: " + JSON.stringify(data))
		} else {
			log(JSON.stringify(data));
			var topic = body.gatewayName +"/command/" + body.deviceId;
	        var payload = {"command": "ReadEnv", "status": "Authorized", "gatewayName": body.gatewayName, "deviceId": body.deviceId, "deviceAddress": body.deviceAddress, "deviceType": body.deviceType, "deviceAddrType": body.deviceAddrType};
	        var msg = ClearBlade.Messaging();
	        log("Publishing topic: " + topic + " with payload " + JSON.stringify(payload));
            msg.publish(topic, JSON.stringify(payload));
            resp.success("Done");  
		}
	});
}