# This file is part of the "your-package-name" project.
# It is licensed under the "Custom Non-Commercial License".
# You may not use this file for commercial purposes without
# explicit permission from the author.


import ssl
import smtplib
import time
from email.message import EmailMessage
import certifi
import socket

from . import log_utilities


# Video tutorial
# https://www.youtube.com/watch?v=g_j6ILT-X0k

# App passwords help page
# https://support.google.com/accounts/answer/185833?hl=en


# Setup Logger
logger = log_utilities.Logger("EmailGroup", "email_group.log", stream_log_level = log_utilities.INFO, file_log_level = log_utilities.DEBUG)

class EmailSender():

    def __init__(self, sender_email, sender_password, receiver_emails):

        self._sender_email = sender_email
        self._sender_password = sender_password
        self._receiver_emails = receiver_emails
        self._smtp = None
        self._connect_and_login()  # Establish connection and login

    def __del__(self):

        if self._smtp and self._smtp.sock is not None:
            try:
                self._smtp.quit()
                logger.info("SMTP connection closed.")
            except smtplib.SMTPServerDisconnected:
                logger.info("SMTP connection was already closed.")
            except Exception as e:
                logger.error(f"Error closing SMTP connection: {e}")

    def _connect_and_login_with_retry(self):

        retries = 0

        while retries < 8:

            try:
                self._connect_and_login()
            
            except Exception as error:

                logger.warn(f"Error connecting and logging in: {error.__class__.__name__}({error}).")

                if isinstance(error, socket.timeout) or isinstance(error, socket.gaierror) or isinstance(error, ssl.SSLError):

                    logger.warn(f"Function '{self._connect_and_login.__name__}' timed out. Retrying. Retry count: {retries + 1}/8. Curent delay: {2 ** (retries + 1)} seconds.")

                    retries += 1
                    delay = 2 ** retries
                    time.sleep(delay)

                else:
                    raise error from error

            raise TimeoutError("Exceeded maximum retries.")

    def _connect_and_login(self):

        try:

            context = ssl.create_default_context()
            context.load_verify_locations(certifi.where())
            self._smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context)
            self._smtp.login(self._sender_email, self._sender_password)
            logger.info("Connected and logged in to SMTP server.")

        except Exception as e:

            logger.error(f"Failed to connect and login: {e}")
            raise e

    def _reconnect_if_needed(self):

        # Reconnect to the SMTP server if the connection is lost.

        try:

            status = self._smtp.noop()

            if status[0] != 250:
                raise smtplib.SMTPException("SMTP connection is not healthy")

        except (smtplib.SMTPException, AttributeError):

            logger.warning("SMTP connection lost, reconnecting...")
            self._connect_and_login()
    
    def send_emails(self, subject, body):

        for receiver_email in self._receiver_emails:
            self._send_email(receiver_email, subject, body)

    def _send_email(self, receiver_email, subject, body):

        em = EmailMessage()
        em["From"] = self._sender_email
        em["To"] = receiver_email
        em["Subject"] = subject
        em.set_content(body)

        self._reconnect_if_needed() # Ensure connection is active before sending

        try:
            start_time = time.time()
            self._smtp.send_message(em)
            seconds_elapsed = time.time() - start_time
            logger.info(f"Sent email to '{receiver_email}' in {seconds_elapsed:.2f} seconds.")
        except Exception as e:
            logger.error(f"Failed to send email to '{receiver_email}': {e}")  