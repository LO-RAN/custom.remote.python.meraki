# custom.remote.python.meraki

Dynatrace ActiveGate extension scraping Cisco MEraki APIs to generate metrics about network devices.

Prerequisites: deployed ActiveGate that can reach out to Meraki's API endpoints and push dat to Dynatrace API metrics ingestion endpoint.

Note: It creates only metrics. It does not create any entity nor entity related data.

## deployment
* Install on any Linux host, e.g. an ActiveGate.
* Unzip "dtmeraki.zip" in "/opt/dynatrace/batch"
* Edit "config.properties" to set tenant URL and token for your Dynatrace environment, and Meraki organization and key.

## run
you can schedule the script to run every 15 minutes by adding the following line in your crontab configuration with the command 'crontab -e' :
```
*/15 * * * * /usr/bin/python3 /opt/dynatrace/batch/dtmeraki/dtMerakiDaemon.py
```