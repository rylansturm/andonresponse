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
    """ returns an object with info for days (Mon-Sat) of the week which contains the day used in initialization """
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
        """ returns a list with just the datetime.date objects of the week """
        week = [_day[2] for _day in [self.monday, self.tuesday, self.wednesday,
                self.thursday, self.friday, self.saturday]]
        return week


def date_from_string(date):
    """ returns a datetime.date object. arg can be string (format below), datetime.date, or datetime.datetime """
    _type = type(date)
    try:
        if _type == datetime.date:
            return date
        elif _type == datetime.datetime:
            return datetime.datetime.date(date)
        else:
            return datetime.datetime.date(datetime.datetime.strptime(date, '%Y-%m-%d'))
    except ValueError:
        return date
    except TypeError:
        return date


def time_from_string(time):
    """ returns a datetime.time object. arg can be string (format below), datetime.time, or datetime.datetime """
    _type = type(time)
    try:
        if _type == datetime.time:
            return time
        elif _type == datetime.datetime:
            return datetime.datetime.time(time)
        else:
            try:
                return datetime.datetime.time(datetime.datetime.strptime(time, '%I:%M %p'))
            except ValueError:
                return datetime.datetime.time(datetime.datetime.strptime(time, '%H:%M:%S'))
    except ValueError:
        return time
    except TypeError:
        return time


def datetime_from_string(time):
    """ returns a datetime.datetime object. arg can be string (format below) or datetime.datetime """
    try:
        if type(time) == datetime.datetime:
            return time
        else:
            return datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return time
    except TypeError:
        return time


def datetime_from_time(time: datetime.time, date: datetime.date=datetime.date.today()):
    """ returns a datetime.datetime object with today's date, given a datetime.time object """
    if type(time) == datetime.time:
        return datetime.datetime.combine(date, time)
    else:
        return time


def get_available_time(times: list):
    """ given a list of datetime.time or datetime.datetime objects, return the available time (datetime.timedelta).
     list passed must be all of the plan times in order, alternating between start and stop times"""
    available_time = datetime.timedelta(0)
    for time in times:
        if time:
            t = datetime_from_time(time)
            if times.index(time) > 0 and t < times[times.index(time)-1]:
                t += datetime.timedelta(1)
            times[times.index(time)] = t
    for i in range(len(times) // 2):
        try:
            available_time += times[2*i+1] - times[2*i]
        except TypeError:
            pass
    return available_time
