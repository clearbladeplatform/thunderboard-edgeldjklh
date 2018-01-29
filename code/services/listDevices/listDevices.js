function listDevices(req, resp) {
    ClearBlade.init({request: req});
    log(JSON.stringify(req))
	ClearBlade.getAllDevicesForSystem(function(err, data) {
	    //resp.success(data)
	    log(data) ;
		var newData=[];
		for (var i =0;i<data.length;i++) {
		    // returns an array with the device_label and the device name as the ID  string.includes(substring);
		    if ( data[i].device_label !== null && data[i].device_label.includes ("Thunder")) {
		        newData.push({"label":data[i].device_label, "value":data[i]});
		    }
		}
		log(newData);
		resp.success(newData);
	});
}