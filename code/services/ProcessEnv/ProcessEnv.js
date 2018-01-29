function ProcessEnv(req, resp){
    
    var topics = [
        "thunderboard/environment/31796",
        "thunderboard/environment/20000",
        "thunderboard/environment/20001",
    ] ;

    ClearBlade.init({ request: req });
    
    /*
    if (! ClearBlade.isEdge()) {  // don't run on platform 
        log ("ProcessEnv: trying to run on the platform. Exiting") ;
        resp.error ("ProcessEnv: trying to run on the platform. Exiting") ;
    }
    */
    
    var codeEngine = ClearBlade.Code()
    var serviceToCall = "ProcessEnvironment" ; 
    var loggingEnabled = true
    var params = {
        topc:"Foo"
    }            
    
    function callback (err, data){
        if(err){
            resp.error("Failed to complete my service: " + JSON.stringify(data))
        }
        log(data) ;
    } 
        
    for (i=0; i < topics.length; i++) {
        log (topics[i]) ;
        params = { topic: topics[i] } ;
        codeEngine.execute(serviceToCall, params, loggingEnabled, callback ) ;
    }
    resp.success("done") ;
}