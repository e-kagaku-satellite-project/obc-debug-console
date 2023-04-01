import PySimpleGUI as sg
from src.log_printer import ConfigWindow, LogPrinter, FindWindow, listup_serial_ports

if __name__ == "__main__":
    log_printer = LogPrinter()
    config_window = None
    find_window = None
    cnt = 0
    max_cnt = 100

    while True:
        main_evt, main_vals = log_printer.window.read(timeout=1)

        # if main_evt != "__TIMEOUT__":
        #     print(main_evt)
        if main_evt == sg.WIN_CLOSED or main_evt == 'Exit':
            break
        elif 'open_close' == main_evt or 'open_close_key' == main_evt:   # Open serial port
            if log_printer.is_serial_opened:
                log_printer.stop_reading_log()
            else:
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
            ports = listup_serial_ports()
            log_printer.port = list(ports.keys())[list(ports.values()).index(main_vals['port'])]
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
        elif main_evt == 'find':
            find_window = FindWindow()
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

        if find_window:
            find_evt, find_vals = find_window.window.read(timeout=1)
            if find_evt == '__TIMEOUT__':
                continue
            if find_evt == sg.WIN_CLOSED or find_evt == 'Exit' or find_evt == 'cancel' or find_evt is None:
                if find_window.highlight_idx > 0 and len(find_window.found_txt_idxes) > find_window.highlight_idx:
                    c, r = find_window.found_txt_idxes[find_window.highlight_idx]
                    log_printer.remove_tag_from_console(f"{c+1}.{r}", f"{c+1}.{r+len(find_window.serach_txt)}", 'HIGHLIGHT')

                for c, r in find_window.found_txt_idxes:
                    log_printer.remove_tag_from_console(f"{c+1}.{r}", f"{c+1}.{r+len(find_window.serach_txt)}", 'CANDIDATE')

                find_window.window.close()
                find_window = None
            elif find_evt == 'previous' or find_evt == 'next' or find_evt == 'Find_Enter':
                if find_evt == 'Find_Enter':
                    find_evt = find_window.last_pressed_btn
                find_window.last_pressed_btn = find_evt
                if len(find_vals['Find']) == 0:
                    sg.popup('Please enter text to find', title='Warning', keep_on_top=True)
                    continue

                if find_window.highlight_idx >= 0 and len(find_window.found_txt_idxes) > find_window.highlight_idx:
                    c, r = find_window.found_txt_idxes[find_window.highlight_idx]
                    log_printer.remove_tag_from_console(f"{c+1}.{r}", f"{c+1}.{r+len(find_window.serach_txt)}", 'HIGHLIGHT')

                # Remove highlight tag from previous search result
                if find_window.serach_txt != find_vals['Find']:
                    for c, r in find_window.found_txt_idxes:
                        log_printer.remove_tag_from_console(f"{c+1}.{r}", f"{c+1}.{r+len(find_window.serach_txt)}", 'CANDIDATE')
                        find_window.found_txt_idxes = []
                    if find_evt == 'previous':
                        find_window.highlight_idx = 1e100
                    else:
                        find_window.highlight_idx = -1

                # Find text
                find_window.serach_txt = find_vals['Find']
                txts = log_printer.window['console'].get().splitlines()
                find_window.found_txt_idxes = []
                max_x_len = 0
                for i, txt in enumerate(txts):
                    idx = txt.find(find_window.serach_txt)
                    if idx != -1:
                        find_window.found_txt_idxes.append((i, idx))
                    max_x_len = max(max_x_len, len(txt))
                if find_evt == 'next':
                    find_window.highlight_idx += 1
                elif find_evt == 'previous':
                    find_window.highlight_idx -= 1
                if find_window.highlight_idx >= len(find_window.found_txt_idxes):
                    find_window.highlight_idx = 0
                elif find_window.highlight_idx < 0:
                    find_window.highlight_idx = len(find_window.found_txt_idxes) - 1

                if len(find_window.found_txt_idxes) == 0:
                    sg.popup('No text found', title='Warning', keep_on_top=True)
                    find_window.window['count'].update("")
                    continue

                find_window.window['count'].update(f"{find_window.highlight_idx+1}/{len(find_window.found_txt_idxes)}")

                for c, r in find_window.found_txt_idxes:
                    log_printer.add_tag_to_console(f"{c+1}.{r}", f"{c+1}.{r+len(find_window.serach_txt)}", 'CANDIDATE')

                c, r = find_window.found_txt_idxes[find_window.highlight_idx]
                log_printer.add_tag_to_console(f"{c+1}.{r}", f"{c+1}.{r+len(find_window.serach_txt)}", 'HIGHLIGHT')
                yscroll_pos = (c - 10) / len(txts)
                if yscroll_pos < 0:
                    yscroll_pos = 0
                xscroll_pos = (r - 20) / max_x_len
                if xscroll_pos < 0:
                    xscroll_pos = 0
                log_printer.window['console'].Widget.xview_moveto(xscroll_pos)
                log_printer.window['console'].Widget.yview_moveto(yscroll_pos)

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
