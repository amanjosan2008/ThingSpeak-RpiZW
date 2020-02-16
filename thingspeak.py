#!/usr/bin/python3

# Crontab:
# 0 * * * * sudo python3 /home/pi/thingspeak.py
# @reboot sudo python3 /home/pi/thingspeak.py

import socket
import json
from time import strftime,localtime,sleep
import requests
import os
import logging

key = "XMM5GRL6TYC741HBN"

#Create and configure logger
logging.basicConfig(filename="/var/log/rpistats.log", format='%(asctime)s %(message)s', filemode='a')
logger=logging.getLogger()
logger.setLevel(logging.DEBUG)

# Check Internet connectivity
def is_connected():
  try:
    host = socket.gethostbyname("www.google.com")
    s = socket.create_connection((host, 80), 2)
    return True
  except:
    return False

def cpu_utl():
    last_idle = last_total = 0
    with open('/proc/stat') as f:
        fields = [float(column) for column in f.readline().strip().split()[1:]]
    idle, total = fields[3], sum(fields)
    idle_delta, total_delta = idle - last_idle, total - last_total
    last_idle, last_total = idle, total
    utilisation = 100.0 * (1.0 - idle_delta / total_delta)
    return '%5.1f' % utilisation

def count_files():
    x = os.popen('ls /media/aman32/Downloads/ | wc -l').read().strip()
    y = os.popen('ls /media/aman32/Incoming/ | wc -l').read().strip()
    return int(x) + int(y)

def thing():
    #cpu = int(100 - float(os.popen('top -bn1 | head -n 3 | grep "Cpu"').read().split()[7]))
    #temp = int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3
    cpu = cpu_utl()
    temp = int(float(os.popen('/opt/vc/bin/vcgencmd measure_temp').read().split('=')[-1].strip('\'C\n')))
    mem = os.popen('free -m').read().split()[-9]
    swap = os.popen('free -m').read().split()[-2]
    hdd = os.popen('df -m /').read().split()[-2].strip('%')
    load = os.popen('cat /proc/loadavg').read().split()[0]
    uptime = "{0:0.1f}".format(float(os.popen('cat /proc/uptime').read().split()[0])/3600)
    count = count_files()
    ctime = strftime("%Y-%m-%d %H:%M:%S +0530", localtime())

    logger.info(str(("Data Fetched=",ctime, " Temp=",temp, " cpu=",cpu, " mem=",mem, " swap=",swap, " hdd=",hdd, " load=",load, " Count=",count)))

    # Upload Temperature Data to thingspeak.com
    payload = {"write_api_key":key,"updates":[{"created_at":ctime,"field1":temp,"field2":cpu,"field3":mem,"field4":swap,"field5":hdd,"field6":load,"field7":uptime,"field8":count}]}
    url = 'https://api.thingspeak.com/channels/512987/bulk_update.json'
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response


while True:
    if is_connected():
        response = thing()
        if response.status_code == 202:
            logger.info(("Data successfully uploaded= ", str(response.status_code)))
            break
        else:
            logger.error(("HTTP Error Code= ", str(response.status_code)))
            sleep(60)
            continue
    else:
        logger.error('Error: Internet Connection down, Retrying after 60 seconds\n')
        sleep(60)
        continue
