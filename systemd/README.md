# Systemd Service

To use, copy the two service files to `/etc/systemd/system/`

```sh
cd systemd
cp *.service /etc/systemd/system/
systemctl enable steemvalue.service
systemctl enable steemvalue-backup.service
systemctl start steemvalue
```

By default, uses python3 WITHOUT a virtualenv to run:

```
/home/steemvalue/steem-value/app.py
```

Adjust the path as required once the service is installed.

--------------------------------

To use it with an existing virtualenv, change this line:

```
ExecStart=/usr/bin/env python3 /home/steemvalue/steem-value/app.py
```

To this (change the path to your venv):

```
ExecStart=/home/steemvalue/steem-value/venv/bin/python3 /home/steemvalue/steem-value/app.py
```


