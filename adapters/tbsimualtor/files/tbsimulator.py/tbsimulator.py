import struct, time, datetime, json, logging, os, socket, re, sys
from clearblade.ClearBladeCore import System, Query, Developer
from clearblade.ClearBladeCore import cbLogs

# tune these parameters if going direct to platform or an edge ..
waitTimeBetweenReads=60  # wait and then process data 30 = platform, 5 for edge
NumMotionPoints=300     # read 100 ax and 100 ox then stop. 150 for platform, 1000 for edge
credentials = {}

#credentials['username'] = "mqtt@clearblade.com"  # device name from dev table
#credentials['password'] = "clearblade" # activekey word from dev table
#credentials['platformURL'] = "http://127.0.0.1:9000"
#
credentials['platformURL'] = "https://staging.clearblade.com"
credentials['systemKey'] = "88aeb19d0bc2ad9dc199c7a59550"
credentials['systemSecret'] = "88AEB19D0BACD0B982839ADEFE30"
credentials['name'] = "ThunderPi"  # device name from dev table
credentials['active_key'] = "1234567890" # activekey word from dev table

LOGLEVEL="INFO"
cbLogs.DEBUG = False
cbLogs.MQTT_DEBUG = False
mqtt=""

# this array contains the list of discovered thunderboards.  We need to keep track and
#then have the platform/edge tell the adapter to read or stop
thunderboards = {}

class MQTT:
    def __init__(self, credentials):
        self.gatewayAddress = self.GetMacAddress()
        #Connect to MQTT
        cbSystem=System(credentials['systemKey'], credentials['systemSecret'], credentials['platformURL'])
        # Device Auth
        if 'active_key' in credentials:
            self.gatewayName = credentials["name"]
            cbAuth=cbSystem.Device(self.gatewayName, credentials['active_key'])
        else:
            self.gatewayName = self.gatewayAddress
            cbAuth=cbSystem.User(credentials['username'], credentials['password'])
        # right now override the GatewayName so that portal demos work easier
        self.gatewayName = "thunderboard"
        self.client = cbSystem.Messaging(cbAuth)   
        self.client.connect() #Connect to the msg broker
        self.client.on_message = self.CommandCallback
        self.client.on_connect = self.on_connect
        
    def on_connect(self, client, userdata, flags, rc):
        time.sleep(1)
        
    def Disconnect(self):
        self.client.disconnect()
        
    def PublishGatewayStatus (self, Online):
        topic = self.gatewayName + "/status"
        #print "Publishing topic: " + topic
        messageToPublish = {}
        messageToPublish["gatewayName"] = self.gatewayName 
        messageToPublish["gatewayAddress"] = self.gatewayAddress
        if Online is True:
            messageToPublish["status"] = "Online"
        else:
            messageToPublish["status"] = "Offline"
        self.client.publish(topic, json.dumps(messageToPublish))
        
    def PublishDeviceOffline (self, deviceId):
        topic = self.gatewayName + "/status/" + deviceId
        #print "Publishing topic: " + topic
        messageToPublish = {}
        messageToPublish["gatewayName"] = self.gatewayName 
        messageToPublish["gatewayAddress"] = self.gatewayAddress
        messageToPublish["deviceId"] = deviceId
        messageToPublish["status"] = "Offline"
        self.client.publish(topic, json.dumps(messageToPublish))
        
    def PublishTopic(self, topic, message):
        self.client.publish(topic,message)

    def SubscribeToTopic(self, topic):
        self.client.subscribe(topic)
    
    def PublishError(self, message):
	    topic = self.gatewayName + "/status"
	    messageToPublish = {}
	    messageToPublish["gatewayName"] = self.gatewayName
	    messageToPublish["gatewayAddress"] = self.gatewayAddress
	    messageToPublish["error"] = message
	    self.client.publish(topic, json.dumps(messageToPublish))
    
    def CommandCallback(self, client, obj, message ):
        parsedMessage = json.loads(message.payload)
        deviceAddress = parsedMessage["deviceAddress"]
        if "_edge" in message.topic:  # gw/command/dev/_edge/edge_id
            gw, q, deviceId, e, f = message.topic.split("/") 
        else:
            gw, q, deviceId = message.topic.split("/")  
        #logging.info("CommandCallback: " + message.payload + " on topic " + gw + "/" + q + "/" + deviceId)
        logging.info("CommandCallback: " + message.payload + " on topic " + message.topic)
        if parsedMessage['command'] == "ReadEnv" and parsedMessage['status'] == "Authorized":
            thunderboards[deviceAddress]["status"] = "Authorized"
            thunderboards[deviceAddress]["command"] = "ReadEnv"  
        elif parsedMessage['command'] == "StopEnv" and parsedMessage['status'] == "Authorized": 
            thunderboards[deviceAddress]["status"] = "Authorized"
            thunderboards[deviceAddress]["command"] = "StopEnv"
        elif parsedMessage['command'] == "disconnect":
            thunderboards[deviceAddress]["status"] = "UnAuthorized"
            thunderboards[deviceAddress]["command"] = "disconnect"
            # disconnect really means do nothing
        elif parsedMessage['command'] == "ReadMotion" and parsedMessage['status'] == "Authorized":
            thunderboards[deviceAddress]["status"] = "Authorized"
            thunderboards[deviceAddress]["command"] = "ReadMotion"  
        elif parsedMessage['command'] == "StopMotion" and parsedMessage['status'] == "Authorized": 
            thunderboards[deviceAddress]["status"] = "Authorized"
            thunderboards[deviceAddress]["command"] = "StopMotion"
        else:
            message = "CommandCallback: Unknown command [" + parsedMessage['command'] + "] on topic " + message.topic
            self.client.PublishError(message)
                     
    def GetMacAddress(self):
        #Execute the hcitool command and extract the mac address using a regular expression
        #mac = re.search('hci0\s*(([0-9a-fA-F]{2}:){5}([0-9a-fA-F]{2}))', os.popen('hcitool -i hci0 dev').read()).group(1)
        # this is a cross-platform way to do it
        from uuid import getnode as get_mac
        mac = get_mac()
        mac = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
        return mac

