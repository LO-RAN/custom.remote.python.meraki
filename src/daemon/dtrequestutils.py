import requests
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError

import json
import logging

# --------------------------------------------------------------------------------
def getorganizations(thekey):
    orgs = []

    try:

        # get Meraki organizations
        with requests.get(
            'https://api.meraki.com/api/v1/organizations',
            headers={
                'X-Cisco-Meraki-API-Key': thekey
            },
            verify=False
        ) as ro:

            # error ?
            if(ro.status_code != 200):
                logging.error(ro.status_code, ro.reason, ro.text)
                return []

            logging.debug(ro.text)
            # parse retrieved data as json
            orgs = json.loads(ro.text)
            logging.info("Found "+str(len(orgs))+" organizations.")
    except (ConnectTimeout, HTTPError, Timeout, ConnectionError):
        # handle ConnectionError the exception
        logging.error("Issue in getting Meraki organizations")
    return orgs
# --------------------------------------------------------------------------------


def getorganizationid(theorg, theorgs):
    # look for the organization name, to fetch the corresponding id
    orgid = ""
    for org in theorgs:
        if(org["name"] == theorg):
            # we found the id we were looking for.
            # it is available as org["id"]
            logging.info("Found id "+org["id"] +
                         " for organization "+theorg+".")
            orgid = org["id"]
            # stop iterating the array
            break
    return orgid

# --------------------------------------------------------------------------------
# get  networks for organization


def getnetworks(theorgid, thekey):
    networks = []
    try:
        with requests.get(
            'https://api.meraki.com/api/v1/organizations/'+theorgid+'/networks',
            headers={
                'X-Cisco-Meraki-API-Key': thekey
            },
            verify=False
        ) as rn:

            # error ?
            if(rn.status_code != 200):
                logging.error(rn.status_code, rn.reason, rn.text)
                return[]

            logging.debug(rn.text)

            # parse retrieved data as json
            networks = json.loads(rn.text)

            logging.info("Found "+str(len(networks)) +
                    " networks for organization id "+theorgid+".")
    except (ConnectTimeout, HTTPError, Timeout, ConnectionError):
        # handle ConnectionError the exception
        logging.error("Issue in getting Meraki networks for "+theorgid)

    return networks

# --------------------------------------------------------------------------------


def getdevices(thenetworkid, thekey):
    devices = []
    try:
        # get devices for network
        with requests.get(
            'https://api.meraki.com/api/v1/networks/' +
            thenetworkid+'/devices',
            headers={
                'X-Cisco-Meraki-API-Key': thekey
            },
            verify=False
        ) as rd:

            # error ?
            if(rd.status_code != 200):
                logging.error(rd.status_code, rd.reason, rd.text)
                return []

            logging.debug(rd.text)

            # parse retrieved data as json
            devices = json.loads(rd.text)

            logging.info("Found "+str(len(devices)) +
                    " devices for network id "+thenetworkid+".")
    except (ConnectTimeout, HTTPError, Timeout, ConnectionError):
        # handle ConnectionError the exception
        logging.error("Issue in getting Meraki devices for "+thenetworkid)

    return devices

# --------------------------------------------------------------------------------


def getclients(thedeviceid, thekey, thetimespan):
    clients = []

    try:
        with requests.get(
            'https://api.meraki.com/api/v1/devices/' +
            thedeviceid+'/clients',
            params={
                'timespan': thetimespan
            },
            headers={
                'X-Cisco-Meraki-API-Key': thekey
            },
            verify=False
        ) as rc:

            # error ?
            if(rc.status_code != 200):
                logging.error(thedeviceid, rc.status_code, rc.reason, rc.text)
                return []

            logging.debug(rc.text)

            # parse retrieved data as json
            clients = json.loads(rc.text)

            logging.info("Found "+str(len(clients)) +
                    " clients for device id "+thedeviceid+".")
    except (ConnectTimeout, HTTPError, Timeout, ConnectionError):
        # handle ConnectionError the exception
        logging.error("Issue in getting Meraki clients for "+thedeviceid)

    return clients
# --------------------------------------------------------------------------------


def getuplinks(thenetworkid, thedeviceid, thekey):
    uplinks = []

    try:
        with requests.get(
            'https://api.meraki.com/api/v0/networks/' +
            thenetworkid+'/devices/'+thedeviceid+'/uplink',
            headers={
                'X-Cisco-Meraki-API-Key': thekey
            },
            verify=False
        ) as ru:

            # error ?
            if(ru.status_code != 200):
                logging.error(ru.status_code, ru.reason, ru.text)
                return []

            logging.debug(ru.text)

            # parse retrieved data as json
            uplinks = json.loads(ru.text)

            logging.info("Found "+str(len(uplinks)) +
                    " UpLinks for device id "+thedeviceid+".")
    except (ConnectTimeout, HTTPError, Timeout, ConnectionError):
        # handle ConnectionError the exception
        logging.error("Issue in getting Meraki uplinks for "+thedeviceid)

    return uplinks

# --------------------------------------------------------------------------------

def sendtodynatrace(theresult, theurl, thetoken):
    try:
        with requests.post(
            theurl+'/api/v2/metrics/ingest',
            data=theresult,
            headers={
                'Authorization': "Api-Token " + thetoken,
                'accept': '*/*',
                'Content-Type': 'text/plain; charset=utf-8'
            },
            verify=False
        ) as rdt:

            # error ?
            if(rdt.status_code != 202):
                logging.error(rdt.status_code, rdt.reason, rdt.text)
            else:
                logging.info(
                "Successfully pushed "+str(theresult.count('\n'))+" metrics data to Dynatrace ingestion endpoint.")
                logging.debug(rdt.text)
    except (ConnectTimeout, HTTPError, Timeout, ConnectionError):
        # handle ConnectionError the exception
        logging.error("Issue in sending data to Dynatrace")
# --------------------------------------------------------------------------------
