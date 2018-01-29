function CreateCollection(req, resp){

    // This function is an administrative function to copy message queue data and create collection based on the JSON
    // structure of the messages.  It's not really needed but it is nice library to have.
    
    var topic = "thunderboard/environment/20001" ;  // hardwire for now
    var columns;  // the GetTopicColumns call will fill this in with 1 messsage
    var collection = "ThunderboardHistorian" ;
    var primary_key = "deviceid" ;  // in this case, use the last of the topic but better to hard code it
    var primary_key_value = "20001" ;   
    
    //log("New item: " + JSON.stringify(newItem));
    
    ClearBlade.init({ request: req });

    /*  0) Options to consider:  topic, All = do all, FirstN, SkipN, FromTime
            Messaging.getMessageHistoryWithTimeFrame(topic, count, last, start, stop, callback)
            Messaging.getMessageHistory(topic, last, count, callback)
        1) Read request and determine message queue topic
        2) Open queue and read the last topic, assuming it is the definition of the others
        3) Now parse out each message and identify column names and values
        4) Verify that the 10 messages have the same format or send out errors
        5) Create Collection
                - use the last of the topic to use a device ID
                ? error if exists?  Yes
        6) Loop through column names and add columns (int, string, timestamp)
        7) Now Loop through list and add rows with collection.create
        8) Start another loop and read the rest of the message queue
    */

    //This will create a blank collection
    var CreateCollection = function(title) {
        ClearBlade.newCollection(title, function(err, data) { 
            if(err) {
                log("Error creating blank collection: " + data);
                resp.error({error: true, result: data});
            } else {
                //resp.success({error: false, result: data});
            }
        });
    };
    
    var AddColumn = function (title, column_name, column_type) {
        // column_type in ("Int", "string", "timestamp")
        var type = String(column_type);
        column_name = column_name.toLowerCase();  // Do this now since Collections don't do Upper Case
        var column = {
            name: column_name, 
            type: type
        };
        log("AddColumn: " + title + " column: " + column_name) ;
        var collection = ClearBlade.Collection({collectionName: title}); 
        collection.addColumn(column, function(err, data) { 
            if(err) {
                log("Error adding column: " + column_name + " to collection: " + data);
                resp.error({error: true, result: data});
            } else {
                log("Successfully added column: " + data);
                //resp.success({error: false, result: data});
            }
        });
    };
    
    var PrintColumns = function() {
        for (var key in columns) {
            if (columns.hasOwnProperty(key)) {
                log(key + " = " + columns[key]);
            }
        }  
    };
    
    var CreateNewCollection = function(name, columns) {
        CreateCollection(name);
        AddColumn(name, primary_key, "string") ;  // every table gets this
        AddColumn(name, "recorddate", "timestamp") ;  // every table gets this
        for (var key in columns) {
            if (columns.hasOwnProperty(key)) {
                log(key + " = " + columns[key]);
                AddColumn(name, key, "Int"); // default to Integer for every other column
            }
        }  
    };
    
    var GetTopicColumns = function(topic) {
        var timeInSecs = Math.round(new Date().getTime()/1000.0);
        var msg = ClearBlade.Messaging();
        log("Time: " + timeInSecs) ;
 	    msg.getMessageHistory( topic, timeInSecs, 1, function(err, body) {
 		    if(err) {
 			    resp.error("message history error : " + JSON.stringify(body));
 		    } else {
 		        log ("body is:" + JSON.stringify(body) + " length: " + body.length ) ;
 		        // loop through each message
 			    for (var i = 0; i<body.length; i++){
 			        var message = body[i];
 			        //var ts = message["send-date"] ;
 			        //var dt = new Date(ts*1000);
 			        //log ("message is:" + message.message + " at " + dt ) ;
 			        //log ("time is: " + message.send-date) ;
 			        columns = JSON.parse(message.message) ;
 			    }
 		    }
 		    //PrintColumns();
 		    CreateNewCollection(collection, columns) ;
 		    //WriteTopicToCollection (topic, collection) ;
 		    resp.success("got it done") ;
 	    });
    };
    
    var WriteTopicToCollection = function(topic, collection) {
        var timeInSecs = Math.round(new Date().getTime()/1000.0);  // start from right now
        var msg = ClearBlade.Messaging();
        log("WriteTopicToCollection: Time: " + timeInSecs) ;
 	    msg.getMessageHistory( topic, timeInSecs, 0, function(err, body) {  // get all of them
 		    if(err) {
 			    resp.error("message history error : " + JSON.stringify(body));
 		    } else {
 		        log ("body is:" + JSON.stringify(body) + " length: " + body.length ) ;
 		        // loop through each message
 		        var historianCollection = ClearBlade.Collection({ collectionName: collection });
 		        var callback = function(err, data) {
                    if (err) {
                        log(JSON.stringify(data));
                        resp.error("WriteTopicToCollection: Callback error: " + JSON.stringify(data));
                    } else {
                        //log(JSON.stringify(data));
                        //resp.success(data);
                        return true;
                    }
                };

 			    for (var i = 0; i<body.length; i++){
 			        var message = body[i];
 			        var ts = message["send-date"] ;
 			        var dt = new Date(ts*1000);
 			        //log ("message is:" + message.message + " at " + dt ) ;
 			        data = JSON.parse(message.message) ;
 			        var ndata = {};  // need to munge with data to insert into collection nicely
                    for (var key in data) {  // convert stuff to strings
                        if (data.hasOwnProperty(key)) {
                            var nkey = key.toLowerCase();  // Do this now since Collections don't do Upper Case
                            var nval = String(data[key]) ;
                            ndata[nkey] = nval;
                            //log(nkey + " = " + ndata[nkey]);
                        }
                    }
                    ndata[primary_key] = primary_key_value ;
                    ndata.recorddate = ts ;
                    log("WriteTopicToCollection: " + JSON.stringify(ndata)) ;
                    // Now write to the collection
                    historianCollection.create(ndata, callback);
 			    }
 		    }
 		    resp.success("WriteTopicToCollection: Created Collection: " + collection) ;
 	    });
    };
    
    GetTopicColumns(topic);
    
    resp.success("here with message:"+JSON.stringify(columns));
}