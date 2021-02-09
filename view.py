import datetime
import os
import urllib.request as url
from tkinter import *
from tkinter import BOTH
from tkinter import filedialog
from tkinter import messagebox as msgbx
from typing import List

import matplotlib.pyplot as plot
import pandas as pnds
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as Navigation

from simulation import start_simulation


# currency_pair, date1, date2
# https://stooq.pl/q/d/l/?s=eurpln&d1=20160304&d2=20200304&i=d&o=1111110
csv_time_column = 'Data'
graph_data_option = 'Zamkniecie'
csv_dir_path = os.path.join(os.path.curdir, "csvFiles")
internet_address = 'https://stooq.pl/q/d/l/?s={}&d1={}&d2={}&i=d&o=1111110'
currency_pairs = ('EURUSD', 'USDJPY', 'GBPUSD', 'AUDUSD', 'USDCHF', 'NZDUSD', 'USDCAD', 'WIG', 'WIG20', 'WIG30')
window = None
canvas = None
toolbar = None
menu_bar = None
choice: str = ""


def check_csv_dir():
    if not os.path.exists(csv_dir_path):
        os.mkdir(csv_dir_path)
    print("Directory '{}' checked!".format(csv_dir_path))


def destroy_window():
    global window
    if window is not None:
        try:
            window.destroy()
        except TclError:
            pass
        sys.exit(0)


def choose_value(title, text, values):
    global window

    def get_choice():
        global choice
        output = string_var.get()
        ok_var.set(1)
        top.destroy()
        if len(output) > 0 and output in values:
            choice = output
        else:
            choice = ""

    ok_var = IntVar()
    width = int((window.winfo_width()) / 20)
    height = int((window.winfo_height()) / 200)
    top = Toplevel()
    top.resizable(False, False)
    top.title(title)
    label = Label(top, text=text, background="#cccccc")
    label.pack()
    label.config(width=width, height=height)
    string_var = StringVar()
    string_var.set(values[0])
    opt_menu = OptionMenu(top, string_var, *values)
    opt_menu.pack()
    opt_menu.config(width=width, height=height, background="#cccccc")
    btn = Button(top, text='OK', command=get_choice, background="#cccccc")
    btn.pack()
    btn.config(width=width, height=height)
    return tuple((btn, ok_var))


def wait_for_value(components):
    global choice
    (components[0]).wait_variable(components[1])
    chosen: str = choice
    choice = ""
    return chosen


def get_currency_pair():
    global currency_pairs
    pair: str = wait_for_value(choose_value('Para walutowa', 'Wybierz parę walutową: ', currency_pairs))
    if pair is None or pair == "":
        msgbx.showerror('Para walutowa', 'Nieudany wybór pary walutowej!')
        return None
    return pair.lower()


def download_menu_option():
    global currency_pairs

    pair: str = get_currency_pair()
    if pair is None or pair == "":
        return

    earlier = (datetime.datetime.now()) - (datetime.timedelta(days=1410))
    d1: str = earlier.strftime("%Y%m%d")
    d2: str = (datetime.datetime.now()).strftime("%Y%m%d")

    try:
        address: str = internet_address.format(pair, d1, d2)
        print('input: {}'.format(address))
        testfile = url.URLopener()
        dst = os.path.join(csv_dir_path, ("{}.csv".format(pair)))
        print('output: {}'.format(dst))
        testfile.retrieve(address, dst)
        msgbx.showinfo('Plik csv', 'Odpowiedni plik został pobrany!\n'
                                   'Lokalizacja: "{}"'.format(dst))
    except:
        msgbx.showerror('Plik csv', 'Wystąpił błąd!')
    return


def choose_csv_file():
    global window
    window.filename = filedialog.askopenfilename(initialdir=csv_dir_path,
                                                 title='Wybierz odpowiedni plik csv')
    path_to_file: str = window.filename
    if path_to_file != '' and not os.path.isfile(path_to_file):
        msgbx.showerror('Wybór pliku', 'Wybrany plik nie istnieje: {}'.format(path_to_file))
        return ''
    return path_to_file


def show_2_graphs(graph_data, title, pair, points=None):
    global window, canvas, toolbar

    plot.close('all')
    fig, ax = plot.subplots(2, figsize=(14, 1), dpi=100, sharex=True,
                            gridspec_kw={'hspace': 0.05, 'wspace': 0})
    ax[0].set_title(title)
    ax[0].plot(graph_data[2], label=pair)
    ax[1].plot(graph_data[0], label='MACD')
    ax[1].plot(graph_data[1], label='SIGNAL')
    if points is not None:
        dictionary: dict = points
        for key, value in dictionary.items():
            ax[0].plot(key, value[0], 'or', color=value[1])
    ax[0].legend()
    ax[1].legend()
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
    toolbar = Navigation(canvas, window)
    toolbar.update()
    return


