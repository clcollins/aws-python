#!/usr/bin/env python

import boto.ec2
import boto.exception
import time
import sys

epoch = int(time.time())

default_region = 'us-west-2'
default_type = 't2.micro'
ami = 'baseimage'
key = 'root_aws'
security_groups = ['INTERNAL SSH', 'INTERNAL ICMP']
user_data = ''

dry_run = False
verbose = True

ssh_cmd = ("-oStrictHostKeyChecking=no -t "
           "'sudo yum update -y && sudo shutdown -h now'")

conn = boto.ec2.connect_to_region(default_region)


# STDERR FUNCTIONS
def debug(string):
    if verbose:
        print "DEBUG %s" % string


def warn(string):
    print "WARN %s" % string


def err(string):
    print "ERROR %s" % string
    sys.exit(1)


# INFORMATION FUCNTIONS
def get_attribute(resource_type, name, attribute):
    debug("[get_attribute] Type: %s" % resource_type)
    debug("[get_attribute] Name: %s" % name)

    debug("[get_attribute] Getting type %s ..." % resource_type)
    if resource_type == 'image':
        images = conn.get_all_images(owners='self')
        for image in images:
            count = 0
            if count < len(images):
                if getattr(image, 'name') == name:
                    debug("[get_attribute] Matched %s name: %s" % (
                        resource_type, getattr(image, 'name')))
                    debug("[get_attribute] %s %s: %s" % (
                        resource_type, attribute, getattr(image, attribute)))
                    return getattr(image, attribute)
                else:
                    debug("[get_attribute] Name '%s' not found in '%s'"
                          "(this is not necessarily bad)"
                          % (name, getattr(image, 'id')))
                    count = count + 1
                    pass
            else:
                err("[get_attribute] Unable to find %s: %s in any %s"
                    % (attribute, name, resource_type))

    else:
        err("[get_attribute] Unknown resource_type %s" % resource_type)


# INSTANCE FUNCTIONS
def run_instance(ami_id):
    debug("[run_instance] Launching instance from ami_id %s" % ami_id)
    new_reservation = conn.run_instances(
        image_id=ami_id,
        instance_type=default_type,
        key_name=key,
        user_data=user_data,
        security_groups=security_groups,
        dry_run=dry_run
    )
    debug("[run_instance] Reservation created: %s" % new_reservation)
    debug("[run_instance] Checking new instance id")
    instance_id = getattr(new_reservation.instances[0], 'id')
    debug("[run_instance] Instance ID: %s" % instance_id)
    return instance_id


def terminate_instance(instance_id):
    debug("[terminate_instance] Terminating %s" % instance_id)
    term = conn.terminate_instances(instance_ids=[instance_id],
                                    dry_run=dry_run)

    if len(term) > 1:
        err("[terminate_instance] Yeah, so, I terminated more"
            "than 1 instance:\n"
            "Instances: %s\n"
            "You might, uh, want to check on that..." % term)
    for instance in term:
        return instance.id


def wait_for_instance(instance_id):
    exists = False
    count = 0
    last_count = 30
    sleeptime = 10
    while exists is False:
        if count < last_count:
            reservations = conn.get_all_instances()
            for reservation in reservations:
                for instance in reservation.instances:
                    if getattr(instance, 'id') == instance_id:
                        exists = True
                    else:
                        debug("[wait_for_instance] "
                              "Checking instance %s exists (%d/%d)"
                              % (instance_id, count + 1, last_count))
                        count = count + 1
                        time.sleep(sleeptime)
        else:
            err("[wait_for_image] Waited %d seconds for %s "
                "to become available, in vain."
                % ((last_count * sleeptime), instance_id))
    return True


def check_instance_status(resource_id, status):
    debug("[wait_for_status] Checking Instance ID '%s' for status '%s'" % (
          resource_id, status))

    reservations = conn.get_all_instances(instance_ids=[resource_id])

    # There should only ever be 1 matching reservation
    if len(reservations) == 1:
        for res in reservations:
            instances = getattr(res, 'instances')
            # Similarly, there should only be 1 instance in the reservation
            if len(instances) == 1:
                returned_status = instances[0].update()
                while returned_status != status:
                    debug("[wait_for_status] Status check for instance "
                          "%s returned '%s'; needs '%s'"
                          % (resource_id, returned_status, status))
                    time.sleep(10)
                    returned_status = instances[0].update()
            else:
                err("[wait_for_status] Received more than 1 instance: "
                    "%s" % instances)
    else:
        err("[wait_for_status] Received more than 1 reservation: "
            "%s" % reservations)

    if returned_status == status:
        debug("[wait_for_status] %s status is %s" % (resource_id, status))
        return True


