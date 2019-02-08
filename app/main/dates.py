import datetime


# def monday():
#     today = datetime.date.today()
#     weekday = datetime.date.weekday(today)
#     monday = today-datetime.timedelta(weekday)
#     if weekday >4:
#         monday += datetime.timedelta(days=7)
#     return monday
#
#
# def this_week():
#     daily = datetime.timedelta
#     week = [monday() + daily(x) for x in range(6)]
#     return week


class Week(object):
    monday = ['Monday', 'Mon', None]
    tuesday = ['Tuesday', 'Tue', None]
    wednesday = ['Wednesday', 'Wed', None]
    thursday = ['Thursday', 'Thu', None]
    friday = ['Friday', 'Fri', None]
    saturday = ['Saturday', 'Sat', None]

    def __init__(self, date=datetime.date.today()):
        _weekday = datetime.date.weekday(date)
        _monday = date - datetime.timedelta(_weekday)
        if _weekday > 4:
            _monday += datetime.timedelta(7)
        self.monday[2] = _monday
        for _day, _interval in [(self.tuesday, 1), (self.wednesday, 2),
                                (self.thursday, 3), (self.friday, 4), (self.saturday, 5)]:
            _day[2] = _monday + datetime.timedelta(_interval)

    def get_dates_list(self):
        week = [_day[2] for _day in [self.monday, self.tuesday, self.wednesday,
                self.thursday, self.friday, self.saturday]]
        return week


def date_from_string(date: str):
    return datetime.datetime.date(datetime.datetime.strptime(date, '%Y-%m-%d'))


def time_from_string(time: str):
    return datetime.datetime.time(datetime.datetime.strptime(time, '%I:%M %p'))
