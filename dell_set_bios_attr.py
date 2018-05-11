#!/usr/bin/env python3
#
# pdam@intacct.com
# Written 12/14/2017
#
# This script gathers system attributes for Dell 12th, 13th, and 14th gen
# servers. You should run it in parallel to gather info for many servers.
#
#
import re
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
	global new_user_passwd
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
	parser.add_argument('-c', '--credential', help='Enter new username/password comma-separated', required=True)
	parser.add_argument('-f', '--file', help='Path to JSON config file', required=True)
	parser.add_argument('-r', '--reboot', help='Toggle to reboot', action='store_true')
	parser.add_argument('-d', '--default', help='Reset BIOS to factory defaults', action='store_true')
	args = vars(parser.parse_args())

	iDRAC_https_url = 'https://' + args['ip']
	iDRAC_account = args['username']
	iDRAC_password = args['password']
	new_user_passwd = args['credential']
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
		# Power state options:
		#   "On",
		#   "ForceOff",
		#   "GracefulRestart",
		#   "GracefulShutdown",
		#   "PushPowerButton",
		#   "Nmi"
		payload = {'ResetType': power_state_option}
		headers = {
			'Content-Type': "application/json",
			'X-Auth-Token': self.x_auth_token
		}
		response = requests.request(
			"POST",
			power_url,
			headers=headers,
			data=json.dumps(payload),
			verify=False,
			timeout=30.000
		)
		if re.compile("2[0-9][0-9]").match(str(response.status_code)):
			return ("# INFO -- Successfully performed a '%s'" % (power_state_option))
		else:
			return ("# ERROR -- returned err code '%s' with err message '%s'" % (str(response.status_code), response.text))

	def set_bios_attr(self, bios_data):
		set_bios_url = "%s/Systems/System.Embedded.1/Bios/Settings" % (self.root_url)
		payload = {'Attributes':bios_data}
		headers = {
			'Content-Type': "application/json",
			'X-Auth-Token': self.x_auth_token
		}
		response = requests.request(
			"PATCH",
			set_bios_url,
			headers=headers,
			data=json.dumps(payload),
			verify=False,
			timeout=60.000
		)
		if response.status_code == requests.codes.ok:
			return ("# INFO -- Successfully returned code '%s' with message: '%s'" % (str(response.status_code), response.text))
		else:
			return ("# ERROR -- returned err code '%s' with err message '%s'" % (str(response.status_code), response.text))
		
		
	def reset_bios_dflt(self):
		reset_bios_url = "%s/Systems/System.Embedded.1/Bios/Actions/Bios.ResetBios" % (self.root_url)
		headers = {
			'Content-Type': "application/json",
			'X-Auth-Token': self.x_auth_token
		}
		response = requests.request(
			"POST",
			reset_bios_url,
			headers=headers,
			verify=False,
			timeout=60.000
		)
		if response.status_code == requests.codes.ok:
			return ('Success')

	def set_idrac_credentials(self, new_username, new_password):
		root_idrac_accounts_url = "%s/Managers/iDRAC.Embedded.1/Accounts" % (self.root_url)
		headers = {
			'Content-Type': "application/json",
			'X-Auth-Token': self.x_auth_token
		}
		response = requests.request(
			"GET",
			root_idrac_accounts_url,
			headers=headers,
			verify=False,
			timeout=30.000
		)
		output = response.json()
		for e in output['Members']:
			each_account_path = e['@odata.id']
			each_account_url = "%s%s" % (self.iDRAC_https_url, each_account_path)
			response = requests.request(
				"GET",
				each_account_url,
				headers=headers,
				verify=False,
				timeout=10.000
			)
			output = response.json()
			#UserName = output['UserName']
			Id = str(output['Id'])
			if Id == '2':
				print (each_account_url)
				# Now that we have found the iDRAC account ID, we can proceed to change it 
				# to out standard IT defaults
				payload = {'UserName': new_username, 'Password': new_password}
				response = requests.request(
					"PATCH",
					each_account_url,
					headers=headers,
					data=json.dumps(payload),
					verify=False,
					timeout=30.000
				)
				if response.status_code == requests.codes.ok:
					# TODO: Maybe parse JSON to deliver better output message
					return ("# INFO -- Response code: '%s' Output: %s" % (str(response.status_code), response.text))
				else:
					return ("# ERROR -- Could not set iDRAC password. Returned error code '%s' and err mesg: '%s'") % (response.status_code, response.text)
				break
	
		# Get 1Gbps NIC
		def get_first_one_gbps_nic(self):
			ethernet_dev_url = "%s/Systems/System.Embedded.1/EthernetInterfaces" % (self.root_url)
			headers = {
				'Content-Type': "application/json",
				'X-Auth-Token': self.x_auth_token
			}
			# Determine the 1Gbps interface
			# We want this to boot second after the hard drive
			response = requests.request(
				"GET",
				ethernet_dev_url,
				headers=headers,
				verify=False,
				timeout=10.000
			)
			output = response.json()

			one_gbps_list = []
			for e in output['Members']:
				each_nic_path = e['@odata.id']
				each_nic_url = "%s%s" % (self.iDRAC_https_url, each_nic_path)
				response = requests.request(
					"GET",
					each_nic_url,
					headers=headers,
					verify=False,
					timeout=10.000
				)
				output = response.json()
				if output['SpeedMbps'] == 1000:
					one_gbps_list.append(output['Id'])
			try:
				target_nic = sorted(one_gbps_list)[0]
			except:
				target_nic = 'NIC.Integrated.1-1-1'

			return target_nic

	# Dell currently does not support creating RAID virtual disks via Redfish
	# They plan on releasing this feature Q2 2018
	# Until then, you can use SCP feature to import these settings
	# TODO: Figure out whether using integrated or RAID controller maybe?



	# Boot order stuff
	# TODO: Need to figure out 1Gbps interface by comparing last octet of 'PermanentMACAddress'
	# Note that 'HardDisk.List.1-1' seems to work regardless whether or not RAID is integrated or discrete
	def get_bios_boot_mode(self):
		get_bios_url = "%s/Systems/System.Embedded.1/Bios" % (self.root_url)
		headers = {
			'Content-Type': "application/json",
			'X-Auth-Token': self.x_auth_token
		}
		response = requests.request(
			"GET",
			get_bios_url,
			headers=headers,
			verify=False,
			timeout=10.000
		)
		output = response.json()
		current_boot_mode = output[u'Attributes']["BootMode"]
		self.current_boot_mode = current_boot_mode

	#def get_boot_order(self):

	def set_boot_order(self):
		get_boot_ord_url = "%s/Systems/System.Embedded.1/BootSources" % (self.root_url)
		set_boot_ord_url = "%s/Systems/System.Embedded.1/BootSources/Settings" % (self.root_url)
		headers = {
			'Content-Type': "application/json",
			'X-Auth-Token': self.x_auth_token
		}
		if self.current_boot_mode == "Uefi":
			boot_seq = "UefiBootSeq"
		else:
			boot_seq = "BootSeq"

		# First, get the available boot devices
		# Note, this can vary between R640 and R740xd
		# Then, make sure that hard drive is index 0 and PXE is 1 and all the others are after
		# Tricky coding below
		#
		response = requests.request(
			"GET",
			get_boot_ord_url,
			headers=headers,
			verify=False,
			timeout=10.000
		)
		output = response.json()

		payload = {}
		bootseq_list = []

		for e in output['Attributes'][boot_seq]:
			if e['Name'] == 'HardDisk.List.1-1':
				bootseq_list.insert(0, e)
			elif e['Name'] == 'NIC.Integrated.1-1-1':
				bootseq_list.insert(1, e)
			elif e['Name'] == 'NIC.Integrated.1-3-1':
				bootseq_list.insert(1, e)
			else:
				bootseq_list.append(e)

		for i in bootseq_list:
			index = bootseq_list.index(i)
			i['Index'] = index

		payload['Attributes'] = {boot_seq:bootseq_list}
		json_data = json.dumps(payload)

		# Build a hash first and then convert to JSON
		# Should look something like this for Dell R640
		#
		#
		# "Attributes": {
		#  	"BootSeq": [
		# 		{
		# 			"Enabled": true,
		# 			"Id": "BIOS.Setup.1-1#BootSeq#HardDisk.List.1-1#c9203080df84781e2ca3d512883dee6f",
		# 			"Index": 0,
		# 			"Name": "HardDisk.List.1-1"
		# 		},
		# 		{
		# 			"Enabled": true,
		# 			"Id": "BIOS.Setup.1-1#BootSeq#NIC.Integrated.1-1-1#4dee2631ee9d41c7976443d88057b88c",
		# 			"Index": 1,
		# 			"Name": "NIC.Integrated.1-1-1"
		# 		}
		# 	],
		# 	"HddSeq": [
		# 		{
		# 			"Id": "BIOS.Setup.1-1#HddSeq#RAID.Integrated.1-1#c8f9584f29b46cfce3d888826e4305d0",
		# 			"Index": 0,
		# 			"Name": "RAID.Integrated.1-1"
		# 		}
		# 	]
		# }
		#
		#

		response = requests.request(
			"PATCH",
			set_boot_ord_url,
			#data=json.dumps(payload),
			data=json_data,
			headers=headers,
			verify=False,
			timeout=60.000
		)
		output = response.json()
		if response.status_code == requests.codes.ok:
			return ("# INFO -- Successfully set boot state to defaults")
		elif response.status_code == 500:
			return ("# WARN -- Experienced server err message: %s" % (str(output['error']['@Message.ExtendedInfo'])))
		else:
			return ("# ERROR -- set BIOS boot settings failed returned err code '%s' and err message: %s" % (str(response.status_code), str(output)))

	def create_bios_config_job(self,target):
		idrac_jobs_url = "%s/Managers/iDRAC.Embedded.1/Jobs" % (self.root_url)
		headers = {
			'Content-Type': "application/json",
			'X-Auth-Token': self.x_auth_token
		}
		payload = {"TargetSettingsURI":target}
		response = requests.request(
			"POST",
			idrac_jobs_url,
			data=json.dumps(payload),
			headers=headers,
			verify=False,
			timeout=60.000
		)
		output = response.json()
		# TODO: Obtain Job ID from header and poll for its creation status
		if response.status_code == requests.codes.ok:
			return ("# INFO -- Successfully created job with ID:")
		elif response.status_code == 500:
			return ("# WARN -- Experienced server err message: %s" % (str(output['error']['@Message.ExtendedInfo'])))
		else:
			return ("# ERROR -- job creation job failed with err code '%s' and err message: '%s'" % (str(response.status_code), str(output)))
		

