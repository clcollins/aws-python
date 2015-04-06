#!/usr/bin/env python

import boto.ec2
import sys

# Build full list of regions
default_region = 'us-west-2'
other_regions = ['us-east-1', 'ap-southeast-1']

ami = 'baseimage'
penultimate = 'penultimate'
antepenultimate = 'antepenultimate'

dry_run = False
verbose = True

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


def get_attribute(connection, resource_type, name, attribute):
    images = connection.get_all_images(owners='self')
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


def sync_amis(local_ami_id, reg_conn, region):
    ami_id = get_attribute(reg_conn, 'image', ami, 'id')
    pen_id = get_attribute(reg_conn, 'image', penultimate, 'id')
    ant_id = get_attribute(reg_conn, 'image', antepenultimate, 'id')

    if (local_ami_id) and (not dry_run):
        # If there is a remote baseimage
        # run through the rest of the rotations
        # Otherwise just get the baseimage from Us-West-2
        if ami_id:
            if pen_id:
                # If we have a penultimate baseimage
                # check to see if we have an antepenultimate baseimage
                # and rotate it out
                if ant_id:
                    debug("[sync_amis] %s: Rotating (deleting) %s image"
                          % (region, antepenultimate))
                    reg_conn.deregister_image(ant_id, dry_run=dry_run)

                # If there's a penultimate image,
                # rotate it to the antipenultimate
                debug("[sync_amis] %s: Rotating %s image"
                      % (region, penultimate))
                reg_conn.copy_image(region, pen_id, name=antepenultimate)
                reg_conn.deregister_image(pen_id, dry_run=dry_run)


            # If we have a local baseimage, rotate that to the penultimate
            debug("[sync_amis] %s: Rotating %s image"
                  % (region, ami_id))
            reg_conn.copy_image(region, ami_id, name=penultimate)
            reg_conn.deregister_image(ami_id, dry_run=dry_run)

        # If there's a local baseimage, copy it to the remote as baseimage
        debug("[sync_amis] Copying new image %s to region as %s"
              % (local_ami_id, ami))
        reg_conn.copy_image(default_region, local_ami_id, name=ami)

    else:

        warn("[sync_amis] Rotation skipped: Dry-run flag set")


def main():
    local_ami_id = get_attribute(conn, 'image', ami, 'id')

    for region in other_regions:
        reg_conn = boto.ec2.connect_to_region(region)
        debug("[sync_amis] Begining rotation of local baseimage to %s region"
              % region)
        sync_amis(local_ami_id, reg_conn, region)


main()
