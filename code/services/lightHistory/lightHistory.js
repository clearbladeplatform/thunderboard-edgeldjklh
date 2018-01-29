function lightHistory(req, resp){
    var clearblade = ClearBlade.init({request:req});
    var timeInMs = Date.now();
    //timeInMs = Math.round(new Date().getTime()/1000.0);
    req.params.deviceid="1735732";
    log ("deviceid is: "+req.params.deviceid);
    var msg = ClearBlade.Messaging();
    log("Time: " + timeInMs)
    
// 	msg.getMessageHistory("thunderboard/1735258/io", 1, (timeInMs/1000), null,null, function(err, body) {
// 		if(err) {
// 			resp.error("message history error : " + JSON.stringify(body));
// 		} else {
//  			// resp.success(body);
// 			var points=[];
// 			for (var i = 0; i<body.length; i++){
// 			    var message = body[i];
// 			    var x= message["send-date"];
// 			    message = JSON.parse(message.message);
// 			 //   resp.success("here with message:"+JSON.stringify(message));
			    
// 			    var point = {"x":i,"y":message.ambientLight};
// 			    points.push(point);
// 			}
// 			resp.success(points);
			interestingData = [];
    		var getRandomArbitrary= function (min, max) {
              return Math.random() * (max - min) + min;
            }
    
    		for (var i =0; i<25; i++) {
    		  //interestingData.push({"x":i,"y":getRandomArbitrary(834,875)});
    		  interestingData.push({"x":i,"lumens":getRandomArbitrary(10,100)}); 
    		}
			resp.success(interestingData);
// 		}
// 	});
}