#!/usr/bin/env python3
#
# This script configures HPE BIOS attributes
# Inspired by scripts published by HPE here:
# https://github.com/HewlettPackard/python-ilorest-library/tree/master/examples/Redfish
#
#
import os
import sys
import json
import argparse
from _redfishobject import RedfishObject
from redfish.rest.v1 import ServerDownOrUnreachableError

def parse_args():
	global iLO_https_url
	global iLO_account
	global iLO_password
	global asset_tag
	global reboot_flag
	global data_file

	parser = argparse.ArgumentParser(
		description='Set BIOS attributes for HPE Gen9 and Gen10 servers',
		formatter_class=argparse.RawTextHelpFormatter
	)
	parser.add_argument('-i', '--ip', help='Enter IP address', required=True)
	parser.add_argument('-a', '--asset', help='Enter asset tag', required=True)
	parser.add_argument('-u', '--username', help='Enter username', required=True)
	parser.add_argument('-p', '--password', help='Enter password', required=True)
	parser.add_argument('-f', '--file', help='Path to JSON config file', required=True)
	parser.add_argument('-r', '--reboot', help='Toggle to reboot', action='store_true')
	args = vars(parser.parse_args())

	iLO_https_url = 'https://' + args['ip'] 
	iLO_account = args['username']
	iLO_password = args['password']
	asset_tag = args['asset']
	data_file = args['file']
	reboot_flag = args['reboot']

def set_asset_tag(redfishobj, asset_tag):
	sys.stdout.write("\n---------\nSet Computer Asset Tag:\n")
	instances = redfishobj.search_for_type("ComputerSystem.")

	for instance in instances:
		body = {"AssetTag": asset_tag}
		response = redfishobj.redfish_patch(instance["@odata.id"], body)
		redfishobj.error_handler(response)

def set_bios_attr(redfishobj, bios_data, bios_password=None):
	sys.stdout.write("\n---------\nSetting BIOS attributes:\n")
	instances = redfishobj.search_for_type("Bios.")
	#print (instances)
	if not len(instances) and redfishobj.typepath.defs.isgen9:
		sys.stderr.write("\nNOTE: This example requires the Redfish schema "\
				 "version TBD in the managed iLO. It will fail against iLOs"\
				 " with the 2.50 firmware or earlier. \n")

	for instance in instances:
		if 'settings' in instance['@odata.id']:
			if redfishobj.typepath.defs.isgen9:
				body = bios_data
			else:
				body = {"Attributes": bios_data}

			response = redfishobj.redfish_patch(instance["@odata.id"], body, optionalpassword=bios_password)
			redfishobj.error_handler(response)

def reboot_server(redfishobj, bios_password=None):
	sys.stdout.write("\n---------\nRebooting server\n")
	instances = redfishobj.search_for_type("ComputerSystem.")

	if redfishobj.typepath.defs.isgen9:
		for instance in instances:
			body = dict()
			body["Action"] = "Reset"
			body["ResetType"] = "ForceRestart"

			response = redfishobj.redfish_post(instance["@odata.id"], body)
			redfishobj.error_handler(response)
	else:
		for instance in instances:
			resp = redfishobj.redfish_get(instance['@odata.id'])
			if resp.status==200:
				body = dict()
				body["Action"] = "ComputerSystem.Reset"
				body["ResetType"] = "ForceRestart"
				path = resp.dict["Actions"]["#ComputerSystem.Reset"]["target"]
			else:
				sys.stderr.write("ERROR: Unable to find the path for reboot.")
				raise

			response = redfishobj.redfish_post(path, body)
			redfishobj.error_handler(response)


if __name__ == "__main__":
	# When running on the server locally use the following commented values
	# iLO_https_url = "blobstore://."
	# iLO_account = "None"
	# iLO_password = "None"

	# When running remotely connect using the iLO secured (https://) address,
	# iLO account name, and password to send https requests
	# iLO_https_url acceptable examples:
	# "https://10.0.0.100"
	# "https://f250asha.americas.hpqcorp.net"

	parse_args()

	# Create a REDFISH object
	try:
		REDFISH_OBJ = RedfishObject(iLO_https_url, iLO_account, iLO_password)
	except ServerDownOrUnreachableError as excp:
		sys.stderr.write("ERROR: server not reachable or doesn't support RedFish.\n")
		sys.exit()
	except Exception as excp:
		raise excp

	# Parse JSON config file for BIOS attributes
	data = json.load(open(data_file))
	data['ServerAssetTag'] = asset_tag

	set_bios_attr(REDFISH_OBJ, data)
	set_asset_tag(REDFISH_OBJ, asset_tag)
	if reboot_flag:
		reboot_server(REDFISH_OBJ)

	REDFISH_OBJ.redfish_client.logout()