# used to mimimc a BluetoothLE Device
class Device:
    def __init__(self, addr, deviceId):
        self.addr = addr # this is mainly for internal lookups
        self.deviceId = deviceId # this is the main key to the device

def addDevice(dev):
    logging.debug("addDevice: Device: " + dev.addr)
    try:
        deviceId = dev.deviceId
        device = {}
        device["status"] = "New"
        device["command"] = "ReadEnv" # default desire by adapter
        device["deviceAddress"] = dev.addr
        device["gatewayName"] = mqtt.gatewayName
        device["deviceType"] = "Thunderboard Sense #" + deviceId
        device["deviceId"] = deviceId
        device["gatewayAddress"] = mqtt.gatewayAddress
        device["connectionType"] = "bluetooth"
        #print ("addDevice: " + json.dumps(device))
        # copy structure into device list
        thunderboards[dev.addr] = device      
        topic = mqtt.gatewayName + "/command/" + deviceId
        #print "addDevice: Subscribing to topic: " + topic
        mqtt.SubscribeToTopic(topic)
        # NEW ADDED THIS to read direct from the platform
        topic = mqtt.gatewayName + "/command/" + deviceId + "/_edge/ThunderMac" ;
        mqtt.SubscribeToTopic(topic)
        # send New command to the status queue to trigger platform response in Platform Callback
        topic = mqtt.gatewayName + "/status/" + deviceId
        mqtt.PublishTopic(topic, json.dumps(device))
    except Exception as e:
        logging.info("EXCEPTION:: %s", str(e))
        mqtt.PublishError("addDevice: exception: " + str(e))
    logging.info("addDevice: device[" + dev.addr + "]")

def processDeviceList(devices):
    for dev in devices:
        logging.debug ("processDeviceList: checking for tboard of device[" + dev.addr + "]")
        for tb in thunderboards:   
            if dev.addr == thunderboards[tb]['deviceAddress']:  
                if thunderboards[tb]['status'] == "Authorized" and thunderboards[tb]['command'] == "ReadEnv":
                    #print "processDeviceList: Processing [" + thunderboards[tb]['deviceId'] + "]"
                    processEnv(dev)
                elif thunderboards[tb]['status'] == "New" and thunderboards[tb]['command'] == "ReadEnv":
                    logging.info("processDeviceList: device [" + thunderboards[tb]['deviceId'] + "] not yet Authorized")
                # now see the board wants to Motion ...
                if thunderboards[tb]['status'] == "Authorized" and thunderboards[tb]['command'] == "ReadMotion":
                    #print "processDeviceList: Processing Motion [" + thunderboards[tb]['deviceId'] + "]"
                    processMotion(dev)

def frandomizer(min, max):
    import random
    obj = (random.random() * (max - min)) + min
    return round(obj,3)                    
                    
