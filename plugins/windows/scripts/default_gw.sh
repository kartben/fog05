#!/usr/bin/env bash
awk '$2 == 00000000 { print $1 }' /proc/net/route