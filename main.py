from __future__ import annotations
import PySimpleGUI as sg
from src.log_printer import ConfigWindow, LogPrinter

if __name__ == "__main__":
    log_printer = LogPrinter()
    config_window = None
    cnt = 0
    max_cnt = 100
    while True:
        main_evt, main_vals = log_printer.window.read(timeout=1)

        # if main_evt != "__TIMEOUT__":
        #     print(main_evt)
        if main_evt == sg.WIN_CLOSED or main_evt == 'Exit':
            break
        elif 'open' == main_evt or 'open_key' == main_evt:   # Open serial port
            log_printer.start_reading_log()
        elif 'close' == main_evt or 'close_key' == main_evt:  # Close serial port
            log_printer.stop_reading_log()
        elif 'refresh' == main_evt or 'refresh_key' == main_evt:
            log_printer.refresh_serial_ports()
        elif 'Clear' == main_evt:  # Clear log window
            log_printer.clear_console()
        elif 'Copy' == main_evt:   # Copy log window
            log_printer.copy_console()
        elif main_evt == 'port':   # Select serial port
            log_printer.port = main_vals['port']
        elif main_evt == 'baudrate':   # Set serial baudrate
            log_printer.baudrate = main_vals['baudrate']
        elif main_evt == 'level':  # Change verbosity level
            log_printer.set_verbosity_level(main_vals['level'])
        elif main_evt == 'log_src':    # Set log file path
            log_printer.log_src = main_vals['log_src']
        elif 'autoscroll' == main_evt or 'autoscroll_key' == main_evt:  # Change autoscroll enable or not
            if main_evt == 'autoscroll_key':
                log_printer.window['autoscroll'].update(not main_vals['autoscroll'])
                log_printer.autoscroll = not main_vals['autoscroll']
            else:
                log_printer.autoscroll = main_vals['autoscroll']
        elif main_evt == 'cpu':    # Select CPU (Change theme)
            log_printer.change_theme(main_vals['cpu'])
        elif main_evt == 'select-Main' or main_evt == 'select-Transmit' or main_evt == 'select-Receive':
            log_printer.change_theme(f"{main_evt[7:]} CPU")
        elif main_evt == 'Configure':  # Open configuration window
            config_window = ConfigWindow(log_printer)
        elif main_evt == 'up-verbosity-level' or main_evt == 'down-verbosity-level':
            log_printer.change_verbosity_level(main_evt)
        elif main_evt == 'open-new-console':
            log_printer.open_new_console()

        # Print telemetry
        if len(log_printer.latest_telems) > 0:
            log_printer.print_log(*log_printer.latest_telems[0])
            log_printer.save_log(*log_printer.latest_telems[0])
            log_printer.latest_telems.pop(0)

        # Configuration
        if config_window:
            config_evt, config_vals = config_window.window.read(timeout=1)
            if config_evt == sg.WIN_CLOSED or config_evt == 'Exit' or config_evt == 'cancel':
                config_window.window.close()
                config_window = None
            elif config_evt == 'ok':
                log_printer.configure_console(config_vals['console_font_size'], config_vals['tab_len'], config_vals['max_console_lines'])
                config_window.window.close()
                config_window = None

        # if cnt < max_cnt + 1:
        #     log_printer.latest_telems.append(["INFO", None, ["TQDM", "Test", "MSG", f"{cnt}", f"{max_cnt}"]])
        #     cnt += 1
        #     time.sleep(0.01)
        # elif cnt == max_cnt + 1:
        #     log_printer.latest_telems.append(["FATAL", None, ["TEST"]])
        #     log_printer.latest_telems.append(["ERROR", None, ["TEST"]])
        #     log_printer.latest_telems.append(["WARN", None, ["TEST"]])
        #     log_printer.latest_telems.append(["INFO", None, ["TEST"]])
        #     log_printer.latest_telems.append(["DEBUG", None, ["TEST"]])
        #     cnt = 0
        # elif cnt > max_cnt + 2:
        #     cnt = 0
