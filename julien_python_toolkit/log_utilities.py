# This file is part of the "your-package-name" project.
# It is licensed under the "Custom Non-Commercial License".
# You may not use this file for commercial purposes without
# explicit permission from the author.


import logging
import logging.handlers
import os

# Helper Tools
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR


class Logger():

	# NOTE: For logging to a file, this class uses a RotatingFileHandler, which rotates the log files.
	#		The logger first starts by writing to a ".log" file adding new entries to the bottom. Once
	#		the file reaches a certain size (1MB in our case), it will move all the logs from the ".log"
	#		file to a ".log.1" file, and then start writing new logs to the ".log" file. The next time
	#		the ".log" file reaches 1MB, it will move all the logs from the ".log" file to the ".log.1"
	#		file, and then move the logs from the ".log.1" file to the ".log.2" file, and so on. However
	#		we only keep 5 log files, so once the ".log.5" file is full, it will delete the ".log.5" file.

	def __init__(self, name, file_name, stream_log_level = WARNING, file_log_level = INFO):
	
		self._logger = self._set_logger(name, file_name, stream_log_level, file_log_level)

	def _set_logger(self, name, file_name, stream_log_level = logging.WARNING, file_log_level = logging.INFO):

		log_folder = os.path.join(os.getcwd(), "logs")

		if not os.path.exists(log_folder):
			os.makedirs(log_folder)

		logger = logging.getLogger(name)
		logger.setLevel(logging.DEBUG)

		handler = logging.StreamHandler()  # Add a stream handler to print logs to the console
		handler.setLevel(stream_log_level)

		file_handler = logging.handlers.RotatingFileHandler(filename=os.path.join(log_folder, file_name), maxBytes=1024*1024, backupCount=5)
		file_handler.setLevel(file_log_level)

		formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
		handler.setFormatter(formatter)
		file_handler.setFormatter(formatter)

		logger.addHandler(handler)
		logger.addHandler(file_handler)

		return logger

	def debug(self, message):
		self._logger.debug(message)

	def info(self, message):
		self._logger.info(message)

	def warn(self, message):
		self._logger.warn(message)

	def error(self, message):
		self._logger.error(message)

	def set_stream_log_level(self, log_level):
		
		for handler in logger.handlers:
			if isinstance(handler, logging.StreamHandler) and stream_log_level is not None:
				handler.setLevel(stream_log_level)
		
	def set_file_log_level(self, log_level):
		
		for handler in logger.handlers:
			if isinstance(handler, logging.RotatingFileHandler) and stream_log_level is not None:
				handler.setLevel(stream_log_level)