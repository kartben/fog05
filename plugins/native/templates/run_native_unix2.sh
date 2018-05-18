#!/usr/bin/env bash

sh -c {{ command }} & echo $! > {{outfile}}.pid