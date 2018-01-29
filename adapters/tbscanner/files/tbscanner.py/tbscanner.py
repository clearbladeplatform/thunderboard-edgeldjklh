from bluepy.btle import *
import struct, time, datetime, json, logging, os, socket, re, sys
from clearblade.ClearBladeCore import System, Query, Developer
from clearblade.ClearBladeCore import cbLogs

scanTimePeriod=10  # 10 seconds to look for new Bluetooth thunderboards
waitTimeBetweenScans=360    # 2 minutes between scans
waitTimeBetweenReads=60  # wait and then process data. Let's say 1 second delay is the lowest
NumMotionPoints=200     # read 100 ax and 100 ox then stop
credentials = {}
credentials['systemKey'] = "88aeb19d0bc2ad9dc199c7a59550"
credentials['systemSecret'] = "88AEB19D0BACD0B982839ADEFE30"
credentials['name'] = "ThunderPi"  # device name from dev table
credentials['active_key'] = "1234567890" # activekey word from dev table
credentials['username'] = "mqtt@clearblade.com"  # device name from dev table
credentials['password'] = "clearblade" # activekey word from dev table
credentials['platformURL'] = "https://staging.clearblade.com"
#credentials['platformURL'] = "http://localhost:9000"


LOGLEVEL="INFO"
R=0
G=255
B=32
L=255
BRIGHTNESS=5
cbLogs.DEBUG = False
cbLogs.MQTT_DEBUG = False
mqtt=""
MotionData = dict()    # for PrintMotion

# this array contains the list of discovered thunderboards.  We need to keep track and
#then have the platform/edge tell the adapter to read or stop
thunderboards = {}

class MQTT:
    def __init__(self, credentials):
        self.systemKey = credentials['systemKey']
        self.systemSecret = credentials['systemSecret']
        self.username = credentials['username']
        self.password = credentials['password']
        self.platformURL = credentials['platformURL']
        self.gatewayAddress = self.GetMacAddress()
        #Connect to MQTT
        cbSystem=System(self.systemKey, self.systemSecret, self.platformURL)
        # Device Auth
        if 'active_key' in credentials:
            self.gatewayName = credentials["name"]
            self.active_key = credentials['active_key']
            cbAuth=cbSystem.Device(self.gatewayName, credentials['active_key'])
        else:
            self.gatewayName = self.gatewayAddress
            cbAuth=cbSystem.User(credentials['username'], credentials['password'])
        # right now override the GatewayName so that portal demos work easier
        self.gatewayName = "thunderboard"
        self.client = cbSystem.Messaging(cbAuth)  
        self.client.connect();  # the on_connect is not working
        self.client.on_message = self.CommandCallback
        #self.client.on_connect = self.on_connect 
    
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
            self.PublishError(message)
                     
    def GetMacAddress(self):
        #Execute the hcitool command and extract the mac address using a regular expression
        #mac = re.search('hci0\s*(([0-9a-fA-F]{2}:){5}([0-9a-fA-F]{2}))', os.popen('hcitool -i hci0 dev').read()).group(1)
        # this is a cross-platform way to do it
        from uuid import getnode as get_mac
        mac = get_mac()
        mac = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
        return mac
                    
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            logging.info("Discovered device %s", dev.addr)
        elif isNewData:
            logging.debug("Received new data from %s", dev.addr)

    def scanProcess(self):
        scanner = Scanner().withDelegate(ScanDelegate())
        try:
            devices = scanner.scan(scanTimePeriod)
        except KeyboardInterrupt:
            if mqtt:
                mqtt.PublishGatewayStatus(False)
                mqtt.Disconnect()
                time.sleep(1)
            os._exit(0)
            raise
        return devices
        
class MotionScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        
    def handleNotification(self, cHandle, data):
        PrintMotion(data, cHandle)
            
