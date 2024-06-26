from libprobe.probe import Probe
from lib.check.device import check_device
from lib.check.event import check_event
from lib.check.health import check_health
from lib.version import __version__ as version


if __name__ == '__main__':
    checks = {
        'device': check_device,
        'event': check_event,
        'health': check_health,
    }

    probe = Probe('unifisite', version, checks)
    probe.start()
