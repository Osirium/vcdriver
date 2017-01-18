class TooManyObjectsFound(Exception):
    def __init__(self, object_type, name):
        super(TooManyObjectsFound, self).__init__(
            'Two or more objects of type {} with name "{}" were found'.format(
                object_type, name
            )
        )


class NoObjectFound(Exception):
    def __init__(self, object_type, name):
        super(NoObjectFound, self).__init__(
            'No objects of type {} with name "{}" were found'.format(
                object_type, name
            )
        )


class TimeoutError(Exception):
    def __init__(self, description, timeout):
        super(TimeoutError, self).__init__(
            '"{}" timed out ({} secs)'.format(description, timeout)
        )


class SshError(Exception):
    def __init__(self, command, return_code):
        super(SshError, self).__init__(
            '"{}" failed with exit code {}'.format(command, return_code)
        )


class UploadError(Exception):
    def __init__(self, path):
        super(UploadError, self).__init__('Failed to upload "{}"'.format(path))


class DownloadError(Exception):
    def __init__(self, path):
        super(DownloadError, self).__init__(
            'Failed to download "{}"'.format(path)
        )
