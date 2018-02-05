#!/bin/bash

# This script provisions Vagrant users.

# Generate random user password

user_passwd=
function gen_passwd {
	user_passwd="$( cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1 )"
}

# Add custom users below
# IMPORTANT! Be sure to change any relvant groups depending on Linux distribution
# For example, Ubuntu uses 'sudo' and 'admin' groups while Centos uses 'wheel' group
declare -A users_hash=( ["bob"]="hackers sudo admin" )

function die () { ret=$1 ; shift ; echo "FATAL ERROR: ""$@" ; exit $ret ; }

# Sanity checks

OS="$(uname)"
if [ "$OS" = "Linux" ] ; then 
	echo "## INFO -- Correct operating system detected."
else
	die "## ERROR -- Make sure the OS is $OS"
fi

for key in ${!users_hash[@]} ; do
	declare -a groups_arr=( $( echo ${users_hash[$key]} ) )
	primary_group=${groups_arr[0]}
	other_groups=$( echo ${groups_arr[@]:1} | sed 's/ /,/g' )

	# Check if user exists first
	id $key > /dev/null 2>&1
	retcode=$?

	if [[ $retcode -ne 0 ]] ; then
		# Add groups id they do not exist already
		for g in ${groups_arr[@]} ; do 
			grep -q -E "^${g}:" /etc/group
			retcode=$?
			[[ $retcode -eq 0 ]] || (echo "## INFO -- Adding new group ${g}" && groupadd ${g})
		done
		
		# Add new user
		echo "## INFO -- Adding new user ${key}"
		useradd -m -s /bin/bash -g ${primary_group} -G ${other_groups} ${key}
		retcode=$?
		[[ $retcode -eq 0 ]] || die "## ERROR -- Could not properly add user ${key}"

		# Create user SSH directory if it does not exist
		[[ -d /home/${key}/.ssh ]] || mkdir -p /home/${key}/.ssh
		(chown -R ${key}:${primary_group} /home/${key}/.ssh || die "## ERROR -- Could not change ownership of .ssh dir for ${key}") && \
		(chmod 700 /home/${key}/.ssh || die "## ERROR -- Could not change permissions of .ssh dir for ${key}")

		# Create a password for user
		echo "## INFO -- Attempting to create default user password for ${key}"
		gen_passwd    # Call password generation function to generate different password for each user in loop
		passwd ${key} <<-EOF
		${user_passwd}
		${user_passwd}
		EOF
		retcode=$?
		if [[ $retcode -eq 0 ]] ; then
			echo "## INFO -- Password for user ${key} is ${user_passwd}"
		else
			die "## ERROR -- Could not set password for ${key}"
		fi
	fi

	# Password-less sudo
	[[ -f /etc/sudoers.d/${key} ]] || echo "${key} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${key}

	# Now, configure SSH access for user
	# In the Vagrantfile, we moved a bunch of files to /tmp/provision_files/
	# This should contain all the user(s) SSH public keys
	# Please read Vagrant documentation on how to transfer files if needed

	echo "## INFO -- Setting SSH public key for ${key}"

	(cp -p /home/vagrant/.ssh/authorized_keys /home/${key}/.ssh/authorized_keys || die "## ERROR -- Could not copy SSH pub key for ${key}") && \
	(chown ${key}:${primary_group} /home/${key}/.ssh/authorized_keys || die "## ERROR -- Could not change ownership of pub key for ${key}") && \
	(chmod 600 /home/${key}/.ssh/authorized_keys || die "## ERROR -- Could not change permissions of pub key for ${key}")

    if [[ -d /tmp/provision_files/files/${key}_ssh_pub_key ]] ; then
        is_empty=$( ls /tmp/provision_files/files/${key}_ssh_pub_key/ )
        if [[ -n $is_empty ]] ; then
            echo "## INFO -- Copying custom user SSH public key for ${key}"
            cat /tmp/provision_files/files/${key}_ssh_pub_key/* >> /home/${key}/.ssh/authorized_keys
        fi
        ret=$?
        if [ $ret -ne 0 ] ; then
            die "## ERROR -- Could not copy user SSH pub key for ${key}"
        fi
    fi

	# Configure various profiles for user
	# Again, we moved a bunch of files to /tmp/provision_files/
	echo "## INFO -- Setting home profiles for ${key}"
	
    (cp     /tmp/provision_files/files/template_bash_aliases /home/${key}/.bash_aliases || die "## ERROR -- Could not copy bash_aliases for ${key}") && \
    (cp     /tmp/provision_files/files/template_bashrc /home/${key}/.bashrc || die "## ERROR -- Could not copy bashrc for ${key}") && \
    (cp     /tmp/provision_files/files/template_inputrc /home/${key}/.inputrc || die "## ERROR -- Could not copy inputrc for ${key}") && \
    (cp     /tmp/provision_files/files/template_profile /home/${key}/.profile || die "## ERROR -- Could not copy profile for ${key}") && \
    (cp     /tmp/provision_files/files/template_screenrc /home/${key}/.screenrc || die "## ERROR -- Could not copy screenrc for ${key}") && \
    (cp     /tmp/provision_files/files/template_vimrc /home/${key}/.vimrc || die "## ERROR -- Could not copy vimrc for ${key}") && \
    (cp -Rp /tmp/provision_files/files/bin /home/${key}/bin || die "## ERROR -- Could not copy ~/bin scripts for ${key}") && \
	(chown -R ${key}:${primary_group} /home/${key}/bin || die "## ERROR -- Could not change ownership of ~/bin scripts for ${key}") && \
	(chmod -R 700 /home/${key}/bin || die "## ERROR -- Could not change permissions of ~/bin scripts for ${key}")

done

# Remove any temporary provisioning files
[[ -d /tmp/provision_files/ ]] && rm -rf /tmp/provision_files/

# vim: ts=4 sw=4
