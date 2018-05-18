#!/usr/bin/env bash

sh -c {{ path }}/{{ command }} & echo $! > {{outfile}}.pid