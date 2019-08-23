# Django Data Sync

Enables you to sync insensitive data between environments with any Django 
backends (as long the model definitions are the same) directly from admin 
interface.

## Features

- enables you to sync insensitive data between the same Django environments 
  (as long the model definitions are the same) directly from admin interface 
- relation fields are supported (ManyToMany needs to be tested)
- synchronous sync or in background (only Cloud Tasks is supported)

TO BE ADDED

- ~~add support for ImageField and FileField~~ DONE
- ~~support multiple tasks queues, current plan is to support GCP Cloud Tasks~~ DONE
- add authorization and authentication at data export endpoint

MIGHT GET ADDED

- compare data in JSON for audit purpose
- add support for another tasks queues so that is cloud platform agnostic


## Installation

    pip install django-data-sync
   

add `data_sync` to your `INSTALLED_APPS`

```python
    ...
    ...
    
    'data_sync',
    ....
    ....
```
 

Run migrate
```text
python manage.py migrate data_sync
```

Add to urlpatterns. Please do take note of the prefix URLs it will be used 
later.
e.g. most likely we will include this in `api` App, thus the prefix is `/api`.
```python
    path('', include('data_sync.urls')),
```
## Preface

Data Sync works by making use of natural key.
So I heavily recommend to read [django docs on this topic](https://docs.djangoproject.com/en/2.1/topics/serialization/#natural-keys) before going further.

You need to analyze your models and define their natural keys.
You can infer their natural keys usually from unique fields (and or `unique_together`).

Fields that are defined as unique or in `unique_together` can be defined by 
only using the field name  e.g. a Language is related to a Country.
In Language definition, 
the `unique_together` is usually the Country + the Language's ISO 639-1.

In code it'll look something like this

```python
unique_together = (( 'country', 'code'),)
```

Notice that `country` in unique_together itself is _abstract_.
What defines _a country_?
In context of `unique_together` it will be their ID, but ID is not natural key.
Country's natural key should be their ISO 2 code.

So we can infer that natural key of Language, programmatically, is 
the Country's ISO 2 code + the Language's ISO 639-1 

It'll look like this when you implement in code
```python
class Language(models.Model):
    def natural_key(self):
        return (self.country.code, self.code,)
```

In essence, natural key is usually combination of unique fields and or 
`unique_together`, but it needs to be more _verbose_.

## Usage

To get Data Sync working, you need to register the models that want to be 
synced.
**Only register insensitive models e.g. copy. Never sync sensitive 
models e.g. User as it can expose very sensitive data**.

To register the models, you need to decorate them and use custom managers.

```python
from django.db import models

import data_sync
    
    

@data_sync.register_model(natural_key=['code'])
class Country(models.Model):
    objects = data_sync.managers.DataSyncEnhancedManager()
    
    code = models.CharField(max_length=2)  # iso2
    ....
    ....


@data_sync.register_model(natural_key=['country.code', 'code'])
class Language(models.Model):
    objects = data_sync.managers.DataSyncEnhancedManager()
    
    code = models.CharField(max_length=2)  # iso 639-1
    ....
    ....


@data_sync.register_model(
    natural_key=['language.country.code', 'language.code', 'key'],
    fields=('value', 'key', 'language'),
    file_fields=('thumbnail',)
)
class Copy(models.Model):
    objects = data_sync.managers.DataSyncEnhancedManager()
    
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    value = models.TextField()
    key = models.CharField(max_length=255)
    default = models.TextField()
    thumbnail = models.ImageField()
    ....
    ....
```

### @data_sync.register_model

Here you need to define your natural key (read Preface for further topic).  
If natural key has value in related field, you need to use . (dot) notation.

You can also pass argument to `fields` parameter if you want to limit which 
fields that you want to be synced.

To add FileField into Data Sync, add them into `file_fields` parameter.

### DataSyncEnhancedManager

It looks like manager initialization is done at class loading.
So adding custom manager programmatically might be considered hacky 
(I would really like to love input on this).

For now, I'm afraid you must define custom manager, with the default 
attribute name i.e. `objects` to use DataSyncEnhancedManager.

DataSyncEnhancedManager just adds a `get_by_natural_key method` and no other 
else.

### Worker tasks

When the code is deployed to GAE (and GAE only, flex and kube not supported yet),
`data_sync` automatically uses Cloud Tasks with the queue id of `data_sync`.

### Settings and Configuration (WIP)

Data sync should work without additional settings 
(if using synchronous mode which is the default).

If you are deploying to GAE, it automatically uses Cloud Tasks, 
which you should fill the optionals below. 

#### Optionals

    DATA_SYNC_SERVICE_ACCOUNT_EMAIL
    
Defaults to ''. You need to fill this with GCP service account. You can use
GAE default service account. It is needed for OIDC validation as recommended
by GCP.
    
    DATA_SYNC_FORCE_SYNC

Defaults to `False`. Set this to `True` if you want to use synchronous
when deployed to GAE.

    DATA_SYNC_CLOUD_TASKS_QUEUE_ID

Defaults to `data_sync`

    DATA_SYNC_CLOUD_TASKS_LOCATION
    
Defaults to `europe-west1`

    DATA_SYNC_GOOGLE_CLOUD_PROJECT
    
Defaults to value of env var of `GOOGLE_CLOUD_PROJECT`.

    DATA_SYNC_GAE_VERSION

Defaults to value of env var of `GAE_VERSION`, which is already set by GAE.

    DATA_SYNC_GAE_SERVICE
    
Defaults to value of env var of `GAE_SERVICE`, which is already set by GAE.

### Data Source

Data Source holds information about an environment from which you want your
data to be synced.

The URL is dependant on where and how you include the `data_sync.urls` at
installation phase.

For example, if you include `data_sync.urls` in your `api` App urlpatterns,
then the URL in data source must be appended with your `api` URL.
Thus it might look something like this `https://example.com/api`.

If you include `data_sync.urls` in your root `urls`, then Data Source URL will
look like this `https://example.com`.

Do not include endslash.

### The Sync

To do a sync, simply create a Data Pull

## Compatibility

Python 3.7, Django 2.2 and up

## Testing

No automated tests (yet.....).

To test locally, you can spawn two django servers with different ports and 
different database and set the Data Source accordingly.
