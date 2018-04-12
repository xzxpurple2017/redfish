#!/usr/bin/env python3
#
# pdam@intacct.com
# Written 12/14/2017
#
# This script gathers system attributes for Dell 12th, 13th, and 14th gen
# servers. You should run it in parallel to gather info for many servers.
#
#
import os
import sys
import json
import time
import sqlite3
import requests
import argparse
import traceback
import warnings

warnings.filterwarnings("ignore")

def parse_args():
    global iDRAC_https_url
    global iDRAC_account
    global iDRAC_password
    global asset_tag
    global reboot_flag
    global data_file
    global default

    parser = argparse.ArgumentParser(
        description='Set BIOS attributes for Dell 12th, 13th, and 14th gen servers',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-i', '--ip', help='Enter IP address', required=True)
    parser.add_argument('-a', '--asset', help='Enter asset tag', required=True)
    parser.add_argument('-u', '--username', help='Enter username', required=True)
    parser.add_argument('-p', '--password', help='Enter password', required=True)
    parser.add_argument('-f', '--file', help='Path to JSON config file', required=True)
    parser.add_argument('-r', '--reboot', help='Toggle to reboot', action='store_true')
    parser.add_argument('-d', '--default', help='Reset BIOS to factory defaults', action='store_true')
    args = vars(parser.parse_args())

    iDRAC_https_url = 'https://' + args['ip']
    iDRAC_account = args['username']
    iDRAC_password = args['password']
    asset_tag = args['asset']
    data_file = args['file']
    reboot_flag = args['reboot']
    default = args['default']

class Utils:
	def __init__(self, iDRAC_https_url, iDRAC_account, iDRAC_password):
		self.iDRAC_https_url = iDRAC_https_url
		self.username = iDRAC_account
		self.password = iDRAC_password
		self.root_url = "%s/redfish/v1" % (iDRAC_https_url)

	def auth_session(self):
		sessions_url = "%s/Sessions" % (self.root_url)
		headers = { 'Content-Type': "application/json" }
		payload = "{\"UserName\": \"%s\", \"Password\": \"%s\"}" % (self.username, self.password)
		response = requests.request(
			"POST",
			sessions_url,
			headers=headers,
			data=payload,
			verify=False,
			timeout=60.000
		)
		# Check to make sure we get a successful HTTP 201 Created response
		#if re.search(r'^2[0-9][0-9]$', str(response.status_code)):
		if response.status_code == requests.codes.created:
			self.x_auth_token = response.headers['X-Auth-Token']
			session_id = response.headers['Location']
			self.curr_session_location = "%s%s" % (self.iDRAC_https_url, session_id)
		else:
			print ("# ERROR -- Authorization attempt for %s returned err code %s" % (self.iDRAC_https_url, str(response.status_code)))
			sys.exit(1)

	def del_curr_session(self):
		headers = {
			'Content-Type': "application/json",
			'X-Auth-Token': self.x_auth_token
		}
		response = requests.request(
			"DELETE",
			self.curr_session_location,
			headers=headers,
			verify=False,
			timeout=30.000
		)
		if response.status_code == requests.codes.ok:
			return ("# INFO -- Successfully deleted current session")
			sys.exit(0)
		else:
			print ("# ERROR -- Session deletion attempt failed returned err code %s" % (str(response.status_code)))
			sys.exit(1)
	
	def get_power_state(self):
		systems_url = "%s/Systems/System.Embedded.1" % (self.root_url)
		headers = {
			'Content-Type': "application/json",
			'X-Auth-Token': self.x_auth_token
		}
		response = requests.request(
			"GET",
			systems_url,
			headers=headers,
			verify=False,
			timeout=10.000
		)
		if response.status_code == requests.codes.ok:
			return (response.json()['PowerState'])

	def set_power_state(self, power_state_option):
		power_url = "%s/Systems/System.Embedded.1/Actions/ComputerSystem.Reset" % (self.root_url)
		payload = {'ResetType': power_state_option}
		headers = {
			'Content-Type': "application/json",
			'X-Auth-Token': self.x_auth_token
		}
		response = requests.request(
			"POST",
			power_url,
			headers=headers,
			data=payload,
			verify=False,
			timeout=30.000
		)
		if response.status_code == requests.codes.ok:
			return (response.text)

	def set_bios_attr(self,)
		


##===main program==

def main():
	parse_args()

	utils_obj = Utils(iDRAC_https_url, iDRAC_account, iDRAC_password)
	utils_obj.auth_session()
	# TODO: stuff here
	print (utils_obj.get_power_state())
	# Logout of iDRAC
	print (utils_obj.del_curr_session())

	sys.exit(0)

if __name__ == "__main__":
	main()

