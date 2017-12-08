import logging
import time

class DLogger:
    class __SingletonLogger:
        def __init__(self, file_name=None, debug=False):

            if file_name is None:
                self.log_file = 'fosagent_log.log' # str('fosagent_log_%d.log' % int(time.time()))
            else:
                self.log_file = file_name

            self.debug = debug

            if debug:
                logging.basicConfig(format='[%(asctime)s] - [%(levelname)s] > %(message)s',
                                    level=logging.INFO)
            else:
                logging.basicConfig(filename=self.log_file,
                                    format='[%(asctime)s] - [%(levelname)s] > %(message)s',
                                    level=logging.INFO)

            self.logger = logging.getLogger(__name__)

        def info(self, caller, message):
            self.logger.info(str('< %s > %s') % (caller, message))

        def warning(self, caller, message):
            self.logger.warning(str('< %s > %s') % (caller, message))

        def error(self, caller, message):
            self.logger.error(str('< %s > %s') % (caller, message))

        def debug(self, caller, message):
            self.logger.debug(str('< %s > %s') % (caller, message))

    instance = None
    enabled = True

    def __init__(self, file_name=None, debug=False):

        if not DLogger.instance:
            DLogger.instance = DLogger.__SingletonLogger(file_name, debug)

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def info(self, caller, message):
        if self.enabled:
            self.instance.info(caller, message)

    def warning(self, caller, message):
        if self.enabled:
            self.instance.warning(caller, message)

    def error(self, caller, message):
        if self.enabled:
            self.instance.error(caller, message)

    def debug(self, caller, message):
        if self.enabled:
            self.instance.debug(caller, message)