def show_graph(graph_data, title, pair):
    global window, canvas, toolbar
    plot.close('all')
    if type(graph_data) is tuple:
        show_2_graphs(graph_data, title, pair)
        return
    fig, ax = plot.subplots(1, figsize=(14, 1), dpi=100)
    ax.plot(graph_data)
    ax.set_title(title)
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
    toolbar = Navigation(canvas, window)
    toolbar.update()


def get_main_title(path_to_file):
    global currency_pairs
    pair: str = ''
    for cp in currency_pairs:
        tmp = cp.lower()
        if tmp in path_to_file:
            pair = cp
            break
    return pair


def prepare_canvas_and_toolbar():
    global window, canvas, toolbar
    if canvas is not None:
        canvas.get_tk_widget().destroy()
        canvas = None
    if toolbar is not None:
        toolbar.destroy()
        toolbar = None


def generate_title(main_title, csv_data, subtitle=None, stop_loss_used=False, take_profit_used=False):
    time_data = csv_data[csv_time_column]
    start_time = time_data.iloc[0]
    end_time = time_data.iloc[-1]
    to_append: str = ""
    if stop_loss_used is True:
        to_append = to_append + ' [SL]'
    if take_profit_used is True:
        to_append = to_append + ' [TP]'
    if subtitle is None:
        return ('[{}] [{} → {}]'.format(main_title, start_time, end_time)) + to_append
    else:
        return ('[{}] [{}] [{} → {}]'.format(main_title, subtitle, start_time, end_time)) + to_append


def calc_ema(day, n, graph_data) -> float:
    alpha = float(2/(n+1))
    factor = float(1 - alpha)
    numerator: float = float(0)
    denominator: float = float(0)
    for i in range(n+1):
        if day - i < 0:
            continue
        else:
            numerator = float(numerator + ((factor**i) * graph_data[day - i]))
            denominator = float(denominator + (factor**i))
    return float(numerator / denominator)


def calc_macd(day, graph_data) -> float:
    # MACD = EMA12 - EMA26
    ema12 = calc_ema(day, 12, graph_data)
    ema26 = calc_ema(day, 26, graph_data)
    return float(ema12 - ema26)


def get_macd_data(graph_data):
    macd_list: List[float] = []
    signal_list: List[float] = []
    for day in range(0, graph_data.size):
        macd_list.append(calc_macd(day, graph_data))
    for day in range(0, graph_data.size):
        signal_list.append(calc_ema(day, 9, macd_list))
    return tuple((macd_list, signal_list))


def new_graph(graph_data_src, subtitle=None):
    global window, canvas, toolbar
    path_to_file: str = choose_csv_file()
    if path_to_file is None or path_to_file == '':
        return
    else:
        prepare_canvas_and_toolbar()
        main_title = get_main_title(path_to_file)
        csv_data = pnds.read_csv(path_to_file)
        graph_data = csv_data[graph_data_option]
        if graph_data_src is not None:
            tmp_tuple = tuple((graph_data,))
            graph_data = graph_data_src(graph_data)
            graph_data = graph_data + tmp_tuple
        if subtitle is None:
            show_graph(graph_data, generate_title(main_title, csv_data), main_title.upper())
        else:
            show_graph(graph_data, generate_title(main_title, csv_data, subtitle), main_title.upper())


def exchange_rates_menu_option():
    new_graph(None)
    return


def macd_menu_option():
    new_graph(get_macd_data, 'MACD')
    return


def simulation_menu_option():
    global window, canvas, toolbar

    path_to_file: str = choose_csv_file()
    if path_to_file is None or path_to_file == '':
        return
    else:
        prepare_canvas_and_toolbar()
        main_title = get_main_title(path_to_file)
        csv_data = pnds.read_csv(path_to_file)
        graph_data = csv_data[graph_data_option]
        macd_tuple = get_macd_data(graph_data)

        ret_values = start_simulation(graph_data, macd_tuple[0], macd_tuple[1])

        points: dict = ret_values[0]
        pc_change_str: str = 'zysk: {}%'.format(ret_values[1])
        s_l_used: bool = ret_values[2]
        t_p_used: bool = ret_values[3]

        tmp_tuple = tuple((graph_data,))
        graph_data = macd_tuple + tmp_tuple

        show_2_graphs(graph_data,
                      generate_title(main_title, csv_data, pc_change_str, s_l_used, t_p_used),
                      main_title.upper(), points)
    return


def game_menu():
    global window, menu_bar
    menu_bar.add_command(label='Pobierz dane', command=download_menu_option)
    menu_bar.add_command(label='Kurs', command=exchange_rates_menu_option)
    menu_bar.add_command(label='MACD', command=macd_menu_option)
    menu_bar.add_command(label='Symulacja', command=simulation_menu_option)
    window.config(menu=menu_bar)


def program_opened():
    global window, menu_bar
    check_csv_dir()
    window = Tk()
    window.title('MS')
    window.geometry('1100x500')
    window.resizable(False, False)
    window.protocol('WM_DELETE_WINDOW', destroy_window)
    menu_bar = Menu(window)
    game_menu()
    window.mainloop()
