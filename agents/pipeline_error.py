DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
SSL_CERTIFICATE_VERIFY_FAILED = "SSL_CERTIFICATE_VERIFY_FAILED"
SOURCE_FETCH_FAILED = "SOURCE_FETCH_FAILED"
UNEXPECTED_ERROR = "UNEXPECTED_ERROR"


class PipelineError(RuntimeError):

    EXIT_CODE_BY_ERROR_CODE = {
        DEPENDENCY_MISSING: 3,
        SSL_CERTIFICATE_VERIFY_FAILED: 4,
        SOURCE_FETCH_FAILED: 5,
        UNEXPECTED_ERROR: 2,
    }

    def __init__(self, code, message, exit_code=None):
        super().__init__(message)
        self.code = code
        self.exit_code = self._resolve_exit_code(code, exit_code)

    @classmethod
    def _resolve_exit_code(cls, code, exit_code):
        if exit_code is not None:
            return int(exit_code)
        return cls.EXIT_CODE_BY_ERROR_CODE.get(code, 2)