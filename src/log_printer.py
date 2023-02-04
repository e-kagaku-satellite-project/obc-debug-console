#!/usr/bin/env python3
# coding:utf-8

from __future__ import annotations
import base64
import datetime
import json
import logging
import os
import re
import serial
import subprocess
import threading
import PySimpleGUI as sg
from serial.tools import list_ports

os.makedirs('./log', exist_ok=True)
logging.basicConfig(filename='./log/odc_system.log', level=logging.DEBUG)

level_colors = {
    'DEBUG': '#FFFFFF',  # white
    'INFO': '#00FF00',  # Green
    'WARN': '#FFE000',  # Orange(Yellow)
    'ERROR': '#FF0000',  # Red
    'FATAL': '#FF0000',  # Red
}

level_bg_colors = {
    'DEBUG': None,  # black
    'INFO': None,  # black
    'WARN': None,  # black
    'ERROR': None,  # black
    'FATAL': '#FFFF00',  # Yellow
}

font_style_window = 'Helvetica'
font_style_console = 'Ubuntu Mono'
font_style_popup = 'Helvetica'
themes = {'Main CPU': 'Dark', 'Transmit CPU': 'DarkBlue', 'Receive CPU': 'DarkAmber'}
verbosity_levels = {'DEBUG': 0, 'INFO': 1, 'WARN': 2, 'ERROR': 3, 'FATAL': 4, 'NONE': 5}
cpus = ["Main CPU", "Transmit CPU", "Receive CPU"]
cpu_log_src = {"Main CPU": "log_main_cpu.csv", "Transmit CPU": "log_trans_cpu.csv", "Receive CPU": "log_rcv_cpu.csv"}
baudrates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

default_config = {
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
    "console_font_size": 12,
    "max_console_lines": 10000,
}

ICON_IMG_SRC = "img/icon.png"


def listup_serial_ports():
    devices = list_ports.comports()
    ports = [info.device for info in devices] if len(devices) != 0 else ['']
    return ports


def img_to_base64(img_src):
    with open(img_src, "rb") as f:
        img = f.read()
    return base64.b64encode(img)


class ConfigWindow():
    def __init__(self, log_printer: LogPrinter):
        col = [
            [sg.Text('Tab length'), sg.InputText(key='tab_len', default_text=f'{log_printer.tab_len}', size=(5, 1), font=(font_style_window, 12), enable_events=True)],
            [sg.Text('Font size')],
            [sg.Text('    Console'), sg.InputText(key='console_font_size', default_text=f'{log_printer.console_font_size}', size=(5, 1), font=(font_style_window, 12), enable_events=True)],
            [sg.Text('Scrollback'), sg.InputText(key='max_console_lines', default_text=f'{log_printer.max_console_lines}', size=(8, 1), font=(font_style_window, 12), enable_events=True), sg.Text('lines')],
        ]
        self.layout = [
            [sg.Column(col)],
            [sg.Column([[sg.Button('OK', key='ok'), sg.Button('Cancel', key='cancel')]], justification='c')],
        ]
        self.window = sg.Window('Configuration', self.layout, resizable=True, finalize=True, icon=img_to_base64(ICON_IMG_SRC))
        self.window.bind('<Escape>', 'cancel')


