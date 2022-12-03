import re
import serial


class ConsoleColorPrinter():
    def __init__(self):
        self.COLOR_DEBUG = '\033[37m'   # white
        self.COLOR_INFO = '\033[32m'    # green
        self.COLOR_WARN = '\033[33m'    # yellow
        self.COLOR_ERROR = '\033[31m'   # red
        self.COLOR_FATAL = '\033[31m\033[47m'   # red and white(background)

    def level(self, level):
        if level == 'DEBUG':
            return self.COLOR_DEBUG
        elif level == 'INFO':
            return self.COLOR_INFO
        elif level == 'WARN':
            return self.COLOR_WARN
        elif level == 'ERROR':
            return self.COLOR_ERROR
        elif level == 'FATAL':
            return self.COLOR_FATAL
        else:
            return self.reset

    @property
    def bold(self):
        return '\033[1m'

    @property
    def reset(self):
        return '\033[0m'


if __name__ == "__main__":
    pattern_tm = re.compile(r"(DEBUG.|INFO.|WARN.|ERROR.|FATAL.)(.*)\n")
    ccp = ConsoleColorPrinter()

    log_src = "log.txt"

    try:
        ser = serial.Serial("COM3", 9600)
    except serial.serialutil.SerialException:
        assert False, "Could not open serial port"

    while True:
        byte_data = ser.read_until(b'\n')
        str_data = byte_data.decode(errors='ignore')
        re_result = pattern_tm.match(str_data)
        if re_result:
            level = re_result.group(1)[:-1]
            print(f"{ccp.level(level)}{re_result.group(2)}{ccp.reset}")
            with open(log_src, 'a') as f:
                f.write(str_data)
