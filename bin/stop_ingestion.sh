#!/bin/bash
kill $(ps aux | grep 'ingest_respawn_data' | grep -v grep | awk '{print $2}') || true
