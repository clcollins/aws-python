#!/usr/bin/env python

import boto.ec2

def_region = 'us-west-2'

conn = boto.ec2.connect_to_region(def_region)

reservations = conn.get_all_reservations()
instances = []
for r in reservations:
    instances.extend(r.instances)

for i in instances:
    # print i.__dict__
    if 'Name' in i.tags:
        print "%s (%s) [%s]" % (i.tags['Name'], i.id, i.state)
    else:
        print "<undef> (%s) [%s]" %  (i.id, i.state)
