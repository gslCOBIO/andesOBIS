# andesOBIS
Creates an OBIS DwCA from ANDES


These exports scripts leverages the Django ORM, and thus have to be executed within the Django runtime.

# Quickstart

Clone the repo from within the Django root, and add `andesOBIS` to the `INSTALLED_APPS` 

Use the `export_obis` command to create the archive.

``` bash
python manage.py export_obis
```

