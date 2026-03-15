"""
pan-os-python wrapper with retry logic and consistent error handling
reads creds from env: PANOS_HOSTNAME, PANOS_USERNAME, PANOS_PASSWORD
optionally PANOS_API_KEY if you prefer key auth over user/pass
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
        api_key: Optional[str] = None,
        device_type: str = "firewall",
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        self.hostname = hostname or os.environ.get("PANOS_HOSTNAME")
        self.username = username or os.environ.get("PANOS_USERNAME")
        self.password = password or os.environ.get("PANOS_PASSWORD")
        self.api_key = api_key or os.environ.get("PANOS_API_KEY")
        self.device_type = device_type
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._device = None

        # need either api_key or username+password to authenticate
        has_key = bool(self.api_key)
        has_creds = bool(self.username and self.password)
        if not self.hostname or (not has_key and not has_creds):
            raise ValueError(
                "need hostname + (api_key or username/password) — "
                "set via environment variables or pass directly"
            )

    def connect(self):
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"connecting to {self.hostname} (attempt {attempt}/{self.max_retries})")
                conn_kwargs = {"hostname": self.hostname}
                if self.api_key:
                    conn_kwargs["api_key"] = self.api_key
                else:
                    conn_kwargs["api_username"] = self.username
                    conn_kwargs["api_password"] = self.password

                if self.device_type == "panorama":
                    self._device = Panorama(**conn_kwargs)
                else:
                    self._device = Firewall(**conn_kwargs)

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
        """run an operational command, returns raw xml element"""
        try:
            return self.device.op(cmd)
        except PanDeviceError as e:
            logger.error(f"op failed {self.hostname}: {cmd!r} - {e}")
            raise

    def op_cmd(self, cmd: str):
        """alias for op() — used by scripts that prefer the explicit name"""
        return self.op(cmd)

    def get_system_info(self) -> dict:
        """pull hostname, sw-version, model etc into a flat dict"""
        info = self.op("show system info")
        result = {}
        system = info.find(".//system")
        if system is not None:
            for child in system:
                result[child.tag] = child.text or ""
        return result

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


# alias so scripts can import either name
PANConnector = PanConnector


class PanoramaConnector(PanConnector):
    """
    panorama-specific connector — defaults device_type to panorama
    reads PANORAMA_HOSTNAME from env if hostname not passed directly
    """

    def __init__(
        self,
        hostname: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        hostname = hostname or os.environ.get("PANORAMA_HOSTNAME")
        if not hostname:
            raise ValueError(
                "need PANORAMA_HOSTNAME — set env var or pass hostname directly"
            )
        super().__init__(
            hostname=hostname,
            username=username,
            password=password,
            api_key=api_key,
            device_type="panorama",
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
