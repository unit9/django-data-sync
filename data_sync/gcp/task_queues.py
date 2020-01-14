import json
import logging
from urllib.parse import urlparse

from django.conf import settings
from google.api_core.exceptions import NotFound

from google.cloud import tasks_v2beta3

from data_sync import url_constants


logger = logging.getLogger('gcp')


def setup_task_queue():
    """
    Create data-sync task queue if not exist
    """
    # duplicated client, kinda a problem if make them module level
    # at local which usually does not have default creds and can
    # make django starts very slow
    client = tasks_v2beta3.CloudTasksClient()

    queue_name = client.queue_path(
        settings.DATA_SYNC_GOOGLE_CLOUD_PROJECT,
        settings.DATA_SYNC_CLOUD_TASKS_LOCATION,
        settings.DATA_SYNC_CLOUD_TASKS_QUEUE_ID
    )
    try:
        client.get_queue(queue_name)
    except NotFound:
        parent = client.location_path(
            settings.DATA_SYNC_GOOGLE_CLOUD_PROJECT,
            settings.DATA_SYNC_CLOUD_TASKS_LOCATION
        )

        new_queue = {
            'name': queue_name,
            'retry_config': {
                'max_attempts': 1
            }
        }

        logger.info('data-sync queue not exist, creating..')
        r = client.create_queue(
            parent=parent,
            queue=new_queue
        )
        logger.info(
            'data-sync queue created with the name '
            f'{settings.DATA_SYNC_CLOUD_TASKS_QUEUE_ID}\n'
            f'{r}'
        )


def get_cloud_task_handler_url(data_source_base_url):
    """
    Get self version task handler URL
    """
    # since data sync urls can be registered inside another namespace
    # we can't reverse it reliably
    # however, we can infer it from the data_source_base_url
    parsed_data_source_base_url = urlparse(data_source_base_url)

    project_dependent_namespace = parsed_data_source_base_url.path

    service = settings.DATA_SYNC_GAE_SERVICE

    if service == 'default':
        version_service = settings.DATA_SYNC_GAE_VERSION
    else:
        version_service = (
            f'{settings.DATA_SYNC_GAE_VERSION}-dot-'
            f'{settings.DATA_SYNC_GAE_SERVICE}'
        )

    url = (
        f'https://{version_service}-dot-'
        f'{settings.DATA_SYNC_GOOGLE_CLOUD_PROJECT}.appspot.com'
    )
    url += project_dependent_namespace
    url += f'/{url_constants.RUN_DATA_SYNC_GAE_CLOUD_TASKS}'
    return url


def create_run_data_sync_task(data_pull_id, data_source_base_url):
    """
    Calls self version to run data sync
    """
    setup_task_queue()

    data = {
        'data_pull_id': data_pull_id,
        'data_source_base_url': data_source_base_url
    }
    encoded_data = json.dumps(data).encode()
    target_url = get_cloud_task_handler_url(data_source_base_url)
    task = {
        'http_request': {
            'http_method': 'POST',
            'url': target_url,
            'body': encoded_data,
            'oidc_token': {
                'service_account_email': settings.DATA_SYNC_SERVICE_ACCOUNT_EMAIL
            }
        },
    }

    client = tasks_v2beta3.CloudTasksClient()
    queue = client.queue_path(
        settings.DATA_SYNC_GOOGLE_CLOUD_PROJECT,
        settings.DATA_SYNC_CLOUD_TASKS_LOCATION,
        settings.DATA_SYNC_CLOUD_TASKS_QUEUE_ID
    )
    response = client.create_task(queue, task)

    logger.info(
        f'Data pull task initiated. ID: {data_pull_id} '
        f'SOURCE_URL: {data_source_base_url} '
        f'TASK URL: {target_url} '
        f'CLOUD TASKS RESPONSE: {response}'
    )

    return response
