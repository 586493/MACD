from enum import Enum
from tkinter import messagebox as msgbx


class MacdValue(Enum):
    MACD_NO_RECOMMENDATION = 3
    MACD_GREATER = 2
    MACD_LOWER = 1


points: dict = dict()
init_amount: int = 1000
volume: float = float(0)
money: float = float(init_amount)
buy_price: float = float(0)
position_opened: bool = False
indicator_values: list = []

use_stop_loss: bool = False
stop_loss_limit: float = float(0.015)

use_take_profit: bool = False
take_profit_limit: float = float(0.015)

SMALLEST_AMOUNT: float = 0.001


def truncate(amount: float) -> float:
    factor: int = int(1.0 / SMALLEST_AMOUNT)
    n: float = float(int(amount * factor))
    n /= factor
    return n


def get_situation(macd: float, signal: float) -> MacdValue:
    if macd > signal:
        return MacdValue.MACD_GREATER
    if macd < signal:
        return MacdValue.MACD_LOWER
    return MacdValue.MACD_NO_RECOMMENDATION


def stop_loss(exchange_rate: float) -> bool:
    global buy_price, position_opened, init_amount, stop_loss_limit
    if position_opened is False or exchange_rate > buy_price:
        return False
    else:
        abs_diff: float = abs(exchange_rate - buy_price)
        change: float = float(abs_diff/buy_price)
        return change >= stop_loss_limit


def take_profit(exchange_rate: float) -> bool:
    global buy_price, position_opened, init_amount, take_profit_limit
    if position_opened is False or exchange_rate < buy_price:
        return False
    else:
        abs_diff: float = abs(exchange_rate - buy_price)
        change: float = float(abs_diff / buy_price)
        return change >= take_profit_limit


def new_sell_point(exchange_rate: float):
    return tuple((exchange_rate, 'red'))


def new_buy_point(exchange_rate: float):
    return tuple((exchange_rate, 'green'))


def sell_cond(day) -> bool:
    cond1: bool = indicator_values[day - 3] is MacdValue.MACD_GREATER
    cond2: bool = indicator_values[day - 2] is MacdValue.MACD_LOWER
    return cond1 and cond2


def buy_cond(day) -> bool:
    cond1: bool = indicator_values[day - 3] is MacdValue.MACD_LOWER
    cond2: bool = indicator_values[day - 2] is MacdValue.MACD_GREATER
    return cond1 and cond2


def decision(day, exchange_rate: float, last_day: bool = False):

    global position_opened, points, volume, \
        money, indicator_values, buy_price, \
        use_take_profit, use_stop_loss
    # Miejsce, w którym MACD przecina SIGNAL od dołu jest sygnałem do zakupu akcji.
    # Miejsce, w którym MACD przecina SIGNAL od góry, jest sygnałem do sprzedaży akcji.

    if position_opened is True:

        if (use_take_profit is True and take_profit(exchange_rate) is True) \
                or (use_stop_loss is True and stop_loss(exchange_rate) is True) \
                or (sell_cond(day) is True) \
                or (last_day is True):

            position_opened = False
            points[day] = new_sell_point(exchange_rate)
            money = truncate(money + (volume * exchange_rate))
            volume = 0
            buy_price = float(0)
            return

    else:
        if (buy_cond(day) is True) and (money > 0) and (last_day is False):

            max_volume: float = money / exchange_rate
            real_max_volume: float = truncate(max_volume)
            if real_max_volume > 0:
                points[day] = new_buy_point(exchange_rate)
                buy_price = exchange_rate
                volume = real_max_volume
                money = truncate(money - (exchange_rate * real_max_volume))
                position_opened = True
            return


def start_simulation(graph_data, macd_list, signal_list) -> tuple:

    global position_opened, init_amount, points, volume, \
        money, indicator_values, buy_price, use_stop_loss, \
        use_take_profit

    result_s_l = msgbx.askyesno('Symulacja', 'Czy zastosować zlecenia typu stop loss?')
    use_stop_loss = True if result_s_l is True else False

    result_t_p = msgbx.askyesno('Symulacja', 'Czy zastosować zlecenia typu take profit?')
    use_take_profit = True if result_t_p is True else False

    indicator_values = []
    position_opened = False
    points.clear()
    volume = float(0)
    money = float(init_amount)
    buy_price = float(0)

    max_day = len(graph_data)
    for day in range(0, max_day):
        last_day: bool = False
        if day == (max_day - 1):
            last_day = True
        if day < (26+8):
            indicator_values.append(MacdValue.MACD_NO_RECOMMENDATION)
        else:
            indicator_values.append(get_situation(macd_list[day], signal_list[day]))
            decision(day, graph_data[day], last_day)

    # changes
    change: float = money - init_amount
    pc_change: float = (change * 100.0) / init_amount
    pc_change_str: str = '%.2f' % pc_change
    start_amount: str = '%.2f' % init_amount
    end_amount: str = '%.2f' % money
    text_s_l: str = 'tak' if use_stop_loss else 'nie'
    text_t_p: str = 'tak' if use_take_profit else 'nie'
    msgbx.showinfo(title='Symulacja',
                   message=('kwota początkowa = {}\nkwota końcowa = {}\n'
                            'zysk = {}%\nstop loss: {}\ntake profit: {}'.
                            format(start_amount, end_amount, pc_change_str,
                                   text_s_l, text_t_p)))
    return tuple((points, pc_change_str, use_stop_loss, use_take_profit))