# IMAGE FUNCTIONS
def create_new_ami(instance_id):
    new_ami_name = ami + "-%d" % epoch
    debug("[create_new_ami] Creating new ami %s from instance %s"
          % (new_ami_name, instance_id))
    new_ami_id = conn.create_image(instance_id,
                                   name=new_ami_name,
                                   description=new_ami_name,
                                   dry_run=dry_run)

    debug("[create_new_ami] New AMI created: %s" % new_ami_id)
    return new_ami_id


def rotate_ami(new_ami_id):
    penultimate = 'penultimate'
    antepenultimate = 'antepenultimate'

    ami_id = get_attribute('image', ami, 'id')
    pen_id = get_attribute('image', penultimate, 'id')
    ant_id = get_attribute('image', antepenultimate, 'id')

    if (ami_id) and (not dry_run):
        debug("[rotate_ami] Rotating images]")
        # If we have a baseimage,
        # check to see if we have a penultimate baseimage
        if pen_id:
            # If we have a penultimate baseimage
            # check to see if we have an antepenultimate baseimage
            if ant_id:
                debug("[rotate_ami] Rotating (deleting) %s image"
                      % antepenultimate)
                conn.deregister_image(ant_id, dry_run=dry_run)

            debug("[rotate_ami] Rotating %s image" % penultimate)
            conn.copy_image(default_region, pen_id, name=antepenultimate)
            conn.deregister_image(pen_id, dry_run=dry_run)

        debug("[rotate_ami] Rotating %s image" % ami_id)
        conn.copy_image(default_region, ami_id, name=penultimate)
        conn.deregister_image(ami_id, dry_run=dry_run)

        debug("[rotate_ami] Renaming new image %s to %s" % (new_ami_id, ami))
        conn.copy_image(default_region, new_ami_id, name=ami)
        conn.deregister_image(new_ami_id, dry_run=dry_run)

    else:

        warn("[rotate_ami] Rotation skipped: Dry-run flag set")


def check_image_status(resource_id, status):
    images = conn.get_all_images(image_ids=[resource_id])
    # Should only ever get 1 image returned
    if len(images) == 1:
        returned_status = images[0].update()
        while returned_status != status:
            debug("[wait_for_status] Status check for image %s returned '%s';"
                  "needs '%s'" % (resource_id, returned_status, status))
            time.sleep(10)
            returned_status = images[0].update()
    else:
        err("wait_for_status] Received more than 1 image: %s" % images)

    if returned_status == status:
        debug("[wait_for_status] %s status is %s" % (resource_id, status))
        return True


def wait_for_image(image_id):
    exists = False
    count = 0
    last_count = 30
    sleeptime = 10

    while exists is False:
        if count < last_count:
            images = conn.get_all_images(owners='self')
            for image in images:
                if getattr(image, 'id') == image_id:
                    exists = True
                else:
                    debug("[wait_for_image] Checking image %s exists "
                          "(%d/%d)" % (image_id, count + 1, last_count))
                    count = count + 1
                    time.sleep(sleeptime)
        else:
            err("[wait_for_image] Waited %d seconds for %s "
                "to become available, in vain."
                % ((last_count * sleeptime), image_id))
    return True


def main():
    # Get the AMI ID for the baseimage AMI
    ami_id = get_attribute('image', ami, 'id')
    # Create the baseimage instance, and start it
    debug("[main] Creating instance from AMI %s: %s" % (ami, ami_id))
    instance_id = run_instance(ami_id)
    # Wait until the instances registers as existing
    debug("[main] Waiting for instance %s to be created" % instance_id)
    wait_for_instance(instance_id)
    # Wait for the instance to become available
    debug("[main] Waiting for instance %s to reach 'running' status"
          % instance_id)
    check_instance_status(instance_id, 'running')
    print "SSH GOES HERE: DO YOUR THING"
    # Wait until the instance stops before creating the new baseimage
    debug("[main] Waiting for instance %s to reach 'stopped' status"
          % instance_id)
    check_instance_status(instance_id, 'stopped')
    # Create the new baseimage
    debug("[main] Creating new %s image from %s" % (ami, instance_id))
    new_ami_id = create_new_ami(instance_id)
    # Wait until the image registers as existing
    debug("[main] Waiting for image %s to be created" % new_ami_id)
    wait_for_image(new_ami_id)
    # Wait for new baseimage to become ready
    debug("[main] Waiting for image %s to reach 'available' status"
          % new_ami_id)
    check_image_status(new_ami_id, 'available')
    # Rotate out the old images
    debug("[main] Rotating baseimage family")
    rotate_ami(new_ami_id)
    # Delete the baseimage instance
    debug("[main] Terminating instance %s" % instance_id)
    term = terminate_instance(instance_id)
    debug("[main] Waiting for instance %s to reach 'terminated' status"
          % instance_id)
    check_instance_status(term, 'terminated')
    return debug("[main] Patch run complete; have a nice day!")

main()
