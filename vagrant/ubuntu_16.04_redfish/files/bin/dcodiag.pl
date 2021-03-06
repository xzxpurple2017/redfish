#!/usr/bin/perl
#
#
# Written 2/20/2016
# Checks hardware diagnostics.
# Run it without arguments.

use strict;
use warnings;
use File::Basename;
use Getopt::Long;
use Data::Dumper;
use Parse::DMIDecode ();
use Parse::DMIDecode::Constants qw(@TYPES);
use Sys::Hostname;
use IPC::System::Simple qw(capture);
use Sys::Load qw/getload uptime/;   # Install using cpanm
use Net::Address::IP::Local;        # Install using cpanm

my $progname = basename($0);

my $big_letters = << 'EOF';
 ____   ____ ___  ____ ___    _    ____
|  _ \ / ___/ _ \|  _ \_ _|  / \  / ___|
| | | | |  | | | | | | | |  / _ \| |  _
| |_| | |__| |_| | |_| | | / ___ \ |_| |
|____/ \____\___/|____/___/_/   \_\____|
EOF

print "$big_letters\n";

my $decoder = new Parse::DMIDecode;
$decoder->parse(qx(sudo /usr/sbin/dmidecode));		# Works best when user has password-less sudo permissions
  
# Defining variables below.

my $asset_tag		= $decoder->keyword("baseboard-asset-tag");
my $serial_number	= $decoder->keyword("baseboard-serial-number");
my $product_name	= $decoder->keyword("baseboard-product-name");
my $mobo_manufacturer	= $decoder->keyword("baseboard-manufacturer");
my $smbios_version	= $decoder->smbios_version;
my $operating_system	= qx(cat /etc/*release | sed -n '1p');
my $kernel_release 	= qx(uname -r);
my $hostname		= hostname;
my $address_ipv4 	= Net::Address::IP::Local->public_ipv4;
my $system_uptime	= int uptime();
my @mem_array		= ();
my $smartctl		= 'sudo /usr/sbin/smartctl';
my $drives 		= 'ls /dev | grep -oP "sd.*[^\d+]" | sort -u';
my @drives_array	= split "\n", capture("$drives");

# Creating message below.

print "System Info\n-----------------------------------------------\n";
print "Operating System:" . "\t" . "$operating_system";
print "Kernel Release:" . "\t\t" . "$kernel_release";
print "Hostname:" . "\t\t" . "$hostname\n";
print "IP Address:" . "\t\t" . "$address_ipv4\n";
if ($serial_number) {
    print "Serial Number:" . "\t\t" . "$serial_number\n";
} else {
    print "Serial Number:" . "\t\t" . "Improperly provisioned -- Please check motherboard settings\n";
}
if ($asset_tag) {
    print "Asset Tag:" . "\t\t" . "$asset_tag\n";
} else {
    print "Asset Tag:" . "\t\t" . "Improperly provisioned -- Please check motherboard settings\n";
}
print "BIOS Version:" . "\t\t" . "$smbios_version\n";
print "FRU Info:" . "\t\t" . "$mobo_manufacturer $product_name\n";

print "\nCurrent Stats\n-----------------------------------------------\n";
print "1 Min CPU Load:" . "\t\t" . (getload())[0]."\n";
print "5 Min CPU Load:" . "\t\t" . (getload())[1]."\n";
print "15 Min CPU Load:" . "\t" . (getload())[2]."\n";
printf "Server Uptime:\t\t%d days, %d hours, %d minutes, and %d seconds\n",(gmtime $system_uptime)[7,2,1,0];

print "\nMemory Diagnostics\n-----------------------------------------------\n";

for my $handle ($decoder->get_handles( group => "memory" )) {
    for my $mem_info ($handle->raw) {
	push @mem_array, $mem_info;
    }
}

my $first_info = shift @mem_array;			# Getting just the first element and "popping" it out.

for my $num_of_dimms ($first_info) {
    my @array = split(/\t/, $num_of_dimms);
    print "\n$array[6]\n";
}

for my $dimm_info (@mem_array ) {
    my @array = split(/\t/, $dimm_info);
    print "$array[8]";
    print "$array[13]";
    print "$array[14]";
    print "$array[5]\n";
}

print "\nHard Drive Info\n-----------------------------------------------\n";

for my $device (@drives_array) {
    print "/dev/$device\n----------\n";
    eval {
	my $device_info = capture("$smartctl -i /dev/$device");
	my @device_info_array = split "\n", $device_info;
	if ($device_info_array[4] =~ /^Device/) {
            print "$device_info_array[4]\n";
	    print "$device_info_array[5]\n";
	    print "$device_info_array[8]\n\n";
	} elsif ($device_info_array[5] =~ /^Device/) {
	    print "$device_info_array[5]\n";
	    print "$device_info_array[6]\n";
	    print "$device_info_array[9]\n\n";
	} else {
	    print "Please check drive info to make sure it is parsed correctly\n";
	}
	1;
    } or do {
	print "Drive info cannot be analyzed.\nPerhaps logically managed elsewhere? Check RAID or LVM.\n\n";
    }
}

print "\nHard Drive Diagnostics\n-----------------------------------------------\n";

for my $device (@drives_array) {
    print "/dev/$device\n----------\n";
    eval {
        my @device_test_array = split "\n", capture("$smartctl -H /dev/$device");
        if ($device_test_array[4]) { 
            print "$device_test_array[4]\n\n";
        } else {
            print "Drive cannot be analyzed.\nPerhaps logically managed elsewhere? Check RAID or LVM.\n\n";
        }
    } or do {
	print "WARNING! Please check drive status. Failed to run analysis checks. Drive may have failed!\n\n";
    }
}    
#print Data::Dumper->Dump([[split /\t/, capture("$drives")]], ["*text"]);

exit 0



