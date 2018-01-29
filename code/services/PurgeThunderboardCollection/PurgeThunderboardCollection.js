const COLLECTIONNAME="ThunderboardHistorian";
var retentionTime=5; //Days to retain

function PurgeThunderboardCollection(req, resp){
    ClearBlade.init({request:req});
    //@param {function} callback Function that handles the response from the server
    var query = ClearBlade.Query({collectionName: COLLECTIONNAME});
    query.lessThan('recorddate', new Date(Date.now() - (retentionTime * 24 * 60 * 60 * 1000)).toISOString());
    query.setPage(0, 0);
    log(new Date(Date.now() - (retentionTime * 24 * 60 * 60 * 1000)).toISOString());
    var callback = function (err, data) {
        if (err) {
        	resp.error("removal error : " + JSON.stringify(data));
        } else {
        	resp.success(data);
        }
    };
    query.remove(callback);
}