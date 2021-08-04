from ruxit.api.base_plugin import RemoteBasePlugin
import json
import logging
import requests

logger = logging.getLogger(__name__)


class Generator(RemoteBasePlugin):

    def initialize(self, **kwargs):

        config = kwargs['config']
        debuglogging = config["debug"]

        # get input parameters

        if debuglogging == "DEBUG":
            self.logging_level = logging.DEBUG
        elif debuglogging == "INFO":
            self.logging_level = logging.INFO
        else:
            self.logging_level = logging.WARNING
        logger.setLevel(self.logging_level)

        self.dt_server_url = config["dt_server_url"]
        self.api_token = config["api_token"]
        self.meraki_token = config["meraki_token"]
        self.meraki_org = config["meraki_org"]
        self.meraki_network = config["meraki_network"]

    def query(self, **kwargs):

        requests.packages.urllib3.disable_warnings()

        logger.setLevel(self.logging_level)


        # get Meraki organizations
        ro = requests.get(
            'https://api.meraki.com/api/v1/organizations',
            headers={
                'X-Cisco-Meraki-API-Key': self.meraki_token
            },
            verify=False
        )

        # error ?
        if(ro.status_code != 200):
            logger.error(ro.status_code, ro.reason, ro.text)
            return

        logger.debug(ro.text)

        # parse retrieved data as json
        orgs = json.loads(ro.text)

        logger.info("Found "+str(len(orgs))+" organizations.")

        orgid = ""
        # look for the organization name, to fetch the corresponding id
        for org in orgs:
            if(org["name"] == self.meraki_org):
                # we found the id we were looking for.
                # it is available as org["id"]
                orgid = org["id"]
                logger.info("Found id "+orgid +" for organization "+self.meraki_org+".")
                # stop iterating the array
                break
        
        # if we could not find the organization, we should stop here and report error
        if orgid == "":
            logger.error("Meraki organization not found")
            return

        # get Maraki networks for organization
        rn = requests.get(
            'https://api.meraki.com/api/v1/organizations/'+orgid+'/networks',
            headers={
                'X-Cisco-Meraki-API-Key': self.meraki_token
            },
            verify=False
        )

        # error ?
        if(rn.status_code != 200):
            logger.error(rn.status_code, rn.reason, rn.text)
            return

        logger.debug(rn.text)

        # parse retrieved data as json
        networks = json.loads(rn.text)

        logger.info("Found "+str(len(networks))+" networks for organization "+self.meraki_org+".")

        networkid = ""
        # look for the network name, to fetch the corresponding id
        for network in networks:
            if(network["name"] == self.meraki_network):
                # we found the id we were looking for.
                # it is available as network["id"]
                # stop iterating the array
                networkid = network["id"]
                logger.info("Found id "+networkid+" for network "+self.meraki_network+".")
                break

        # if we could not find the network, we should stop here and report error
        if networkid == "":
            logger.error("Meraki network not found")
            return

        # get devices for network
        rd = requests.get(
            'https://api.meraki.com/api/v1/networks/'+networkid+'/devices',
            headers={
                'X-Cisco-Meraki-API-Key': self.meraki_token
            },
            verify=False
        )

        # error ?
        if(rd.status_code != 200):
            logger.error(rd.status_code, rd.reason, rd.text)
            return

        logger.debug(rd.text)

        # parse retrieved data as json
        devices = json.loads(rd.text)

        logger.info("Found "+str(len(devices))+" devices for network "+network["name"]+".")


        # the resulting data we will push to Dynatrace API as metrics ingestion
        result = ""

        # get clients for device
        for device in devices:
            rc = requests.get(
                'https://api.meraki.com/api/v1/devices/'+device["serial"]+'/clients',
                params={
                    'timespan': '60'
                },
                headers={
                    'X-Cisco-Meraki-API-Key': self.meraki_token
                },
                verify=False
            )

            # error ?
            if(rc.status_code != 200):
                logger.error(rc.status_code, rc.reason, rc.text)
                return

            logger.debug(rc.text)

            # parse retrieved data as json
            clients = json.loads(rc.text)

            logger.info("Found "+str(len(clients))+" clients for device "+device["name"]+".")

            # build the metrics line for Dynatrace ingestion
            ingestline ="meraki.device.clients"\
                    + ",device="+device["name"].replace(" ","")\
                    + ",model="+device["model"].replace(" ","")\
                    + ",network="+self.meraki_network.replace(" ","")\
                    + ",org="+self.meraki_org.replace(" ","")\
                    + " "\
                    + str(len(clients))\
                    + "\n"

            logger.info(ingestline)

            # add the metrics line to the existing result
            result += ingestline


            # get UpLinks for device
            ru = requests.get(
                'https://api.meraki.com/api/v0/networks/'+networkid+'/devices/'+device["serial"]+'/uplink',
                headers={
                    'X-Cisco-Meraki-API-Key': self.meraki_token
                },
                verify=False
            )

            # error ?
            if(ru.status_code != 200):
                logger.error(ru.status_code, ru.reason, ru.text)
                return

            logger.debug(ru.text)

            # parse retrieved data as json
            uplinks = json.loads(ru.text)

            logger.info("Found "+str(len(uplinks))+" UpLinks for device "+device["name"]+".")

            linkstatus ={'Active' : 2,'Not connected' : 1,'Inactive' : 0}

            for uplink in uplinks:
                
                # build the metrics line for Dynatrace ingestion
                ingestline ="meraki.device.interface.status"\
                    + ",interface="+uplink["interface"].replace(" ","")\
                    + ",device="+device["name"].replace(" ","")\
                    + ",model="+device["model"].replace(" ","")\
                    + ",network="+self.meraki_network.replace(" ","")\
                    + ",org="+self.meraki_org.replace(" ","")\
                    + " "\
                    + str(linkstatus.get(uplink["status"], -1))\
                    + "\n"

                logger.info(ingestline)

                # add the metrics line to the existing result
                result += ingestline



        # send overall result (all the metric lines) to Dynatrace
        rdt = requests.post(
            self.dt_server_url+'/api/v2/metrics/ingest',
            data=result,
            headers={
                'Authorization': "Api-Token " + self.api_token,
                'Content-Type': 'text/plain; charset=utf-8'
            },
            verify=False
        )

        # error ?
        if(rdt.status_code != 202):
            logger.error(rdt.status_code, rdt.reason, rdt.text)
        else:
            logger.info("Successfully pushed metrics data to Dynatrace ingestion endpoint.")
            logger.debug(rdt.text)
