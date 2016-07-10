#define exception message
import sys
from oslo.config import cfg
from log import logger

exc_log_opts = [
    cfg.BoolOpt('fatal_exception_format_errors',
                default=False,
                help='Make exception message format errors fatal.'),
]
CONF = cfg.CONF
CONF.register_opt(exc_log_opts)


class NovaException(Exception):
    """Base Nova Exception
    """

    msg_fmt = ("An unknown exception occurred.")
    code = 500
    headers = {}
    safe = False


