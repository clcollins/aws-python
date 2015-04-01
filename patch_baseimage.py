#!/usr/bin/env python

import boto.ec2
import time

# Assumes a three version base AMI image maintenace program

def_region = 'us-west-2'
def_type = 't2.micro'

# The default Baseimage AMI names
ami = 'baseimage'
ami_prev = "baseimage_previous"
ami_last = "baseimage_last"
ami_new = "PENDING"

key = 'root_aws'
user_data = ''
dry_run = False
verbose = True


# Add any extra security groups to the default list
def_sec_grp = ['INTERNAL SSH']
add_sec_grps = ['INTERNAL Pings']

sec_grps = def_sec_grp + add_sec_grps

conn = boto.ec2.connect_to_region(def_region)


def debug(string):
    if verbose:
        print string


def warn(string):
    print string


def get_image_id(name):
    debug(name)
    images = conn.get_all_images(owners='self')

    for image in images:
        if image.name == name:
            debug("name:" + name + ", ID:" + image.id)
            return image.id


def rotate_ami(new_id):
    ami_id = get_image_id(ami)
    previous_id = get_image_id(ami_prev)
    last_id = get_image_id(ami_last)

    if (ami_id) and (not dry_run):

        debug("Rotating images")
        # If we have a baseimage,
        # then check to see if we have a previous image
        if previous_id:
            # If we have a previous image,
            # then check to see if we have a last image
            if last_id:
                debug("Rotating: " + last_id)
                conn.deregister_image(last_id, dry_run=dry_run)

            debug("Rotating: " + previous_id)
            conn.copy_image(def_region, previous_id, name=ami_last)
            conn.deregister_image(previous_id, dry_run=dry_run)

        debug("Rotating: " + ami_id)
        conn.copy_image(def_region, ami_id, name=ami_prev)
        conn.deregister_image(ami_id, dry_run=dry_run)

        debug("Renaming: " + new_id)
        conn.copy_image(def_region, new_id, name=ami)
        conn.deregister_image(new_id, dry_run=dry_run)

    else:

        warn("Rotation of images did not occur: Dry Run flag set")


def create_new_ami(instance):
    warn("BASEIMAGE MUST BECOME AVAILABLE - THIS MAY TAKE A WHILE")
    create_image(instance, name=ami_new, description=ami_new, dry_run=dry_run)

    new = get_image_id(ami_new)

    status = new.update()
    while status == 'pending':
        time.sleep(10)
        status = new.update()

    if status == 'available':
        # The new base image has been created and is available;
        # Delete the parent instance & begin the rotation
        # TODO: delete_instance(instance)
        rotate_ami(new)

    else:
        warn('Status: ' + status)
        return None


def launch_instance(region, itype, ami, key, user_data, sec_grps, dry_run):

    reservation = conn.run_instances(image_id=ami,
                                     instance_type=itype,
                                     key_name=key,
                                     user_data=user_data,
                                     security_groups=sec_grps,
                                     dry_run=dry_run)

    i = reservation.instances[0]
    status = i.update()
    while status == 'pending':
        time.sleep(10)
        status = i.update()

    if status == 'running':

            i.add_tag('Name', 'baseimage', dry_run=dry_run)
            debug("Instance created: " + i.id)
            return i.id

    else:
        warn('Status: ' + status)
        return None


# def ssh_and_patch(instance_id):

    # TODO: figure out the paramiko ssh client to handle yum updates


# THE ORDER:
# ami_id = get_image_id(ami)
# instance = launch_instance(def_region,
#                            def_type,
#                            ami_id,
#                            key,
#                            user_data,
#                            sec_grps,
#                            dry_run)

# ssh_and_patch(instance) & shutdown!
# create_new_ami(instance) - runs rotate when done
