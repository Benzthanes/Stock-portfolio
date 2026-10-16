"""Test package setup. Blocks real network access unless ALLOW_NETWORK=1.

Importing this package (unittest does so with `discover -s tests -t .`) patches
socket.socket.connect so an unmocked HTTP call fails fast instead of hitting
Yahoo, TradingView, Google News or Translate.
"""

import os
import socket

if os.environ.get("ALLOW_NETWORK") != "1":
    def _blocked_connect(self, address, *args, **kwargs):
        if self.family == getattr(socket, "AF_UNIX", None):
            return _real_connect(self, address, *args, **kwargs)
        raise OSError(f"Network access blocked in tests (connect to {address!r}). Mock it or set ALLOW_NETWORK=1.")

    _real_connect = socket.socket.connect
    socket.socket.connect = _blocked_connect
    socket.socket.connect_ex = lambda self, address: _blocked_connect(self, address)
