from twisted.internet.task import LoopingCall

from paradrop.base import settings
from paradrop.lib.utils import pdos
from paradrop.core.config.airshark import airshark_interface_manager
from scanner import Scanner
from spectrum_reader import SpectrumReader
from analyzer import AnalyzerProcessProtocol

class AirsharkManager(object):
    def __init__(self):
        self.loop = LoopingCall(self.check_spectrum)
        self.wifi_interface = None
        self.scanner = None
        self.analyzer_process = AnalyzerProcessProtocol()
        self.observers = []
        airshark_interface_manager.add_observer(self)

    def status(self):
        hardware_ready = False
        software_ready = False
        scanner_running = False
        if self.wifi_interface:
            hardware_ready = True

        if pdos.exists(settings.AIRSHARK_INSTALL_DIR):
            software_ready = True

        if self.scanner:
            scanner_running = True

        return (hardware_ready, software_ready, scanner_running)

    def on_interface_up(self, interface):
        self._stop()
        self.wifi_interface = interface
        self.scanner = Scanner(self.wifi_interface)
        self._start()

    def on_interface_down(self, interface):
        self._stop()
        self.wifi_interface = None
        self.scanner = None

    def _start(self):
        self.scanner.cmd_chanscan()
        self.scanner.start()

        if not self.analyzer_process.isRunning():
            cmd = ["airshark.analyzer", "specfile", "--spectrum-fd=3", "--output-fd=4"]
            self.analyzer_process \
                = reactor.spawnProcess(self,analyzer_protocol,\
                                       cmd[0], cmd, env=None, \
                                       childFDs={0:"w", 1:"r", 2:2, 3:"w", 4:"r"})

        self.loop.start(0.2)
        return True

    def _stop(self):
        if (self.scanner):
            self.scanner.stop()

        if self.analyzer_process.isRunning():
            self.analyzer_process.stop()

        self.loop.stop()

    def check_spectrum(self):
        ts, data = self.scanner.spectrum_reader.read_samples()
        if (data is not None):
            for (tsf, max_exp, freq, rssi, noise, max_mag, max_index, bitmap_weight, sdata) in SpectrumReader.decode(data):
                for observer in self.observers:
                    observer.on_spectrum_data(tsf, max_exp, freq, rssi, noise, max_mag, max_index, bitmap_weight, sdata)

    # TODO: Not sure we need it or not
    def read_raw_samples(self):
        if (self.scanner):
            return self.scanner.spectrum_reader.read_samples()
        else:
            return None, None

    def add_observer(self, observer):
        if (self.observers.count(observer) == 0):
            self.observers.append(observer)

    def remove_observer(self, observer):
        if (self.observers.count(observer) == 1):
            self.observers.remove(observer)
