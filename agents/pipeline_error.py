"""流水线错误码与标准异常定义。"""

DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
SSL_CERTIFICATE_VERIFY_FAILED = "SSL_CERTIFICATE_VERIFY_FAILED"
SOURCE_FETCH_TIMEOUT = "SOURCE_FETCH_TIMEOUT"
SOURCE_FETCH_RATE_LIMITED = "SOURCE_FETCH_RATE_LIMITED"
SOURCE_FETCH_UNAVAILABLE = "SOURCE_FETCH_UNAVAILABLE"
SOURCE_FETCH_FAILED = "SOURCE_FETCH_FAILED"
UNEXPECTED_ERROR = "UNEXPECTED_ERROR"


class PipelineError(RuntimeError):
    """携带错误码与进程退出码的流水线异常。"""

    EXIT_CODE_BY_ERROR_CODE = {
        DEPENDENCY_MISSING: 3,
        SSL_CERTIFICATE_VERIFY_FAILED: 4,
        SOURCE_FETCH_TIMEOUT: 6,
        SOURCE_FETCH_RATE_LIMITED: 7,
        SOURCE_FETCH_UNAVAILABLE: 8,
        SOURCE_FETCH_FAILED: 5,
        UNEXPECTED_ERROR: 2,
    }

    def __init__(self, code, message, exit_code=None):
        super().__init__(message)
        self.code = code
        self.exit_code = self._resolve_exit_code(code, exit_code)

    @classmethod
    def _resolve_exit_code(cls, code, exit_code):
        """根据错误码和可选覆盖值解析退出码。"""
        if exit_code is not None:
            return int(exit_code)
        return cls.EXIT_CODE_BY_ERROR_CODE.get(code, 2)