# make sure this is not in the ScanDelegate class
def PrintMotion (data, handle):
        import struct
        global MotionData
        acc_handle = 78  # from getHandle()
        orient_handle = 81 # from getHandle() 
        x_y_z = struct.unpack('<HHH', data)
        #print "PrintMotion: handle ["+str(handle)+"]"
        if handle == acc_handle :
            t = tuple([(val/100.0) for val in x_y_z])
            #print "axayaz",t
            ax, ay, az = t
            MotionData['ax'] = ax
            MotionData['ay'] = ay
            MotionData['az'] = az           
        elif handle == orient_handle:
            t = tuple([(val/1000.0) for val in x_y_z])
            #print "oxoyoz",t
            ox, oy, oz = t
            MotionData['ox'] = ox
            MotionData['oy'] = oy
            MotionData['oz'] = oz 

def addDeviceToPlatform(dev):
    for (adtype, desc, value) in dev.getScanData():
        logging.debug("addDeviceToPlatform: adtype: " + str(adtype) + " desc: " + desc + " value: " + value)
        if desc == 'Complete Local Name':
            if 'Thunder Sense #' in value and adtype==9: #only do this, ignore 255s
                try:
                    deviceId = str(int(value.split('#')[-1])) 
                    device = {}
                    # create internal array and status. 
                    device["status"] = "New"
                    device["command"] = "ReadEnv" # default desire by adapter
                    device["deviceAddress"] = dev.addr
                    device["gatewayName"] = mqtt.gatewayName
                    device["deviceType"] = value
                    device["deviceId"] = str(int(value.split('#')[-1])) #    "deviceType": "Thunder Sense #31796",
                    device["gatewayAddress"] = mqtt.gatewayAddress
                    device["connectionType"] = "bluetooth"
                    print ("addDeviceToPlatform: " + json.dumps(device))
                    # copy structure into device list
                    thunderboards[dev.addr] = device      
                    topic = mqtt.gatewayName + "/command/" + deviceId
                    #print "addDeviceToPlatform: Subscribing to topic: " + topic
                    mqtt.SubscribeToTopic(topic)
                    # NEW ADDED THIS to read direct from the platform in case this is running to the edge
                    topic = mqtt.gatewayName + "/command/" + deviceId + "/_edge/" + credentials['name'] ;
                    mqtt.SubscribeToTopic(topic)
                    # send New command to the status queue to trigger platform response
                    topic = mqtt.gatewayName + "/status/" + deviceId
                    mqtt.PublishTopic(topic, json.dumps(device))
                except Exception as e:
                    logging.info("EXCEPTION:: %s", str(e))
                    mqtt.PublishError("addDevicetoPlatform: exception: " + str(e))
    logging.info("addDeviceToPlatform: device[" + dev.addr + "]")
                    
def initDeviceList(devices):
    for dev in devices:
        if gotThunderboard(dev) == False and isThunderboard(dev):
            addDeviceToPlatform(dev)

def processDeviceList(devices):
    for dev in devices:
        #print "processDeviceList: checking for tboard of device[" + dev.addr + "]"
        for tb in thunderboards:   
            if dev.addr == thunderboards[tb]['deviceAddress']:  
                if thunderboards[tb]['status'] == "Authorized" and thunderboards[tb]['command'] == "ReadEnv":
                    #print "processDeviceList: Processing [" + thunderboards[tb]['deviceId'] + "]"
                    processEnv(dev)
                elif thunderboards[tb]['status'] == "New" and thunderboards[tb]['command'] == "ReadEnv":
                    logging.info("processDeviceList: device [" + thunderboards[tb]['deviceId'] + "] not yet Authorized")
                #
                if thunderboards[tb]['status'] == "Authorized" and thunderboards[tb]['command'] == "ReadMotion":
                    #print "processDeviceList: Processing Motion [" + thunderboards[tb]['deviceId'] + "]"
                    processMotion(dev)
                    