##===main program==

def main():
	parse_args()

	new_username, new_password = new_user_passwd.split(',')

	# Parse JSON config file for BIOS attributes
	#data = json.load(open(data_file))
	#data['ServerAssetTag'] = asset_tag
	#data['ServerName'] = "mgmt-" + asset_tag + ".intacct.com"

	utils_obj = Utils(iDRAC_https_url, iDRAC_account, iDRAC_password)
	utils_obj.auth_session()
	
	# TODO: stuff here
	print (utils_obj.get_power_state())

	# Set BIOS boot mode from default UEFI
	data = {}
	data['BootMode'] = 'Bios'
	print (utils_obj.set_bios_attr(data))
	print (utils_obj.create_bios_config_job('/redfish/v1/Systems/System.Embedded.1/Bios/Settings'))
	if reboot_flag:
		print (utils_obj.set_power_state('ForceOff'))
		time.sleep(15)
		print (utils_obj.set_power_state('On'))

	time.sleep(300)

	utils_obj.get_bios_boot_mode()
	print (utils_obj.set_boot_order())
	print (utils_obj.create_bios_config_job('/redfish/v1/Systems/System.Embedded.1/Bios/Settings'))
	# TODO: Implement dynamic way to set credentials rather than numeric ID
	print (utils_obj.set_idrac_credentials(new_username, new_password))

#	success_flag = (utils_obj.reset_bios_dflt())
#	if success_flag == 'Success':
#		print (utils_obj.set_power_state('ForceOff'))
#		
#		counter = 0
#		interval = 1
#		max_count = 600
#
#		while counter <= max_count:
#			time.sleep(interval)
#			srv_power_state = utils_obj.get_power_state()
#			print (srv_power_state)
#			if srv_power_state == 'Off':
#				break
#			counter = counter + interval
#			remainder = max_count - counter
#			s = str(remainder) + ' seconds remaining in POST'
#			print(s, end='')
#			print('\r', end='')
#
#	print (utils_obj.set_power_state('On'))

	if reboot_flag:
		print (utils_obj.set_power_state('ForceOff'))
		time.sleep(15)
		print (utils_obj.set_power_state('On'))

	# Logout of iDRAC
	print (utils_obj.del_curr_session())

	sys.exit(0)

if __name__ == "__main__":
	main()

