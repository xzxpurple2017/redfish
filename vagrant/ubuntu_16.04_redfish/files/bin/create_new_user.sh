#!/bin/bash

prog_name=$( basename $0 )
declare -a new_users=("$@")
group="hackers"

if [[ ${#new_users[@]} = 0 ]] ; then
	echo -e "Use this script to add multiple users to group ${group}\n\nUsage: $prog_name USER1 USER2 ... USERN"
	exit 0
fi

# Sudo is only needed if not already running as root
# This automatically prompts for sudo password if not root
[ `id -u` -eq 0 ]  &&  SUDO=  ||  SUDO=/usr/bin/sudo

for u in ${new_users[@]} ; do
	$SUDO useradd -g ${group} ${u}
done

