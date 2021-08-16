import requests
import json
import logging
import configparser
import os
import sys

import dtrequestutils as rq
import datetime


logging.basicConfig(filename=os.path.join(sys.path[0], "dtMerakiDaemon.log"),filemode='w',format='%(asctime)s %(message)s', level=logging.INFO)

requests.packages.urllib3.disable_warnings()


logging.info("Starting at "+datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S"))

# open properties file
config = configparser.ConfigParser()

config.read(os.path.join(sys.path[0], "config.properties"))

# get properties
dttoken = config.get('dynatrace', 'dt_api_token')
dttenanturl = config.get('dynatrace', 'dt_tenant_url')

merakiorg = config.get('meraki', 'meraki_org')
merakikey = config.get('meraki', 'meraki_key')
merakitimespan = config.get('meraki', 'meraki_time_span')


# describe the possible states of an interface (uplink)
linkstatus = {'Active': 2, 'Not connected': 1, 'Not active': 0}

# retrieve organization id from name
orgid = rq.getorganizationid(merakiorg, rq.getorganizations(merakikey))

# if we could not find the organization, we should stop here and report error
if orgid == "":
    logging.error("Meraki organization not found")
    exit(-1)


# get  networks for organization
networks = rq.getnetworks(orgid, merakikey)

for network in networks:
    # get devices for network
    devices = rq.getdevices(network["id"], merakikey)

    for device in devices:
        # the resulting data we will push to Dynatrace API as metrics ingestion
        result = ""

        # get clients for device
        clients = rq.getclients(device["serial"], merakikey,merakitimespan)

        # warning: name can be missing !!
        if("name" in device):
            devicename=device["name"]
        else:
            devicename=device["serial"]

        # build the metrics line for Dynatrace ingestion
        ingestline = "meraki.device.clients"\
            + ",device="+devicename.replace(" ", "_")\
            + ",model="+device["model"].replace(" ", "_")\
            + ",network="+network["name"].replace(" ", "_")\
            + ",org="+merakiorg.replace(" ", "_")\
            + " "\
            + str(len(clients))\
            + "\n"

        logging.debug(ingestline)

        # add the metrics line to the overall result
        result += ingestline

        # get UpLinks for device
        uplinks = rq.getuplinks(network["id"], device["serial"], merakikey)

        # for each found interface
        for uplink in uplinks:

            # build the metrics line for Dynatrace ingestion
            ingestline = "meraki.device.interface.status"\
                + ",interface="+uplink["interface"].replace(" ", "_")\
                + ",device="+device["name"].replace(" ", "_")\
                + ",model="+device["model"].replace(" ", "_")\
                + ",network="+network["name"].replace(" ", "_")\
                + ",org="+merakiorg.replace(" ", "_")\
                + " "\
                + str(linkstatus.get(uplink["status"], -1))\
                + "\n"

            logging.debug(ingestline)

            # add the metrics line to the overall result
            result += ingestline


        # finally send overall result (all the metric lines) to Dynatrace
        rq.sendtodynatrace(result, dttenanturl, dttoken)

logging.info("Ending at "+datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S"))
