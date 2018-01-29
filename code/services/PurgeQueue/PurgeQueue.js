function PurgeQueue(req, resp){

    var timeInSecs = Math.round(new Date().getTime()/1000.0);
    ClearBlade.init({request: req});
    var msg = ClearBlade.Messaging();

    var bcallback = function (err, data) {
		if(err) {
			resp.error("Unable to retrieve current topics: " + JSON.stringify(data));
		} else {
		}
    };
    
    var callback = function (err, data) {
		if(err) {
			resp.error("Unable to retrieve current topics: " + JSON.stringify(data));
		} else {

			log(data);
			
			for (var i=0; i<data.length; i++){
 			    var topic = data[i];
 			    var array = topic.split('/');
 			    if ( array[0] != "thunderboard" || array.length < 3) {
 			        continue ;
 			    }
 			    var plat = array[2].split('_') ;
 			    log (array);
 			    log (plat);
                if ( array[1] == "environment" && plat[1] == "platform" ) {
                    log ("got matching queue: " + topic ) ;
                    // hopefully only process one message
                    msg.getAndDeleteMessageHistory(topic, 0, timeInSecs, null, null, bcallback);
                }
                log("topic:" + topic);
 			}
		}
    };

    msg.getCurrentTopics(callback);
    resp.success("done");
}