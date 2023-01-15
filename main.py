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
        elif 'open' in main_evt:   # Open serial port
            log_printer.start_reading_log()
        elif 'close' in main_evt:  # Close serial port
            log_printer.stop_reading_log()
        elif 'refresh' in main_evt:
            log_printer.refresh_serial_ports()
        elif 'Clear' in main_evt:  # Clear log window
            log_printer.clear_console()
        elif 'Copy' in main_evt:   # Copy log window
            log_printer.copy_console()
        elif main_evt == 'port':   # Select serial port
            log_printer.port = main_vals['port']
        elif main_evt == 'baudrate':   # Set serial baudrate
            log_printer.baudrate = main_vals['baudrate']
        elif main_evt == 'level':  # Change verbosity level
            log_printer.set_verbosity_level(main_vals['level'])
        elif main_evt == 'log_src':    # Set log file path
            log_printer.log_src = main_vals['log_src']
        elif 'autoscroll' in main_evt:  # Change autoscroll enable or not
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

        # Print telemetry
        if len(log_printer.latest_telems) > 0:
            log_printer.print_log(*log_printer.latest_telems[0])
            log_printer.save_log(*log_printer.latest_telems[0])
            log_printer.latest_telems.pop(0)

        # Configuration
        if config_window:
            config_evt, config_vals = config_window.window.read(timeout=1)
            if config_evt == sg.WIN_CLOSED or config_evt == 'Exit':
                config_window.window.close()
                config_window = None
            elif config_evt == 'ok':
                consol_font_size = config_vals['console_font_size']
                log_printer.configure_console(config_vals['console_font_size'], config_vals['tab_len'])
                config_window.window.close()
                config_window = None

        # if cnt < max_cnt + 1:
        #     log_printer.print_processing_bar("INFO", None, "Test", cnt, max_cnt)
        #     cnt += 1
        # elif cnt == max_cnt + 1:
        #     log_printer.print_log("ERROR", None, ["Test"])
        #     log_printer.print_log("INFO", None, ["Test"])
        #     log_printer.print_log("DEBUG", None, ["Test"])
        #     cnt += 1
        # elif cnt > max_cnt + 1:
        #     cnt = 0