def GenerateMotion ():
    # generate random set of motion data
    motion = dict()
    #Orientation alpha angle in deg (+180 to -180) with resolution of 0.01 deg
    motion['ox'] = frandomizer(-180.0, 180.0) #17.702
    #Orientation beta angle in deg (+90 to -90) with resolution of 0.01 deg
    motion['oy'] = frandomizer(-90.0, 90.0) #65.257
    #Orientation gamma angle in deg (+180 to -180) with resolution of 0.01 deg
    motion['oz'] = frandomizer(-180.0, 180.0) #64.43
    # Acceleration along X/Y/Z axis in units in g with resolution of 0.001 g
    motion['ax'] = frandomizer(650.0, 680.0) #654.87
    motion['ay'] = frandomizer(650.0, 680.0) #654.87
    motion['az'] = frandomizer(650.0, 680.0) #645.3
    return motion
                                
def processMotion(dev):
    #print "processDeviceMotion: starting"
    acc_uuid = "c4c1f6e2-4be5-11e5-885dfeff819cdc9f"  #accerometer
    orient_uuid = 'b7c4b694-bee3-45dd-ba9ff3b5e994f49a'
    try:
        topic = thunderboards[dev.addr]['gatewayName'] + "/motion/" + thunderboards[dev.addr]['deviceId'] + "/_platform" ;
        ctr = 0
        while True:
            ctr = ctr + 1
            MotionData = GenerateMotion()
            mqtt.PublishTopic(topic, json.dumps(MotionData))
            #print "processDeviceMotion: Sending: " + json.dumps(MotionData) + " to: " + topic
            if ctr > NumMotionPoints:
                break  # end the loop
            logging.info ("processDeviceMotion: Sending MotionData to: " + topic)
    except KeyboardInterrupt:
        CleanUp()
        raise
    except Exception as e:
        logging.info("EXCEPTION:: %s", str(e))
        mqtt.PublishError("processDeviceMotion: exception: " + str(e))

def randomizer(min, max):
    import random
    obj = (random.random() * (max - min)) + min
    return int(obj)
    
def GenerateEnvironment ():
    # generate random set of motion data
    # need to build random generator next!
    env = dict()
    env['sound'] = randomizer(50, 95) #79
    env['co2'] = randomizer(300, 500) #400
    env['temperature'] = randomizer(1, 32) #28
    env['voc'] = 0
    env['humidity'] = randomizer(30, 80) #53
    env['light'] = randomizer(5, 80) #19
    env['pressure'] = randomizer(900, 1200) #1011
    env['battery'] = randomizer(1, 100) #1
    env['uv'] = randomizer(1,10)
    return env
    
def CleanUp():
    for tb in thunderboards:   
        mqtt.PublishDeviceOffline(thunderboards[tb]['deviceId'])
    mqtt.PublishGatewayStatus(False)
    mqtt.Disconnect()
    os._exit(0)
    
def processEnv(dev):
    try:
        #topic = thunderboards[dev.addr]['gatewayName'] + "/environment/" \
        #    + thunderboards[dev.addr]['deviceId']
        topic = thunderboards[dev.addr]['gatewayName'] + "/environment/" \
            + thunderboards[dev.addr]['deviceId'] + "/_platform" ;
        tbdata = GenerateEnvironment()    
        logging.debug(json.dumps(tbdata))
        mqtt.PublishTopic(topic, json.dumps(tbdata))
        logging.debug ("processDevice: Sending: " + json.dumps(tbdata) + " to: " + topic)
    except KeyboardInterrupt:
        CleanUp()
        raise
    except Exception as e:
        logging.info("EXCEPTION:: %s", str(e))
        mqtt.PublishError("processDevice: exception: " + str(e))

#TODO: Configure Logging to show timestamps on all messages
def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',datefmt='%m-%d-%Y %H:%M:%S %p')
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logging.basicConfig(level=os.environ.get("LOGLEVEL", LOGLEVEL))
    logger.addHandler(handler)
    return logger

#Main Loop
if __name__ == '__main__':
    logger = setup_custom_logger('scanner adapter')
    mqtt = MQTT(credentials)  # activate the ClearBlade network
    # main_loop will be called by the on_connect callback to avoid timers  
    # hack to let the connect happen
    time.sleep(5)
    mqtt.PublishGatewayStatus(True)
    d = {}
    #d["tboard30000"] = Device("tboard30000", "30000")
    #d["tboard30001"] = Device("tboard30001", "30001")
    d["tboard20000"] = Device("tboard20000", "20000")
    d["tboard20001"] = Device("tboard20001", "20001")
    devices = d.values()
    for dev in devices:
        addDevice(dev)
    while True:
        try:
            processDeviceList(devices)
            logging.info('main: timeBetweenReads Sleeping for %s', waitTimeBetweenReads)
            time.sleep(waitTimeBetweenReads)
        except KeyboardInterrupt:
            CleanUp()
            raise
        except Exception as e:
            logging.info ("EXCEPTION:: %s", str(e))
            PublishError("main: exception: " + str(e))
                     



