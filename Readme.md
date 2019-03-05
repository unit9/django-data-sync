##### This document is still in WIP
# Django Data Sync

Enables you to sync insensitive data between environments with any Django 
backends (as long the model definitions are the same) directly from admin 
interface.

## Features

- enables you to sync insensitive data between the same Django environments 
  (as long the model definitions are the same) directly from admin interface 
- relation fields are supported (ManyToMany needs to be tested)

TO BE ADDED

- add support for ImageField and FileField
- support multiple tasks queues, current plan is to support GAE TaskQueue and 
    dramatiq (default is sync)

MIGHT GET ADDED

- compare data in JSON for audit purpose

## Disclaimer (IMPORTANT)

The original codebase run in production projects twice.
This is an adaptation of the original codebase, and haven't yet gone
into production.

## Installation

Will not hosted on PyPI (yet).

    pip install git+https://github.com/unit9/django-data-sync
   

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

Add to urlpatterns. Please do take note of the prefix URLs.
Usually we include this in `/api` prefix.
```python
    path('', include('data_sync.urls')),
```
## Preface

Data Sync works by making use of natural key.
So I heavily recommend to read [django docs on this topic](https://docs.djangoproject.com/en/2.1/topics/serialization/#natural-keys) before going further.

You need to analyze your models and define their natural keys.
You can infer their natural keys usually from unique fields (and or `unique_together`).

Fields that are defined as unique or in `unique_together` can be defined by 
only using the field name  e.g. a Language is related to a Country,
in Language definition, 
the `unique_together` is usually the Language's ISO 639-1 and the Country.

In code it'll look something like this

```python
unique_together = (('iso_code', 'country'),)
```

Notice that `country` in unique_together itself is _abstract_.
What defines _a country_?
In context of `unique_together` it will be their ID, but ID is not natural key.
Country's natural key should be their ISO 2 code.

So we can infer that natural key of Language, programmatically, is 
the Language's ISO 639-1 + the Country's ISO 2 code.

It'll look like this when you implement in code
```python
class Language(models.Model):
    def natural_key(self):
        return (self.country.code, self.code,)
```

In essence, natural key is usually combination of unique fields and or 
`unique_together`, but it needs to be more _precise_.

## Usage

To get Data Sync working, you need to register the models that want to be 
synced.
**Only register insensitive models e.g. copy. Never sync sensitive 
models e.g. User as it can expose very sensitive data**.
Authentication and authorization support might get added in the future.

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
    fields=('value', 'key', 'language')
)
class Copy(models.Model):
    objects = data_sync.managers.DataSyncEnhancedManager()
    
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    value = models.TextField()
    key = models.CharField(max_length=255)
    default = models.TextField()
    ....
    ....
```

### @data_sync.register_model

Here you need to define your natural key (read Preface for further topic).  
If natural key has value in related field, you need to use . (dot) notation.

You can also pass argument to `fields` parameter if you want to limit which 
fields that you want to be synced.

### DataSyncEnhancedManager

It looks like manager initialization is done at class loading.
So adding custom manager programmatically might be considered hacky 
(I would really like to love input on this).

For now, I'm afraid you must define custom manager, with the default 
attribute name i.e. `objects` to use DataSyncEnhancedManager.

DataSyncEnhancedManager just adds a `get_by_natural_key method` and no other 
else.


### Data Source

Data Source holds information about an environment from which you want your
data to be synced.

The URL is dependant on where and how you include the `data_sync.urls` at
installation phase.

For example, if you include `data_sync.urls` in your `api` App urlpatterns,
then the URL in data source must be appended with your `api` URL which might
looks something like this `https://example.com/api`.

If you include `data_sync.urls` in your root `urls`, then Data Source URL will
looks like this `https://example.com`.

Do not include endslash.

### The Sync

To do a sync, simply create a Data Pull

## Compatibility

Python 3.4 and up, Django 2.0 and up

## Testing

No tests yet.

To test locally, you can spawn two django servers with different ports and 
different database and set the Data Source accordingly.
