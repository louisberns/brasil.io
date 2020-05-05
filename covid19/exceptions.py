class SpreadsheetValidationErrors(Exception):
    """
    Custom exception to hold all error messages raised when validating spreadsheets
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages = []

    def new_error(self, msg):
        self.error_messages.append(msg)

    def raise_if_errors(self):
        if self.error_messages:
            raise self

    def __str__(self):
        return " - ".join(self.error_messages)


class OnlyOneSpreadsheetException(Exception):
    """
    Raised when checking if a spreadsheet is ready to be imported but there's no other
    one to compare with
    """
