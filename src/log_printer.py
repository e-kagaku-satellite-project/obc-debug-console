
from __future__ import annotations
import datetime
import json
import os
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

font_style_window = 'Helvetica'
font_style_console = 'Ubuntu Mono'
themes = {'Main CPU': 'Dark', 'Transmit CPU': 'DarkBlue', 'Receive CPU': 'DarkAmber'}
verbosity_levels = {'DEBUG': 0, 'INFO': 1, 'WARN': 2, 'ERROR': 3, 'FATAL': 4, 'NONE': 5}
cpus = ["Main CPU", "Transmit CPU", "Receive CPU"]
cpu_log_src = {"Main CPU": "log_main_cpu.csv", "Transmit CPU": "log_trans_cpu.csv", "Receive CPU": "log_rcv_cpu.csv"}
baudrates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]


def listup_serial_ports():
    devices = list_ports.comports()
    ports = [info.device for info in devices] if len(devices) != 0 else ['']
    return ports


class ConfigWindow():
    def __init__(self, log_printer: LogPrinter):
        self.layout = [
            [sg.Text('Tab length'), sg.InputText(key='tab_len', default_text=f'{log_printer.tab_len}', size=(5, 1), font=(font_style_window, 12), enable_events=True)],
            [sg.Text('Font size')],
            [sg.Text('    Console'), sg.InputText(key='console_font_size', default_text=f'{log_printer.console_font_size}', size=(5, 1), font=(font_style_window, 12), enable_events=True)],
            [sg.Button('OK', key='ok'), sg.Button('Cancel', key='cancel')]
        ]
        self.window = sg.Window('Configlation', self.layout, resizable=True)


class LogPrinter():
    def __init__(self):
        self.cpu = 'Main CPU'
        sg.theme(themes[self.cpu])
        self.create_config_file()
        config = self.load_config()
        self.create_window(config)
        self.pattern_tm = re.compile(r"(DEBUG,|INFO,|WARN,|ERROR,|FATAL,)(.*)\n")

    def __del__(self):
        self.window.close()
        self.serial.close() if self.serial is not None else None

    def change_theme(self, cpu):
        self.cpu = cpu
        sg.theme(themes[self.cpu])
        self.window.close()
        config = self.load_config()
        self.create_window(config)

    def create_config_file(self):
        if not os.path.isfile("./config/config.json"):
            os.makedirs("./config", exist_ok=True)
            config = {
                "Main CPU": {
                    "port": "",
                    "baudrate": 9600,
                },
                "Transmit CPU": {
                    "port": "",
                    "baudrate": 9600,
                },
                "Receive CPU": {
                    "port": "",
                    "baudrate": 9600,
                },
                "tab_len": 6,
                "console_font_size": 12
            }
            with open("./config/config.json", "w") as f:
                json.dump(config, f, indent=4)

    def load_config(self):
        with open('./config/config.json', 'r') as f:
            config = json.load(f)
        self.tab_len = config['tab_len']
        self.console_font_size = config['console_font_size']
        return config

    def update_config(self, *args, **kwargs):
        config = self.load_config()
        for key, value in kwargs.items():
            config[key] = value
        with open('./config/config.json', 'w') as f:
            json.dump(config, f, indent=4)

    def create_window(self, config: dict) -> sg.Window:
        ports = listup_serial_ports()
        self.port = config[self.cpu]['port'] if config[self.cpu]['port'] in ports else ports[0]

        menubar = sg.MenuBar([['File', ['Configure', 'Exit']]])
        cpu_cmbbox = sg.Combo(cpus, default_value=self.cpu, size=(15, 1), key='cpu', font=(font_style_window, 16), enable_events=True, readonly=True)
        port_cmbbox = sg.Combo(ports, default_value=self.port, key='port', size=(20, 1), enable_events=True, readonly=True)
        baudrate_cmbbox = sg.Combo(baudrates, default_value=baudrates[0], key='baudrate', size=(20, 1), enable_events=True, readonly=True)
        level_cmbbox = sg.Combo(list(verbosity_levels.keys()), default_value=list(verbosity_levels.keys())[0], key='level', size=(20, 1), enable_events=True, readonly=True)
        open_btn = sg.Button('Open', key='open')
        close_btn = sg.Button('Close', key='close', disabled=True)
        refresh_btn = sg.Button('Refresh', key='refresh', enable_events=True)
        self.log_src = cpu_log_src[self.cpu]
        log_src_txt = sg.InputText(key='log_src', default_text=self.log_src, size=(30, 1), font=(font_style_window, 12), enable_events=True)
        console_mtl = sg.Multiline(size=(80, 25), font=(font_style_console, self.console_font_size), expand_x=True, expand_y=True, key='console', background_color='#000000', horizontal_scroll=True)
        autoscroll_chkbox = sg.Checkbox('Auto scroll', key='autoscroll', default=True, enable_events=True)
        layouts = [
            [menubar],
            [cpu_cmbbox, log_src_txt, autoscroll_chkbox],
            [port_cmbbox, baudrate_cmbbox, level_cmbbox, open_btn, close_btn, refresh_btn],
            [console_mtl],
            # [sg.Image(r'./img/background.png')]
        ]
        self.baudrate = baudrates[0]
        self.verbosity_level = list(verbosity_levels.values())[0]
        self.latest_telems = []  # バッファとして機能するようにリストにした，FIFO形式
        self.autoscroll = True
        self.is_open_serial = False
        self.window = sg.Window('OBC Debugger', layouts, resizable=True, use_default_focus=False, finalize=True)

        # Shortcut-keys
        self.window.bind('<Control-a>', 'autoscroll_key')
        self.window.bind("<Control-o>", "open_key")  # Open serial port
        self.window.bind("<Control-c>", "close_key")  # Close serial port
        self.window.bind("<Control-r>", "refresh_key")  # Refresh serial port
        self.window.bind("<Control-z>", "Exit")  # Exit
        sg.cprint_set_output_destination(self.window, 'console')

    def refresh_serial_ports(self):
        ports = listup_serial_ports()
        config = self.load_config()
        self.port = config[self.cpu]['port'] if config[self.cpu]['port'] in ports else ports[0]
        self.window['port'].update(values=ports, value=self.port)

    def start_reading_log(self):
        self.is_open_serial = True
        self.latest_telems = []
        self.update_config(**{self.cpu: {'port': self.port, 'baudrate': self.baudrate}})
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
        # echo_str = f"[{dt_now}] {level}\t" + "\t".join(line_data)
        echo_str = "\t".join(line_data)
        echo_str = self.alignTabString(echo_str)
        sg.cprint(f"{echo_str}", autoscroll=self.autoscroll, end='\n', text_color=level_colors[level], background_color=level_bg_colors[level])

    def set_verbosity_level(self, level: str):
        self.verbosity_level = verbosity_levels[level]

    def configure_console(self, font_size, tab_len):
        try:
            self.console_font_size = int(font_size)
            self.window['console'].update(font=(font_style_console, self.console_font_size))
        except:
            pass
        try:
            self.tab_len = int(tab_len)
        except:
            pass

    def alignTabString(self, text: str):
        strs_between_tabs = re.split('\t', text)
        final_strs = ""
        for i, s in enumerate(strs_between_tabs):
            final_strs += s + ' ' * (self.tab_len - len(s) % self.tab_len)
            final_strs += '    'if len(s) % self.tab_len == 0 else ''
        return final_strs
