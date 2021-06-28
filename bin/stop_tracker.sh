#!/bin/bash
kill $(ps aux | grep 'save_api_data_to_db' | grep -v grep | awk '{print $2}') || true
kill $(ps aux | grep 'ingest_respawn_data' | grep -v grep | awk '{print $2}') || true
