# Redfish

Redfish API allows you to interact with server hardware, firmware, and 
management interfaces. It is an open standard currently adopted by many 
server builders, such as HP Enterprise, Dell EMC, and Supermicro. 

Currently, scripts here allow you to simplify the provisioning of 
servers that are have the Redfish standard integrated onto their management
interfaces. In the future, I will add more and more scripts and examples for 
various server types. 

## How to run

There is a handy Vagrant file in this repository and various provisioner
scripts and files to create a ready-made VM for your testing. 
Just make sure that you have the following on your computer.
* [Vagrant](https://www.vagrantup.com/downloads.html) - Also, install the plugin: `vagrant plugin install vagrant-vbguest`
* [Virtualbox](https://www.virtualbox.org/wiki/Downloads) - I recommend downloading and installing the extension pack too
* [Working internet connection](https://en.wikipedia.org/wiki/Internet) - You will need this to download Redfish packages

First, git clone this repository. Then, navigate into the directory with the vagrant file. 
```cd redfish/vagrant/ubuntu_16.04_redfish/```

Now, bring the VM up:
```vagrant up```

Once it is up and provisioned, you can remote into the VM:
```vagrant ssh```

Now git clone this repository inside the guest. Then, you can start running 
the Redfish scripts. Just make sure that your guest VM 
can communicate with the server management interface.

## Documentation

* [HPE API doc](https://hewlettpackard.github.io/ilo-rest-api-docs/ilo5/#introduction) 
* [Dell paper](http://en.community.dell.com/techcenter/systems-management/w/wiki/12213.redfish)
