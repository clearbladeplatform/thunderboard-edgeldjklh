// this is meant to be called by a timer to fire every hour (or day) to purge the message queues
// this is to run on either the edge or the platform
// topic format:   thunderboard/environment/devid/_platform
function PurgeEnv(req, resp){

    var timeInSecs = Math.round(new Date().getTime()/1000.0);
    ClearBlade.init({request: req});
    var msg = ClearBlade.Messaging();

    var bcallback = function (err, data) {
		if(err) {
			resp.error("Unable to read message queue topic: " + JSON.stringify(data));
		} else {
		    // do nothing with the topics that are returned.
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
 			    for (j=0; j < array.length; j++ ) {
 			        if ( array[j] == "_platform") { 
                        log ("got matching queue: " + topic ) ;
                        msg.getAndDeleteMessageHistory(topic, 0, timeInSecs, null, null, bcallback);
                    }
                //log("topic:" + topic);
 			    } // end of for j
			} // end of for i
		}  // end of else
    }; // end of callback

    msg.getCurrentTopics(callback);
    resp.success("done");
}