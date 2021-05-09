#!/bin/bash
kill $(ps aux | grep 'save_api_data_to_db' | grep -v grep | awk '{print $2}') || true