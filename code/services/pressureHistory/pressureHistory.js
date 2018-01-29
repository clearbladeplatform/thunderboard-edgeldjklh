function pressureHistory(req, resp){
    var clearblade = ClearBlade.init({request:req});
    var timeInMs = Date.now();
    //timeInMs = Math.round(new Date().getTime()/1000.0);
    // req.params.deviceid="1735732";
    log ("deviceid is: "+req.params.deviceid);
    var msg = ClearBlade.Messaging();
	msg.getMessageHistory("thunderboard/environment/"+req.params.deviceid+"/_platform", timeInMs, 25, function(err, body) {
		if(err) {
			resp.error("message history error : " + JSON.stringify(data));
		} else {
 			// resp.success(body);
			var points=[];
			for (var i = 0; i<body.length; i++){
			    var message = body[i];
			    message = JSON.parse(message.message);
			 //   resp.success("here with message:"+JSON.stringify(message));
			    var point = { 
			        "pressure": message.pressure / 100,
			        "temperature": Math.round(message.temperature * 9/5 + 32),
			        "humidity": message.humidity,
			        "co2": message.co2,
			        "voc": message.voc,
			        "light": message.light,
			        "uv": message.uv,
			        "sound": message.sound,
			        "battery": message.battery
			    } ;
			    points.push(point);
			}
			resp.success(points);
		}
	});
}