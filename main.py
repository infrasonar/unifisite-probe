from libprobe.probe import Probe
from lib.check.device import CheckDevice
from lib.check.event import CheckEvent
from lib.check.health import CheckHealth
from lib.version import __version__ as version


if __name__ == '__main__':
    checks = (
        CheckDevice,
        CheckEvent,
        CheckHealth,
    )

    probe = Probe('unifisite', version, checks)
    probe.start()
