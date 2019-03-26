from __future__ import absolute_import
import sys

def currentframe():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        return sys.exc_info()[2].tb_frame.f_back
