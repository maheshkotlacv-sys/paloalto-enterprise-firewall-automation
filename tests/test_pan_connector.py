"""
pan-os-python wrapper with retry logic and consistent error handling
reads creds from env: PANOS_HOSTNAME, PANOS_USERNAME, PANOS_PASSWORD
"""

import os
import logging
import time
from typing import Optional
from panos.firewall import Firewall
from panos.panorama import Panorama
from panos.errors import PanDeviceError, PanConnectionError

logger = logging.getLogger(__name__)


class PanConnector:
    """
    wraps pan-os-python connection to firewall or panorama
    use as context manager if you want cleanup:
        with PanConnector(hostname='10.x.x.x') as c:
            c.op('show system info')
    """

    def __init__(
        self,
        hostname: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        device_type: str = "firewall",
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        self.hostname = hostname or os.environ.get("PANOS_HOSTNAME")
        self.username = username or os.environ.get("PANOS_USERNAME")
        self.password = password or os.environ.get("PANOS_PASSWORD")
        self.device_type = device_type
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._device = None

        if not all([self.hostname, self.username, self.password]):
            raise ValueError(
                "need hostname, username, password - use env vars or pass directly"
            )

    def connect(self):
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"connecting to {self.hostname} (attempt {attempt}/{self.max_retries})")
                if self.device_type == "panorama":
                    self._device = Panorama(
                        hostname=self.hostname,
                        api_username=self.username,
                        api_password=self.password,
                    )
                else:
                    self._device = Firewall(
                        hostname=self.hostname,
                        api_username=self.username,
                        api_password=self.password,
                    )
                # quick sanity check
                info = self._device.op("show system info")
                host = info.find(".//hostname").text
                ver = info.find(".//sw-version").text
                logger.info(f"connected to {host} running panos {ver}")
                return self._device
            except PanConnectionError as e:
                logger.warning(f"attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
            except PanDeviceError as e:
                logger.error(f"device error {self.hostname}: {e}")
                raise
        raise PanConnectionError(f"couldnt connect to {self.hostname} after {self.max_retries} tries")

    @property
    def device(self):
        if self._device is None:
            self.connect()
        return self._device

    def op(self, cmd: str):
        try:
            return self.device.op(cmd)
        except PanDeviceError as e:
            logger.error(f"op failed {self.hostname}: {cmd!r} - {e}")
            raise

    def commit(self, description: str = "automated commit", sync: bool = True) -> str:
        try:
            logger.info(f"committing on {self.hostname}")
            result = self.device.commit(description=description, sync=sync)
            logger.info(f"commit done")
            return result
        except PanDeviceError as e:
            logger.error(f"commit failed {self.hostname}: {e}")
            raise

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._device = None
        return False


# aliases - some scripts use PANConnector/PanoramaConnector naming
PANConnector = PanConnector

class PanoramaConnector(PanConnector):
    """panorama-specific connector - thin wrapper that defaults device_type to panorama"""
    def __init__(self, hostname=None, username=None, password=None, **kwargs):
        hostname = hostname or os.environ.get("PANORAMA_HOSTNAME") or os.environ.get("PANOS_HOSTNAME")
        if not hostname:
            raise ValueError("need PANORAMA_HOSTNAME env var or pass hostname directly")
        super().__init__(hostname=hostname, username=username, password=password,
                         device_type="panorama", **kwargs)