class LogPrinter():
    def __init__(self):
        self.cpu = 'Main CPU'
        self.serial = None
        self.is_prev_tqdm = False
        self.pattern_tm = re.compile(r"(DEBUG,|INFO,|WARN,|ERROR,|FATAL,)(.*)\n")
        sg.theme(themes[self.cpu])
        self.create_config_file()
        config = self.load_config()
        self.create_window(config)

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
            with open("./config/config.json", "w") as f:
                json.dump(default_config, f, indent=4)

    def load_config(self):
        with open('./config/config.json', 'r') as f:
            config = json.load(f)
        if 'tab_len' in config:
            self.tab_len = config['tab_len']
        else:
            self.tab_len = default_config['tab_len']
        if 'console_font_size' in config:
            self.console_font_size = config['console_font_size']
        else:
            self.console_font_size = default_config['console_font_size']
        if 'max_console_lines' in config:
            self.max_console_lines = config['max_console_lines']
        else:
            self.max_console_lines = default_config['max_console_lines']
        self.baudrate = config[self.cpu]['baudrate']
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
        self.log_src = cpu_log_src[self.cpu]
        self.verbosity_level = list(verbosity_levels.values())[0]
        self.latest_telems = []  # バッファとして機能するようにリストにした，FIFO形式
        self.autoscroll = True
        self.is_serial_opened = False

        self.window = sg.Window(
            'OBC Debugger',
            self.layouts(ports),
            icon=img_to_base64(ICON_IMG_SRC),
            resizable=True,
            use_default_focus=False,
            finalize=True
        )
        self.window.force_focus()
        self.window['console'].update(disabled=True)
        self.bind_shortcutkeys()
        sg.cprint_set_output_destination(self.window, 'console')

    def layouts(self, ports):
        menubar = sg.MenuBar([['File', ['Configure', 'Exit']], ['Console', ['Clear', 'Copy']]])
        cpu_cmbbox = sg.Combo(cpus, default_value=self.cpu, size=(15, 1), key='cpu', font=(font_style_window, 16), enable_events=True, readonly=True)
        port_cmbbox = sg.Combo(ports, default_value=self.port, key='port', size=(20, 1), enable_events=True, readonly=True)
        baudrate_cmbbox = sg.Combo(baudrates, default_value=baudrates[0], key='baudrate', size=(20, 1), enable_events=True, readonly=True)
        level_cmbbox = sg.Combo(list(verbosity_levels.keys()), default_value=list(verbosity_levels.keys())[0], key='level', size=(20, 1), enable_events=True, readonly=True)
        open_btn = sg.Button('Open', key='open')
        close_btn = sg.Button('Close', key='close', disabled=True)
        refresh_btn = sg.Button('Refresh', key='refresh', enable_events=True)
        log_src_txt = sg.InputText(key='log_src', default_text=self.log_src, size=(30, 1), font=(font_style_window, 12), enable_events=True)
        console_mtl = sg.Multiline(size=(80, 25), font=(font_style_console, self.console_font_size), expand_x=True, expand_y=True, key='console', background_color='#000000', horizontal_scroll=True)
        autoscroll_chkbox = sg.Checkbox('Auto scroll', key='autoscroll', default=True, enable_events=True)
        layouts = [
            [menubar],
            [cpu_cmbbox, log_src_txt, autoscroll_chkbox],
            [port_cmbbox, baudrate_cmbbox, level_cmbbox, open_btn, close_btn, refresh_btn],
            [console_mtl]
        ]
        return layouts

    def bind_shortcutkeys(self):
        self.window.bind('<Shift-A>', 'autoscroll_key')        # Alt-a
        self.window.bind("<Shift-O>", "open_key")  # Open serial port      # Alt-o
        self.window.bind("<Shift-C>", "close_key")  # Close serial port        # Alt-c
        self.window.bind("<Shift-R>", "refresh_key")  # Refresh serial port        # Alt-r
        self.window.bind("<Shift-E>", "Exit")  # Exit      # Alt-e
        self.window.bind("<Shift-Up>", 'up-verbosity-level')        # Alt-Up
        self.window.bind("<Shift-Down>", 'down-verbosity-level')      # Alt-Down
        self.window.bind("<Control-t>", "select-Transmit")       # Alt-t
        self.window.bind("<Control-m>", "select-Main")       # Alt-m
        self.window.bind("<Control-r>", "select-Receive")        # Alt-r
        self.window.bind("<Control-n>", "open-new-console")

    def refresh_serial_ports(self):
        ports = listup_serial_ports()
        config = self.load_config()
        self.port = config[self.cpu]['port'] if config[self.cpu]['port'] in ports else ports[0]
        self.window['port'].update(values=ports, value=self.port)

    def start_reading_log(self):
        if self.is_serial_opened:
            return
        self.is_serial_opened = True
        self.latest_telems = []
        try:
            self.serial = serial.Serial(self.port, self.baudrate)
            self.update_config(**{self.cpu: {'port': self.port, 'baudrate': self.baudrate}})
            self.window['open'].update(disabled=True)
            self.window['close'].update(disabled=False)
            self.window['port'].update(disabled=True)
            self.window['baudrate'].update(disabled=True)
            self.window['log_src'].update(disabled=True)
            self.window['cpu'].update(disabled=True)
            self.log_src = self.window['log_src'].get()
            self.read_telem_thread = threading.Thread(target=self.read_telemetry, daemon=True)
            self.read_telem_thread.start()
        except serial.serialutil.SerialException as e:
            self.serial = None
            sg.popup(f'{e}', title='Failed to open serial port', keep_on_top=True, font=(font_style_popup, 12))
            logging.error(f'{datetime.datetime.now()}:{self.cpu}:{e}')
            self.stop_reading_log()

    def stop_reading_log(self):
        self.serial.close() if self.serial is not None else None
        self.window['open'].update(disabled=False)
        self.window['close'].update(disabled=True)
        self.window['port'].update(disabled=False)
        self.window['baudrate'].update(disabled=False)
        self.window['log_src'].update(disabled=False)
        self.window['cpu'].update(disabled=False)
        self.is_serial_opened = False

    def read_telemetry(self):
        while self.is_serial_opened:
            try:    # 見えぬバグ ifで消した 午前2時
                byte_data = self.serial.readline()
            except serial.SerialException:  # "ReadFile failed (OSError(9, 'ハンドルが無効です。', None, 6))" will be raised when closing the serial port
                pass
            except AttributeError:  # "'NoneType' object has no attribute 'hEvent'" will be raised when closing the serial port
                pass
            except TypeError:   # "byref() argument must be a ctypes instance, not 'NoneType'" will be raised when closing the serial port
                pass
            except Exception as e:
                logging.error(f'{datetime.datetime.now()}:read_telemetry:{self.cpu}:{e}')
            str_data = byte_data.decode(errors='ignore')
            re_result = self.pattern_tm.match(str_data)
            if re_result:
                level = re_result.group(1)[:-1]
                if verbosity_levels[level] >= self.verbosity_level:
                    dt_now = datetime.datetime.now()
                    self.latest_telems.append([level, dt_now, [f"{s}" for s in re_result.group(2).split(",") if s]])

    def clear_console(self):
        self.window['console'].update(value='')

    def copy_console(self):
        self.window['console'].Widget.clipboard_clear()
        self.window['console'].Widget.clipboard_append(self.window['console'].get())

    def save_log(self, level: str, dt_now: str, line_data: list[str]):
        try:
            with open(self.log_src, 'a') as f:
                f.write(f"{dt_now},{level},{','.join(line_data)}\n")
        except Exception as e:
            logging.error(f'{datetime.datetime.now()}:save_log:{self.cpu}:{e}')

    def print_log(self, level: str, dt_now: str, line_data: list[str]):
        # echo_str = f"[{dt_now}] {level}\t" + "\t".join(line_data)
        line_data = [l.replace('\x00', '') for l in line_data]
        if len(line_data) > 3 and line_data[0] == "TQDM":
            if "MSG" in line_data:
                msg_idx = line_data.index("MSG")
            else:
                logging.warn(f'{datetime.datetime.now()}:{self.cpu}:MSG is not in line_data,{line_data}')
                return
            try:
                self.print_processing_bar(level, dt_now, line_data[1:msg_idx], int(line_data[msg_idx + 1]), int(line_data[msg_idx + 2]))
            except:
                logging.error(f'{datetime.datetime.now()}:print_log:{self.cpu}:{line_data}')
                return
            self.is_prev_tqdm = True
        else:
            echo_str = "\t".join(line_data)
            echo_str = self.align_tab_string(echo_str)
            self.is_prev_tqdm = False
            sg.cprint(f"{echo_str}", autoscroll=self.autoscroll, end='\n', text_color=level_colors[level], background_color=level_bg_colors[level])

        # If the number of lines is over self.max_console_lines, delete the first line
        over_line_num = float(self.window['console'].Widget.index('end-1c').split('.')[0]) - self.max_console_lines
        if over_line_num > 0:
            self.window['console'].update(disabled=False)
            self.window['console'].Widget.delete(1.0, over_line_num + 1)
            self.window['console'].update(disabled=True)
        self.window['console'].Widget.tag_raise("sel")

    def print_processing_bar(self, level: str, dt_now: str, msg: str, step: int, max_step: int):
        echo_str = "\t".join(msg)
        if max_step == 0:
            logging.warn(f'{datetime.datetime.now()}:{self.cpu}:max_step is 0:{level}:{msg}:{step}:{max_step}')
            return
        echo_str += f"\t[{step:4d} / {max_step:4d}]\t"
        echo_str += "#" * int(step / max_step * 30) + " " * (30 - int(step / max_step * 30)) + "|"
        echo_str = self.align_tab_string(echo_str)
        if self.is_prev_tqdm:
            # 直前1行を削除する
            line_num = float(self.window['console'].Widget.index('end-1c').split('.')[0])
            self.window['console'].update(disabled=False)
            self.window['console'].Widget.delete(line_num - 1, line_num)
            self.window['console'].update(disabled=True)
        sg.cprint(f"{echo_str}", autoscroll=self.autoscroll, end='\n', text_color=level_colors[level], background_color=level_bg_colors[level])

    def set_verbosity_level(self, level: str):
        self.verbosity_level = verbosity_levels[level]

    def change_verbosity_level(self, event_name: str):
        if event_name == "up-verbosity-level":
            self.verbosity_level += 1
            if self.verbosity_level == len(verbosity_levels):
                self.verbosity_level = 0
        elif event_name == "down-verbosity-level":
            self.verbosity_level -= 1
            if self.verbosity_level < 0:
                self.verbosity_level = len(verbosity_levels) - 1
        key = [k for k, v in verbosity_levels.items() if v == self.verbosity_level][0]
        self.window['level'].update(value=key)

    def open_new_console(self):
        subprocess.Popen('./obc-debug-console.exe')

    def configure_console(self, font_size: str, tab_len: str, max_console_lines: str):
        if font_size.isdecimal():
            self.console_font_size = int(font_size)
            self.window['console'].update(font=(font_style_console, self.console_font_size))
        if tab_len.isdecimal():
            self.tab_len = int(tab_len)
        if max_console_lines.isdecimal():
            self.max_console_lines = int(max_console_lines)
        self.update_config(tab_len=self.tab_len, max_console_lines=self.max_console_lines, console_font_size=self.console_font_size)
        self.load_config()

    def align_tab_string(self, text: str):
        strs_between_tabs = re.split('\t', text)
        final_strs = ""
        for s in strs_between_tabs:
            final_strs += s + ' ' * (self.tab_len - len(s) % self.tab_len)
            final_strs += '    'if len(s) % self.tab_len == 0 else ''
        return final_strs
