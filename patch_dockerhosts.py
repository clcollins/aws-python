#!/usr/bin/env python

# TO DO:
# Get reservations
# Read DOCKERIMAGE tag from Reservations
# Clone Reservation with new baseimage
# Remotely deploy Docker containers based on DOCKERIMAGE tag
# Move Elastic IPs, or Elkastic LB


get_all_reservations
  for reservation in reservations:
      identify dockerhosts
      build arrays of hashes of dockerhosts by image
      ie: dockerhosts = [
          reservation[0]: {'image': 'duke', 'IP': 'x.x.x.x'},
          reservation[1]: emergench
          reservation[2]: cachedns
      ]

create reservations
    tag as dockerhosts
    tag with payload
    for dockerhost in dockerhosts:
        deploy docker containers
        check docker containers
        associate IP


destroy old res