def processMotion(dev):
    #print "processDeviceMotion: starting"
    acc_uuid = "c4c1f6e2-4be5-11e5-885dfeff819cdc9f"  #accerometer
    orient_uuid = 'b7c4b694-bee3-45dd-ba9ff3b5e994f49a'
    if gotThunderboard(dev) or isThunderboard(dev):
        try:
            tbDevice=Peripheral()
            tbDevice.setDelegate(MotionScanDelegate())
            #topic = thunderboards[dev.addr]['gatewayName'] + "/motion/" + thunderboards[dev.addr]['deviceId']
            topic = thunderboards[dev.addr]['gatewayName'] + "/motion/" + thunderboards[dev.addr]['deviceId'] + "/_platform" ;
            
            tbDevice.connect(dev.addr, dev.addrType)

            #print "processDeviceMotion: connected to device."
            setup_data = b"\x01\x00"
            notify = tbDevice.getCharacteristics(uuid=acc_uuid)[0]
            notify_handle = notify.getHandle() + 1
            #print "acc handle: ", str (notify_handle)
            tbDevice.writeCharacteristic(notify_handle, setup_data, withResponse=True)

            notify = tbDevice.getCharacteristics(uuid=orient_uuid)[0]
            notify_handle = notify.getHandle() + 1
            #print "orient handle: ", str (notify_handle)
            tbDevice.writeCharacteristic(notify_handle, setup_data, withResponse=True)
            #print("processDeviceMotion: writing done")
            time.sleep(1) # to let the notifications get cracking
            ctr = 0
            while True:
                global MotionData
                if tbDevice.waitForNotifications(1.0):
                    # a notification came in from the tboard
                    ctr = ctr + 1
                    #print "processDeviceMotion: Whiling in wait Notification: ctr[" + str(ctr) + "]"
                    # search the global array 
                    if 'ox' in MotionData:
                        mqtt.PublishTopic(topic, json.dumps(MotionData))
                        #print "processDeviceMotion: Sending: " + json.dumps(MotionData) + " to: " + topic
                        MotionData = dict() # reset for the rest
                    if ctr > NumMotionPoints:
                        break  # end the loop
                    continue
        except KeyboardInterrupt:
            exitapp = True
            os._exit(0)
            raise
        except Exception as e:
            logging.info("EXCEPTION:: %s", str(e))
            mqtt.PublishError("processDeviceMotion: exception: " + str(e))
        finally:
            tbDevice.disconnect()
            #print "ProcessDeviceMotion: disconnected from device"
        
def isThunderboard(dev):
    for (adtype, desc, value) in dev.getScanData():
        #print "isThunderboard: adtype: " + str(adtype) + " desc: " + desc + " value: " + value
        if desc == 'Complete Local Name':
            if 'Thunder Sense #' in value:
                return True
    return False

def gotThunderboard(dev):
    for tb in thunderboards:   
        if dev.addr == thunderboards[tb]['deviceAddress']:  
            return True
    return False
    
