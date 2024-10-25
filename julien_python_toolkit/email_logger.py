# This file is part of the "your-package-name" project.
# It is licensed under the "Custom Non-Commercial License".
# You may not use this file for commercial purposes without
# explicit permission from the author.


import datetime
import time


class EmailLogger:

    def __init__(self, email_sender, logger_name, subject, timestamp=True):

        self.email_sender = email_sender
        self.logger_name = logger_name
        self.subject = subject
        self.timestamp = timestamp
        self.buffer = []

    def critical(self, message):
        self._log_message(message, 'CRITICAL')

    def error(self, message):
        self._log_message(message, 'ERROR')

    def warning(self, message):
        self._log_message(message, 'WARNING')

    def info(self, message):
        self._log_message(message, 'INFO')

    def debug(self, message):
        self._log_message(message, 'DEBUG')

    def _log_message(self, message, log_level='INFO'):

        formatted_message = ""

        if self.timestamp:
            formatted_message += f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "

        formatted_message += f"{log_level} - {self.logger_name} - {message}"

        self.buffer.append(formatted_message)

    def send(self):

        if self.buffer:
            log_message = '\n'.join(self.buffer)
            self.email_sender.send_emails(self.subject, log_message)
            self.buffer = []


class TimedEmailLogger(EmailLogger):

    def __init__(self, email_sender, logger_name, subject, timestamp=True, interval=60):
        super().__init__(email_sender, logger_name, subject, timestamp=timestamp)
        self.interval = interval
        self.last_email_time = time.time()

    def _log_message(self, message, log_level='INFO'):
        super()._log_message(message, log_level)
        current_time = time.time()
        if current_time - self.last_email_time >= self.interval:
            self.send()
            self.last_email_time = current_time