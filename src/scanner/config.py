import os


class ScannerConfig:
    def __init__(self) -> None:
        self.scan_interval_seconds = int(os.getenv("SCAN_INTERVAL_SECONDS", "60"))
        self.signal_cooldown_seconds = int(os.getenv("SIGNAL_COOLDOWN_SECONDS", "14400"))
