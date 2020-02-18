#!/bin/sh
rsync -avhz mio@konink.de:/tmp/rid* /tmp/.
python manage.py import_html /tmp/rid_lines
python manage.py import_rid /tmp/rid
psql -U openebs2 -d OpenEBS2 -W -h 127.0.0.1 < kv1/scripts/import_rid.sql
