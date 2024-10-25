# This file is part of the "your-package-name" project.
# It is licensed under the "Custom Non-Commercial License".
# You may not use this file for commercial purposes without
# explicit permission from the author.


import os
import time
import socket
import ssl

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from . import log_utilities


# Global Variables
PATH_TO_THIS_FILE = os.path.dirname(os.path.realpath(__file__))


# Set Up Logger
logger = log_utilities.Logger("GoogleServices", "google_services.log", stream_log_level = log_utilities.WARNING, file_log_level = log_utilities.WARNING)


class GoogleServices():

    # How to use:
    # 1. Download credentials.json file from Google Cloud Console (see tutorial below).

    # NOTE: For drive access, you can only do it for personal drive, not shared drives.

    # Tutorial: https://www.youtube.com/watch?v=3wC-SCdJK2c&t=315s

    _SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    # need to perform the OAuth2 authorization flow once for the new spreadsheet, and it will generate a new token file specific to that spreadsheet

    _DEFAULT_PATH_TO_CREDENTIALS_FILE = os.path.join(PATH_TO_THIS_FILE, 'credentials.json')
    _DEFAULT_PATH_TO_TOKEN_FILE = os.path.join(PATH_TO_THIS_FILE, 'token.json')

    @staticmethod
    def retry_if_network_error(func):

        def wrapper(*args, **kwargs):

            retries = 0

            while retries < 10:

                try:
                    return func(*args, **kwargs)
                
                except Exception as error:

                    # NOTE: Add all the errors to retry here.
                    is_timeout_error = isinstance(error, TimeoutError)
                    is_too_many_requests_error = isinstance(error, HttpError) and error.__cause__.resp.status == 429
                    is_internal_server_error = isinstance(error, HttpError) and error.__cause__.resp.status == 500
                    is_bad_gateway_error = isinstance(error, HttpError) and error.__cause__.resp.status == 502
                    is_server_unavailable_error = isinstance(error, HttpError) and error.__cause__.resp.status == 503
                    is_socket_timeout_error = isinstance(error, socket.timeout)
                    is_socket_gaierror = isinstance(error, socket.gaierror)
                    is_ssl_error = isinstance(error, ssl.SSLError)

                    if (is_timeout_error or is_too_many_requests_error or is_internal_server_error \
                        or is_bad_gateway_error or is_server_unavailable_error or is_socket_timeout_error \
                        or is_socket_gaierror or is_ssl_error):

                        logger.warn(f"Function '{func.__name__}' network error. Retrying. Retry count: {retries + 1}/8. Curent delay: {2 ** (retries + 1)} seconds. Error = {error.__class__}({error}).")

                        retries += 1
                        delay = 2 ** retries
                        time.sleep(delay)

                    else:

                        logger.error(f"Function '{func.__name__}' raised an error. Error = {error.__class__}({error}).")

                        raise error from error

            raise TimeoutError("Exceeded maximum retries.")
        
        return wrapper

    def __init__(self, path_to_credentials_file = None, path_to_token_file = None):

        if path_to_credentials_file == None:
            path_to_credentials_file = self._DEFAULT_PATH_TO_CREDENTIALS_FILE
        if path_to_token_file == None:
            path_to_token_file = self._DEFAULT_PATH_TO_TOKEN_FILE

        self._path_to_credentials_file = path_to_credentials_file
        self._path_to_token_file = path_to_token_file
        self._sheet_service = None

        self.open()

    def open(self):

        try:

            credentials = None

            # A. If there is a token file, get credentials from token file.
            if os.path.exists(self._path_to_token_file):
                credentials = Credentials.from_authorized_user_file(self._path_to_token_file, self._SCOPES)

            # B. If credentials are not valid or do not exist.
            if not credentials or not credentials.valid:

                # a. If credentials exist but are just expired -> refresh token.
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())

                # b. Else -> get credentials from server (i.e. login).
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(self._path_to_credentials_file, self._SCOPES)
                    credentials = flow.run_local_server(port=0)

                # Update the token file.
                with open(self._path_to_token_file, "w") as token:
                    token.write(credentials.to_json())

            self._sheet_service = build("sheets", "v4", credentials = credentials)
            self._drive_service = build("drive", "v3", credentials = credentials)

        except Exception as error:
            raise Exception(f"Error initializing Google services: {error}")

    @retry_if_network_error        
    def write_csv_to_sheet(self, csv_data, spreadsheet_id, sheet_name):

        if self._sheet_service == None:
            raise Exception("Spreadsheet service is not initialized. Please run the 'open' function.")

        try:

            self._sheet_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!A1',
                valueInputOption='USER_ENTERED',
                body={'values': csv_data}
            ).execute()

        except HttpError as error:
            error_content = f"HttpError from {self.write_csv_to_sheet.__name__}: {error.content}".encode('utf-8')
            raise HttpError(resp=error.resp, content=error_content) from error

    @retry_if_network_error
    def write_csv_to_range(self, csv_data, spreadsheet_id, sheet_name, range_name):

        if self._sheet_service == None:
            raise Exception("Spreadsheet service is not initialized. Please run the 'open' function.")

        try:

            self._sheet_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!{range_name}',
                valueInputOption='USER_ENTERED',
                body={'values': csv_data}
            ).execute()
        
        except HttpError as error:
            error_content = f"HttpError from {self.write_csv_to_range.__name__}: {error.content}".encode('utf-8')
            raise HttpError(resp=error.resp, content=error_content) from error

    @retry_if_network_error
    def write_data_to_sheet_batch_update(self, ranges, values, spreadsheet_id):

        """
        Function to batch update values to google sheet.
        
        Example:

        values = [
                {'range': "Sheet1!A1:A100", 'values': [['Value A1']] * 100},
                {'range': "Sheet1!C1:C100", 'values': [['Value C1']] * 100},
                {'range': "Sheet1!E1:E100", 'values': [['Value E1']] * 100}
            ]
        """

        if self._sheet_service == None:
            raise Exception("Spreadsheet service is not initialized. Please run the 'open' function.")
                
        # Create values list of dict.
        value_list = []
        for range_name, data in zip(ranges, values):
            value_dict = {'range': range_name, 'values': data}
            value_list.append(value_dict)
        
        try:

            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': value_list
            }

            response = self._sheet_service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()

            return response
        
        except HttpError as error:
            error_content = f"HttpError from {self.write_data_to_sheet_batch_update.__name__}: {error.content}".encode('utf-8')
            raise HttpError(resp=error.resp, content=error_content) from error

    @retry_if_network_error
    def read_csv_from_sheet(self, spreadsheet_id, sheet_name):

        if self._sheet_service == None:
            raise Exception("Spreadsheet service is not initialized. Please run the 'open' function.")

        try:

            result = self._sheet_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=sheet_name
            ).execute()

            return result.get('values', [])
        
        except HttpError as error:
            error_content = f"HttpError from {self.read_csv_from_sheet.__name__}: {error.content}".encode('utf-8')
            raise HttpError(resp=error.resp, content=error_content) from error

    @retry_if_network_error
    def read_csv_from_range(self, spreadsheet_id, sheet_name, range_name):

        if self._sheet_service == None:
            raise Exception("Spreadsheet service is not initialized. Please run the 'open' function.")

        try:

            result = self._sheet_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!{range_name}'
            ).execute()

            return result.get('values', [])
        
        except HttpError as error:
            error_content = f"HttpError from {self.read_csv_from_range.__name__}: {error.content}".encode('utf-8')
            raise HttpError(resp=error.resp, content=error_content) from error

    @retry_if_network_error
    def get_sheet_names_from_sheet(self, spreadsheet_id):

        if self._sheet_service is None:
            raise Exception("Spreadsheet service is not initialized. Please run the 'open' function.")

        try:
            # Call the Sheets API to get the spreadsheet
            spreadsheet = self._sheet_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            
            # Extract the sheet names
            sheets = spreadsheet.get('sheets', [])
            sheet_names = [sheet['properties']['title'] for sheet in sheets]
            
            return sheet_names
        
        except HttpError as error:
            error_content = f"HttpError from {self.get_sheet_names_from_sheet.__name__}: {error.content}".encode('utf-8')
            raise HttpError(resp=error.resp, content=error_content) from error

    def get_subfolders_in_folder(self, folder_id):
    
        if self._drive_service == None:
            raise Exception("Drive service is not initialized. Please run the 'open' function.")

        try:

            query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            response = self._drive_service.files().list(q=query, 
                spaces='drive', fields='nextPageToken, files(id, name)').execute()
            folders = response.get('files', [])

            return folders
        
        except Exception as error:
            raise Exception(f"Error getting subfolders: {error}")
        
    def get_all_files_in_folder(self, folder_id):
        
        if self._drive_service == None:
            raise Exception("Drive service is not initialized. Please run the 'open' function.")

        try:

            query = f"'{folder_id}' in parents and trashed=false"
            response = self._drive_service.files().list(q=query, 
                spaces='drive', fields='nextPageToken, files(id, name, mimeType)').execute()
            files = response.get('files', [])

            return files
        
        except Exception as error:
            raise Exception(f"Error getting files in folder: {error}")
        
    def create_folder(self, new_folder_name, parent_folder_id):
            
        if self._drive_service == None:
            raise Exception("Drive service is not initialized. Please run the 'open' function.")

        try:

            file_metadata = {
                'name': new_folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }

            folder = self._drive_service.files().create(body=file_metadata, fields='id').execute()
            return folder.get('id')
        
        except Exception as error:
            raise Exception(f"Error creating folder: {error}")
        
    def check_if_subfolder_exists_in_folder(self, folder_id, subfolder_name):
        
        if self._drive_service == None:
            raise Exception("Drive service is not initialized. Please run the 'open' function.")

        try:

            query = f"'{folder_id}' in parents and name='{subfolder_name}' and trashed=false"
            response = self._drive_service.files().list(q=query, 
                spaces='drive', fields='nextPageToken, files(id, name)').execute()
            items = response.get('files', [])

            if items:
                return True, items[0]['id']  # Return True and details of the first matching item
            else:
                return False, None
        
        except Exception as error:
            raise Exception(f"Error checking if subfolder exists: {error}")

    def check_if_folder_exists(self, folder_id):

        if self._drive_service == None:
            raise Exception("Drive service is not initialized. Please run the 'open' function.")

        try:
            response = self._drive_service.files().get(fileId=folder_id, fields='id, trashed').execute()
            if 'trashed' in response and response['trashed']:
                return False
            return True

        except HttpError as error:
            if error.resp.status == 404:
                return False
            else:
                raise Exception(f"Error checking if folder exists: {error}")

    def upload_file_to_folder(self, file_path, folder_id, mime_type = None):

        # Mime type for PNG image = 'image/png'

        if mime_type == None:
            raise Exception("Mime type is not provided.")
        
        if self._drive_service == None:
            raise Exception("Drive service is not initialized. Please run the 'open' function.")

        try:

            file_metadata = {
                'name': os.path.basename(file_path),
                'parents': [folder_id]
            }

            media = MediaFileUpload(file_path, mimetype=mime_type)
            file = self._drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        
        except Exception as error:
            raise Exception(f"Error uploading file to folder: {error}")