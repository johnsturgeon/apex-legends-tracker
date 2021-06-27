#!/bin/bash
kill $(ps aux | grep 'flower' | grep -v grep | grep -v stop_flower | awk '{print $2}') || true
