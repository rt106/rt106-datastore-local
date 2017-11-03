#!/bin/sh
# Copyright (c) General Electric Company, 2017.  All rights reserved.

cd /rt106
if test ${DOWNLOAD_RAD_DEMO_DATA:-off} = 'on' || test ${DOWNLOAD_RAD_DEMO_DATA:-off} = 'force'; then
  (./download_rad_demo_data.sh && python create_rad_demo_datastore.py) &
fi

python /rt106/dataServer.py
