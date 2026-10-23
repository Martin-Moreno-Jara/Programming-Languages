class SyntacticalError(Exception):
    """
    Custom exception class to raise when there is a syntactical error
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message

class NotLL1Error(Exception):
    """
    Custom exception class to raise when the given grammar is not LL1
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message