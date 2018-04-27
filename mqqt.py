import paho.mqtt.client as mqtt
import psycopg2
import configparser



# Read database credentials
config = configparser.ConfigParser()
config.read("psql.conf")

def ConfigSectionMap(section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

psql_db = ConfigSectionMap("Credentials")['dbname']
psql_user = ConfigSectionMap("Credentials")['user']
psql_pwd = ConfigSectionMap("Credentials")['password']


# Connect to database
try:
    conn = psycopg2.connect(dbname=psql_db, user=psql_user, password=psql_pwd)
except:
    print("I am unable to connect to the database.")

cur = conn.cursor()

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("Fuelfighter")


def parse_mqtt_message(message):
    newMessage = message.replace("'", "")
    messageSplit = newMessage.split(',')
    return messageSplit
    print(messageSplit[1])
    print(messageSplit)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    #data = ((str(msg.payload)).replace("'", ""))[1:]
    #data = (str(msg.payload))[1:]
    #data = "1,1,1,0,1,0,1,0,1,16,21"
    #query =  "INSERT INTO sensors (" + data + ");"
    messageString = (str(msg.payload))[1:]
    m = parse_mqtt_message(messageString)
    times, BMS_State, BMS_PreChargeTimeout, BMS_LTC_LossOfSignal, BMS_OverVoltage, BMS_UnderVoltage, BMS_OverCurrent, BMS_OverTemp, BMS_NoDataOnStartup, BMS_Battery_Current, BMS_Battery_Voltage = m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10]
    cur.execute('INSERT INTO sensors (times, BMS_State, BMS_PreChargeTimeout, BMS_LTC_LossOfSignal, BMS_OverVoltage,BMS_UnderVoltage,BMS_OverCurrent, BMS_OverTemp, BMS_NoDataOnStartup, BMS_Battery_Current, BMS_Battery_Voltage) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (times, BMS_State, BMS_PreChargeTimeout, BMS_LTC_LossOfSignal, BMS_OverVoltage, BMS_UnderVoltage, BMS_OverCurrent, BMS_OverTemp, BMS_NoDataOnStartup, BMS_Battery_Current, BMS_Battery_Voltage))
    conn.commit()
    #file = open("sample.csv","a")
    #file.write(messageString)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("129.241.91.125", 1883, 60)
client.subscribe("Fuelfighter")

client.publish("Fuelfighter", "211,1,1,0,1,0,1,0,1,162222,122222")

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
