class PipelineError(RuntimeError):
    def __init__(self, code, message, exit_code=2):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code