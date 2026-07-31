class ObjectStorageError(Exception):
    pass


class UnsupportedFileTypeError(ObjectStorageError):
    pass


class UploadedFileTooLargeError(ObjectStorageError):
    pass


class ObjectUploadError(ObjectStorageError):
    pass
