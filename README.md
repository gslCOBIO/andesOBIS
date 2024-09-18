# andesOBIS
Creates an OBIS DwCA from ANDES


These exports scripts leverages the Django ORM, and thus have to be executed within the Django runtime.

# Quickstart

Clone the repo from within the Django root, and add `andesOBIS` to the `INSTALLED_APPS` (in `andes/settings.py`).

We will also use separate sqlite database to store/build the OBIS tables.
add this in the `DATABASES` dictionary in `andes/my_conf.py` or `andes/default_conf.py`
``` python
    "obisdb": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "obisdb.sqlite3"),
    },
```


The resulting config would perhaps look like this:
``` python
DATABASES = {
    'default': my_default_db,
    'obisdb': {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "obisdb.sqlite3"),
    },
}
```

Add the `DATABASE_ROUTERS` to (in `andes/settings.py`)
``` python
DATABASE_ROUTERS = ['andesOBIS.obis_router.OBISRouter',]
```

Use the `export_obis` command to create the archive.

``` bash
python manage.py export_obis
```


# notes
changes to the obis database can be managed with the `--database=obisdb` flag, eg

``` bash
./manage.py migrate --database=users
```