def processEnv(dev):
    #print "processDevice: starting"
    if gotThunderboard(dev) or isThunderboard(dev):
        try:
            tbdata=dict()
            tbDevice=Peripheral()
            tbDevice.connect(dev.addr, dev.addrType)
            characteristics = tbDevice.getCharacteristics()
            topic = thunderboards[dev.addr]['gatewayName'] + "/environment/" \
                + thunderboards[dev.addr]['deviceId'] + "/_platform" ;
            #topic = thunderboards[dev.addr]['gatewayName'] + "/environment/" \
            #    + thunderboards[dev.addr]['deviceId'] ;
            for k in characteristics:
                logging.debug('%s',k.uuid)
                if k.uuid == '2a6e':
                    value = k.read()
                    value = struct.unpack('<H', value)
                    value = value[0] / 100
                    tbdata['temperature'] = value
                                        
                elif k.uuid == '2a6f':
                    value = k.read()
                    value = struct.unpack('<H', value)
                    value = value[0] / 100
                    tbdata['humidity'] = value
                                        
                elif k.uuid == '2a76':
                    value = k.read()
                    value = ord(value)
                    tbdata['uv'] = value
                                        
                elif k.uuid == '2a6d':
                    value=k.read()
                    value = struct.unpack('<L', value)
                    value = value[0] / 1000
                    tbdata['pressure'] = value
                                        
                elif k.uuid == 'c8546913-bfd9-45eb-8dde-9f8754f4a32e':
                    value=k.read()
                    value = struct.unpack('<L', value)
                    value = value[0] / 100
                    tbdata['light'] = value
                                        
                elif k.uuid == 'c8546913-bf02-45eb-8dde-9f8754f4a32e':
                    value=k.read()
                    value = struct.unpack('<h', value)
                    value = value[0] / 100
                    tbdata['sound'] = value
                                        
                elif k.uuid == 'efd658ae-c401-ef33-76e7-91b00019103b':
                    value=k.read()
                    value = struct.unpack('<h', value)
                    value = value[0]
                    tbdata['co2'] = value
                                        
                elif k.uuid == 'efd658ae-c402-ef33-76e7-91b00019103b':
                    value=k.read()
                    value = struct.unpack('<h', value)
                    value = value[0]
                    tbdata['voc'] = value
                                        
                elif k.uuid == 'ec61a454-ed01-a5e8-b8f9-de9ec026ec51':
                    value=k.read()
                    value = ord(value)
                    tbdata['battery'] = value

                elif k.uuid == 'fcb89c40-c603-59f3-7dc3-5ece444a401b':
                    s=chr(L)+chr(R*BRIGHTNESS//100)+chr(G*BRIGHTNESS//100)+chr(B*BRIGHTNESS//100)
                    k.write(s, True)                           
            logging.debug(json.dumps(tbdata))
            mqtt.PublishTopic(topic, json.dumps(tbdata))
        except KeyboardInterrupt:
            exitapp = True
            os._exit(0)
            raise
        except Exception as e:
            logging.info("EXEPTION:: %s", str(e))
            mqtt.PublishError("processDevice: exception: " + str(e))
        finally:
            tbDevice.disconnect()

def CleanUp():
    for tb in thunderboards:   
        mqtt.PublishDeviceOffline(thunderboards[tb]['deviceId'])
    mqtt.PublishGatewayStatus(False)
    mqtt.Disconnect()
    os._exit(0)
    
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
    scanner=ScanDelegate();
    exitapp=False
    mqtt = MQTT(credentials)  # activate the ClearBlade network
    time.sleep(5)   # to make sure we connect okay
    mqtt.PublishGatewayStatus(True)
    scanctr = 0
    while not exitapp:
        if scanctr == 0:
            # only scan a bit but don't sleep for a long time
            logging.info('Scan Cycle Complete: %s', datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S'))
            logging.info("Scan Period: %s seconds", scanTimePeriod)
            # temporary hack to see if adtype 255 fires and not the normal 9
            #if len(thunderboards) < 1:
            devices=scanner.scanProcess()
        # put this in every cycle to get the ScanData to work. It's buggy
        initDeviceList(devices)  # this sends a message and waits to hear if it's okay to read from it
        try:
            processDeviceList(devices)
            #logging.info('main: timeBetweenReads Sleeping for %s', waitTimeBetweenReads)
            time.sleep(waitTimeBetweenReads)
            scanctr = scanctr + waitTimeBetweenReads
            if scanctr > waitTimeBetweenScans: 
                scanctr = 0
        except KeyboardInterrupt:
            exitapp = True
            mqtt.PublishGatewayStatus(False)
            mqtt.Disconnect()
            os._exit(0)
            raise
        except Exception as e:
            logging.info ("EXCEPTION:: %s", str(e))
            mqtt.PublishError("main: exception: " + str(e))
