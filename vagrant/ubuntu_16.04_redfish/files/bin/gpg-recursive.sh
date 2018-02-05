#!/bin/bash
#
# 2/16/2016
# 
# CentOS version
#
# Make sure your GPG keys are loaded correctly.
#
# Run ps ax | grep gpg to make sure. IF you are not sure, kill it and run:
# gpg-agent -s --daemon --write-env-file --use-standard-socket
#
# Also, do a test by encrypting and decrypting a file and then rerunning that test.
# There should be no password prompt the second time around.

PROGNAME=$(basename "$0")
USERNAME='<USERNAME_HERE!!!>'
VERSION='CentOS'

USAGE="
This script is used to encrypt and decrypt files recursively.
To use, please specify flag and directory for argument.

Usage: $PROGNAME\t[-e]\t<DIRECTORY>
\t\t\t[-d]\t<DIRECTORY>

\t\t\t[-h]\tDisplay help statement
\t\t\t[-v]\tGet version info

"

recursive-encrypt () {
    for i in *; do
        if [ -d "$i" ]; then
            (cd "$i" && recursive-encrypt)
        else
            echo "$i"
	    if [ "$(echo "$i" | grep -v $PROGNAME | grep -vq ".gpg" && echo true)" = "true" ]; then
		gpg -e -r "$USERNAME" "$i"                                                
                shred -fzu "$i"
	    fi
        fi
    done
}

recursive-decrypt () {
    for i in *; do
        if [ -d "$i" ]; then
            (cd "$i" && recursive-decrypt)
        else
            echo "$i"
            if [ "$(echo "$i" | grep -v $PROGNAME | grep -q ".gpg" && echo true)" = "true" ]; then
                gpg -q --no-tty "$i"
		if [ "$?" = "0" ]; then
                    shred -fzu "$i"
		else
		    echo "File not decrypted."
		fi
            fi
        fi
    done
}

while getopts ":e:d:hv" opt; do
  case $opt in
    e)
      if [ -d "$OPTARG" ]; then
          cd $OPTARG
      else
          echo "No such directory. Nothing encrypted."
          exit 1
      fi
      #echo $OPTARG
      recursive-encrypt
      exit 0
      ;;
    d)
      if [ -d "$OPTARG" ]; then    
          cd $OPTARG
      else 
          echo "No such directory. Nothing encrypted."
          exit 1
      fi
      #echo $OPTARG
      #echo "Please enter decryption password:"
      #read -s PASSWORD
      recursive-decrypt
      exit 0
      ;;
    h)
      printf "$USAGE"
      exit 0
      ;;
    v)
      echo "$VERSION"
      exit 0
      ;;
    \?)
      echo "Incorrect arguments given"
      printf "$USAGE"
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires a directory as an argument."
      exit 1
      ;;
  esac
done

if [ "$OPTIND" = "1" ]; then
    echo "No arguments given"
    printf "$USAGE"
    exit 1
fi
