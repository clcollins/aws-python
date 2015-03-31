#!/usr/bin/env python

import boto.ec2

def_region='us-west-2'

conn=boto.ec2.connect_to_region(def_region)

images = conn.get_all_images(owners='self')

for image in images:
    if 'Name' in image.tags:
        print "%s (%s) [%s]" % (image.tags['Name'], image.id, image.state)
    else:
        print "<undef> (%s) [%s]" % (image.id, image.state)
