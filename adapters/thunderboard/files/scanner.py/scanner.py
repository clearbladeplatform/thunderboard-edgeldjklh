
from bluepy.btle import *
import struct, time, datetime, json, logging, os, socket, sys
from clearblade.ClearBladeCore import System, Query, Developer
from clearblade.ClearBladeCore import cbLogs

scanTimePeriod=60
#waitTimeBetweenScans=30
SystemKey = "accf829a0bb086848bc29aecaab701"
SystemSecret = "ACCF829A0BCAD2ADE5F984FEC02B"
SystemURL="https://cereslabs.clearblade.com"
cbUser="mqtt@clearblade.com"
cbPass="clearblade"
LOGLEVEL="INFO"
R=0
G=255
B=32
L=255
BRIGHTNESS=5
cbLogs.DEBUG = False
cbLogs.MQTT_DEBUG = False
mqtt=""

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
        devices = scanner.scan(scanTimePeriod)
        return devices      

def processDeviceList(devices):
    for dev in devices:
        processDevice(dev)

def processDevice(dev):
    for (adtype, desc, value) in dev.getScanData():
        if desc == 'Complete Local Name':
            if 'Thunder Sense #' in value:
                try:
                    tbdata=dict()
                    deviceId = int(value.split('#')[-1])
                    logging.info("MAC %s :: %s",  dev.addr, value)
                    tbdata['edgename'] = socket.gethostname()
                    tbdata['devicename']=value
                    tbdata['rssi']=dev.rssi
                    tbdata['deviceid']=dev.addr
                    logging.debug('%s', json.dumps(tbdata))
                    tbDevice=Peripheral()
                    tbDevice.connect(dev.addr, dev.addrType)
                    characteristics = tbDevice.getCharacteristics()
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
                            tbdata['uvIndex'] = value
                                                
                        elif k.uuid == '2a6d':
                            value=k.read()
                            value = struct.unpack('<L', value)
                            value = value[0] / 1000
                            tbdata['pressure'] = value
                                                
                        elif k.uuid == 'c8546913-bfd9-45eb-8dde-9f8754f4a32e':
                            value=k.read()
                            value = struct.unpack('<L', value)
                            value = value[0] / 100
                            tbdata['ambientLight'] = value
                                                
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
                            tbdata['powersource'] = value

                        elif k.uuid == 'fcb89c40-c603-59f3-7dc3-5ece444a401b':
                            s=chr(L)+chr(R*BRIGHTNESS//100)+chr(G*BRIGHTNESS//100)+chr(B*BRIGHTNESS//100)
                            k.write(s, True)                           
                    logging.debug(json.dumps(tbdata))
                    mqtt.publish("device/" + dev.addr, json.dumps(tbdata))
                except KeyboardInterrupt:
                    exitapp = True
                    os._exit(0)
                    raise
                except Exception as e:
                    logging.info("EXEPTION:: %s", str(e))
                finally:
                    tbDevice.disconnect()

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
    cbSystem=System(SystemKey, SystemSecret, SystemURL)
    cbAuth=cbSystem.User(cbUser, cbPass)
    mqtt=cbSystem.Messaging(cbAuth)
        #mqtt.on_connect = on_connect
        #mqtt.on_message = on_message
    mqtt.connect() #Connect to the msg broker
    while not exitapp:
        logging.info("Scan Period: %s seconds", scanTimePeriod)
        devices=scanner.scanProcess()
        try:
            processDeviceList(devices)
            #logging.info('Sleeping for %s', waitTimeBetweenScans)
            #time.sleep(waitTimeBetweenScans)
        except KeyboardInterrupt:
            exitapp = True
            mqtt.disconnect()
            os._exit(0)
            raise
        except Exception as e:
            logging.info ("EXCEPTION:: %s", str(e))
        finally:
            logging.info('Scan Cycle Complete: %s', datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S'))


        
