#!/usr/bin/env python
import pika
from scrapli_netconf.driver import NetconfDriver
import json
from scrapli.exceptions import (
    ScrapliAuthenticationFailed,
    ScrapliConnectionError,
)

sw_filter = """
    <filter>
      <install xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-install-oper">
        <version>
          <package>
            <version/>
          </package>
        </version>
      </install>
    </filter>
"""

def get_sw(msg):
    msg_json = json.loads(msg)
    my_device = {
        "host": msg_json["device_ip"],
        "auth_username": "",
        "auth_password": "",
        "auth_strict_key": False,
    }
    try:
        conn = NetconfDriver(**my_device)
        conn.open()
        if conn.transport.isalive():
            response = conn.get_config(
                source="running",
                filter_=sw_filter,
                filter_type="subtree"
            )
            if response.result:
                print(response.result)
        else:
            print("Transport is down...")
    except ScrapliAuthenticationFailed as err:
        print(f"Failed to connect to network device: {my_device['host']} due to error: {err}")
    except ScrapliConnectionError as err:
        print(f"Failed to connect to network device: {my_device['host']} due to error: {err}")


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='192.168.0.48', credentials=pika.PlainCredentials(
        "guest", "guest"
    )))
channel = connection.channel()

print(' [*] Waiting for messages. To exit press CTRL+C')


def callback(ch, method, properties, body):
    print(f" [x] Received message for device with IP Address: {json.loads(body)['device_ip']}...")
    get_sw(body)
    print(" [x] Done")
    print()
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='netconf', on_message_callback=callback)

channel.start_consuming()
