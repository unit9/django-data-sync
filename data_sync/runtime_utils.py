import os


def is_in_gae():
    """
    is NOT is in GCP, because it checks against GAE only env vars
    """
    if 'python' in os.getenv('GAE_RUNTIME', ''):
        return True
    return False


def is_in_kube():
    raise NotImplementedError
