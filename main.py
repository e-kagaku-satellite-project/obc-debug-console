from __future__ import annotations
import datetime
import re
import serial
import threading
import PySimpleGUI as sg
from serial.tools import list_ports

level_colors = {
    'DEBUG': '#FFFFFF',  # white
    'INFO': '#00FF00',  # Green
    'WARN': '#FFA500',  # Yellow
    'ERROR': '#FF0000',  # Red
    'FATAL': '#FF0000',  # Red
}

level_bg_colors = {
    'DEBUG': '#000000',  # black
    'INFO': '#000000',  # black
    'WARN': '#000000',  # black
    'ERROR': '#000000',  # black
    'FATAL': '#FFFFFF',  # white
}

themes = {'Main CPU': 'Dark', 'Transmit CPU': 'DarkBlue', 'Receive CPU': 'DarkAmber'}
verbosity_levels = {'DEBUG': 0, 'INFO': 1, 'WARN': 2, 'ERROR': 3, 'FATAL': 4, 'NONE': 5}
cpus = ["Main CPU", "Transmit CPU", "Receive CPU"]
baudrates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]


class LogPrinter():
    def __init__(self):
        sg.theme(themes['Main CPU'])
        self.create_window()
        self.pattern_tm = re.compile(r"(DEBUG,|INFO,|WARN,|ERROR,|FATAL,)(.*)\n")

    def __del__(self):
        self.window.close()
        self.serial.close() if self.serial is not None else None

    def change_theme(self, cpu):
        sg.theme(themes[cpu])
        self.window.close()
        self.create_window(cpu)

    def create_window(self, cpu='Main CPU') -> sg.Window:
        ports = list_ports.comports()
        devices = [info.device for info in ports] if len(ports) != 0 else ['']
        self.port = devices[0]
        cpu_cmbbox = sg.Combo(cpus, default_value=cpu, size=(15, 1), key='cpu', font=('Helvetica', 16), enable_events=True, readonly=True)
        port_cmbbox = sg.Combo(devices, default_value=self.port, key='port', size=(20, 1), enable_events=True, readonly=True)
        baudrate_cmbbox = sg.Combo(baudrates, default_value=baudrates[0], key='baudrate', size=(20, 1), enable_events=True, readonly=True)
        level_cmbbox = sg.Combo(list(verbosity_levels.keys()), default_value=list(verbosity_levels.keys())[0], key='level', size=(20, 1), enable_events=True, readonly=True)
        open_btn = sg.Button('Open', key='open')
        close_btn = sg.Button('Close', key='close', disabled=True)
        self.log_src = "log.csv"
        log_src_txt = sg.InputText(key='log_src', default_text=self.log_src, size=(30, 1), font=('Helvetica', 12), enable_events=True)
        console_mtl = sg.Multiline(size=(80, 25), font=('Ubuntu Mono', 12), expand_x=True, expand_y=True, key='console', background_color='#000000', horizontal_scroll=True)
        autoscroll_chkbox = sg.Checkbox('Auto scroll', key='autoscroll', default=True, enable_events=True)
        layouts = [
            [cpu_cmbbox],
            [port_cmbbox, baudrate_cmbbox, level_cmbbox, open_btn, close_btn],
            [log_src_txt],
            [console_mtl],
            [autoscroll_chkbox],
        ]
        self.baudrate = baudrates[0]
        self.verbosity_level = list(verbosity_levels.values())[0]
        self.latest_telems = []  # バッファとして機能するようにリストにした，FIFO形式
        self.autoscroll = True
        self.is_open_serial = False
        self.window = sg.Window('OBC Debugger', layouts, resizable=True)
        sg.cprint_set_output_destination(self.window, 'console')

    def start_reading_log(self):
        self.is_open_serial = True
        self.latest_telems = []
        try:
            self.serial = serial.Serial(self.port, self.baudrate)
            self.window['open'].update(disabled=True)
            self.window['close'].update(disabled=False)
            self.window['port'].update(disabled=True)
            self.window['baudrate'].update(disabled=True)
            self.window['log_src'].update(disabled=True)
            self.read_telem_thread = threading.Thread(target=self.read_telemetry, daemon=True)
            self.read_telem_thread.start()
        except serial.serialutil.SerialException:
            self.serial = None
            sg.popup('Failed to open serial port', title='Error', keep_on_top=True)
            self.stop_reading_log()

    def stop_reading_log(self):
        self.serial.close() if self.serial is not None else None
        self.window['open'].update(disabled=False)
        self.window['close'].update(disabled=True)
        self.window['port'].update(disabled=False)
        self.window['baudrate'].update(disabled=False)
        self.window['log_src'].update(disabled=False)
        self.is_open_serial = False

    def read_telemetry(self):
        while self.is_open_serial:
            try:    # 見えぬバグ ifで消した 午前2時
                byte_data = self.serial.readline()
            except:   # serial port closed
                break
            str_data = byte_data.decode(errors='ignore')
            re_result = self.pattern_tm.match(str_data)
            if re_result:
                level = re_result.group(1)[:-1]
                if verbosity_levels[level] >= self.verbosity_level:
                    dt_now = datetime.datetime.now()
                    self.latest_telems.append([level, dt_now, [f"{s}" for s in re_result.group(2).split(",") if s]])

    def save_log(self, level: str, dt_now: str, line_data: list[str]):
        with open(self.log_src, 'a') as f:
            f.write(f"{dt_now},{level},{','.join(line_data)}\n")

    def print_log(self, level: str, dt_now: str, line_data: list[str]):
        echo_str = f"[{dt_now}] {level}\t" + "\t".join(line_data)
        echo_str = self.alignTabString(echo_str)
        sg.cprint(f"{echo_str}", autoscroll=self.autoscroll, end='\n', text_color=level_colors[level], background_color=level_bg_colors[level])

    def alignTabString(self, text: str):
        tab_idxes = re.finditer('\t', text)
        num_appended = 0
        TAB_SIZE = 6
        for i, idx in enumerate(tab_idxes):
            text = text[:idx.start() + num_appended] + ' ' * (TAB_SIZE - ((idx.start() + num_appended) % TAB_SIZE)) + text[idx.start() + num_appended + 1:]
            num_appended += TAB_SIZE - (idx.start() % TAB_SIZE) - 1
        return text


if __name__ == "__main__":
    log_printer = LogPrinter()
    while True:
        event, values = log_printer.window.read(timeout=1)
        if event == sg.WIN_CLOSED:
            break
        elif event == 'open':
            log_printer.start_reading_log()
        elif event == 'close':
            log_printer.stop_reading_log()
        elif event == 'port':
            log_printer.port = values['port']
        elif event == 'baudrate':
            log_printer.baudrate = values['baudrate']
        elif event == 'level':
            log_printer.verbosity_level = verbosity_levels[values['level']]
        elif event == 'log_src':
            log_printer.log_src = values['log_src']
        elif event == 'autoscroll':
            log_printer.autoscroll = values['autoscroll']
        elif event == 'cpu':
            log_printer.change_theme(values['cpu'])

        if len(log_printer.latest_telems) > 0:
            log_printer.print_log(*log_printer.latest_telems[0])
            log_printer.save_log(*log_printer.latest_telems[0])
            log_printer.latest_telems.pop(0)
