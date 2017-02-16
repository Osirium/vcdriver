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


class IpError(Exception):
    def __init__(self, ip):
        super(IpError, self).__init__(
            '"{}" is not a valid IPv4/IPv6 address'.format(ip)
        )


class TimeoutError(Exception):
    def __init__(self, description, timeout):
        super(TimeoutError, self).__init__(
            '"{}" timed out ({} secs)'.format(description, timeout)
        )


class RemoteCommandError(Exception):
    def __init__(self, command, return_code):
        super(RemoteCommandError, self).__init__(
            'Remote execution of "{}" failed with exit code {}'.format(
                command, return_code
            )
        )


class SshError(RemoteCommandError):
    pass


class WinRmError(RemoteCommandError):
    pass


class FileTransferError(Exception):
    def __init__(self, local_path, remote_path):
        super(FileTransferError, self).__init__(
            'Local path: "{}" Remote path: "{}"'.format(
                local_path, remote_path
            )
        )


class UploadError(FileTransferError):
    pass


class DownloadError(FileTransferError):
    pass


class MissingCredentialsError(Exception):
    def __init__(self, credentials):
        super(MissingCredentialsError, self).__init__(
            'Your virtual machine object needs the following attributes: {}'
            ''.format(credentials)
        )
