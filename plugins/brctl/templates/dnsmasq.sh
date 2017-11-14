#!/usr/bin/env bash

sudo dnsmasq --interface={{ bridge_name }} --bind-interfaces  --dhcp-range={{ dhcp_start }},{{ dhcp_end }} --listen-address {{ listen_addr }} -x  {{ pid_path }}