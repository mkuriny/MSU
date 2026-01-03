import time
import paramiko
from typing import List, Optional


class SSHSession:
    def __init__(self, host, port, username, password, timeout=10):
        self.host = host
        self.port = port or 22
        self.username = username
        self.password = password
        self.timeout = timeout
        self.client = None
        self.channel = None

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False,
            )

            self.channel = self.client.invoke_shell()
            time.sleep(0.5)

            if not self.channel.recv_ready():
                raise RuntimeError("SSH shell opened but no prompt received")

            self.channel.recv(65535)

        except paramiko.AuthenticationException:
            self.close()
            raise RuntimeError("SSH authentication failed")

        except paramiko.SSHException as e:
            self.close()
            raise RuntimeError(f"SSH connection error: {e}")

        except Exception as e:
            self.close()
            raise RuntimeError(f"Unexpected SSH error: {e}")

    def send(self, cmd: str):
        if not self.channel:
            raise RuntimeError("SSH channel not initialized")

        try:
            self.channel.send(cmd + "\n")
            time.sleep(0.2)
        except Exception as e:
            raise RuntimeError(f"Failed to send command '{cmd}': {e}")

    def recv_until(self, prompts: List[str], timeout=15) -> str:
        output = ""
        start = time.time()

        while True:
            if self.channel.recv_ready():
                data = self.channel.recv(65535).decode(errors="ignore")
                output += data

                for p in prompts:
                    if output.rstrip().endswith(p):
                        return output

            if time.time() - start > timeout:
                raise TimeoutError("Timeout waiting for device prompt")

            time.sleep(0.2)

    def close(self):
        try:
            if self.channel:
                self.channel.close()
            if self.client:
                self.client.close()
        except Exception:
            pass


class DeviceProfile:
    name: str
    prompts: List[str]
    disable_paging: List[str]
    fetch_commands: List[str]

    def __init__(
        self,
        name: str,
        prompts: List[str],
        disable_paging: List[str],
        fetch_commands: List[str],
    ):
        self.name = name
        self.prompts = prompts
        self.disable_paging = disable_paging
        self.fetch_commands = fetch_commands


PROFILES = {
    "cisco": DeviceProfile(
        name="cisco",
        prompts=["#", ">"],
        disable_paging=["terminal length 0"],
        fetch_commands=["show running-config"],
    ),
    "huawei": DeviceProfile(
        name="huawei",
        prompts=[">", "]"],
        disable_paging=["screen-length 0 temporary"],
        fetch_commands=["display current-configuration"],
    ),
    "eltex": DeviceProfile(
        name="eltex",
        prompts=["#", ">"],
        disable_paging=["terminal length 0"],
        fetch_commands=["show running-config"],
    ),
    "harmonic": DeviceProfile(
        name="harmonic",
        prompts=["#", ">"],
        disable_paging=[],
        fetch_commands=["show config"],
    ),
}


class SSHConfigFetcher:
    def fetch(self, credential, vendor: str) -> str:
        profile = PROFILES.get(vendor.lower())
        if not profile:
            raise ValueError(f"Unsupported vendor: {vendor}")

        ssh = SSHSession(
            host=credential.host,
            port=credential.port,
            username=credential.username,
            password=credential.password,
        )

        try:
            ssh.connect()

            for cmd in profile.disable_paging:
                ssh.send(cmd)
                ssh.recv_until(profile.prompts)

            full_config = ""

            for cmd in profile.fetch_commands:
                ssh.send(cmd)
                output = ssh.recv_until(profile.prompts)
                full_config += output

        finally:
            ssh.close()

        cleaned = self._cleanup(full_config, profile)
        if not cleaned.strip():
            raise RuntimeError("Empty config received from device")

        return cleaned

    def _cleanup(self, text: str, profile: DeviceProfile) -> str:
        lines = []
        for line in text.splitlines():
            if any(line.strip().endswith(p) for p in profile.prompts):
                continue
            if line.strip() in profile.disable_paging:
                continue
            lines.append(line)
        return "\n".join(lines).strip()