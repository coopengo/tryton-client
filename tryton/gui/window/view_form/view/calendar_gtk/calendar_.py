# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import calendar
import datetime

import goocalendar

from tryton.common import MODELACCESS
from tryton.config import CONFIG

from .dates_period import DatesPeriod

_colors = CONFIG['calendar.colors'].split(',')


class Calendar_(goocalendar.Calendar):
    'Calendar'

    def __init__(self, attrs, view, fields, event_store=None):
        super(Calendar_, self).__init__(
            event_store, attrs.get('mode', 'month'))
        self.props.selected_border_color = _colors[1]
        if hasattr(self.props, 'selected_text_color'):
            self.props.selected_text_color = _colors[0]
        self.attrs = attrs
        self.view_calendar = view
        self.fields = fields
        self.event_store = event_store
        self.current_domain_period = self.get_displayed_period()

    def set_default_date(self, record, selected_date):
        dtstart = self.attrs['dtstart']
        record[dtstart].set(record, datetime.datetime.combine(selected_date,
            datetime.time(0)))
        record.on_change([dtstart])
        record.on_change_with([dtstart])

    def get_displayed_period(self):
        cal = calendar.Calendar(self.firstweekday)
        if self.view == 'day':
            first_date = self.selected_date
            last_date = self.selected_date + datetime.timedelta(1)
        if self.view == 'week':
            week = goocalendar.util.my_weekdatescalendar(cal,
                self.selected_date)
            first_date = week[0]
            last_date = week[6]
            last_date += datetime.timedelta(1)
        elif self.view == 'month':
            weeks = goocalendar.util.my_monthdatescalendar(cal,
                self.selected_date)
            first_date = weeks[0][0]
            last_date = weeks[5][6]
            last_date += datetime.timedelta(1)
        displayed_period = DatesPeriod(first_date, last_date)
        return displayed_period

    def update_domain(self):
        displayed_period = self.get_displayed_period()
        if not displayed_period.is_in(self.current_domain_period):
            self.current_domain_period = displayed_period
            return True
        return False

    def current_domain(self):
        first_datetime, last_datetime = \
            self.current_domain_period.get_dates(True)
        dtstart = self.attrs['dtstart']
        dtend = self.attrs.get('dtend') or dtstart
        domain = ['OR',
            ['AND', (dtstart, '>=', first_datetime),
                (dtstart, '<', last_datetime)],
            ['AND', (dtend, '>=', first_datetime),
                (dtend, '<', last_datetime)],
            ['AND', (dtstart, '<', first_datetime),
                (dtend, '>', last_datetime)]]
        return domain

    def get_colors(self, record):
        text_color = _colors[0]
        if self.attrs.get('color'):
            text_color = record[self.attrs['color']].get(record)
        bg_color = _colors[1]
        if self.attrs.get('background_color'):
            bg_color = record[self.attrs['background_color']].get(
                record)
        return text_color, bg_color

    def display(self, group):
        def is_date_only(value):
            return (isinstance(value, datetime.date)
                and not isinstance(value, datetime.datetime))
        dtstart = self.attrs['dtstart']
        dtend = self.attrs.get('dtend')
        if self.view_calendar.record:
            record = self.view_calendar.record
            date = record[dtstart].get(record)
            if date:  # select the day of the current record
                self.select(date)

        event_store = goocalendar.EventStore()

        model_access = MODELACCESS[self.view_calendar.screen.model_name]
        editable = (
            bool(int(self.view_calendar.attributes.get('editable', 1)))
            and model_access['write'])

        for record in group:
            if not record[dtstart].get(record):
                continue

            start = record[dtstart].get_client(record)
            record[dtstart].state_set(record)
            if dtend:
                end = record[dtend].get_client(record)
                record[dtend].state_set(record)
            else:
                end = None
            midnight = datetime.time(0)
            all_day = is_date_only(start) and (not end or is_date_only(end))
            if not isinstance(start, datetime.datetime):
                start = datetime.datetime.combine(start, midnight)
            if end and not isinstance(end, datetime.datetime):
                end = datetime.datetime.combine(end, midnight)

            # Skip invalid event
            if end is not None and start > end:
                continue

            text_color, bg_color = self.get_colors(record)
            label = '\n'.join(record[attrs['name']].get_client(record)
                for attrs in self.fields).rstrip()
            event_editable = (
                editable
                and not record[dtstart].get_state_attrs(record).get(
                    'readonly', False)
                and (not dtend
                    or not record[dtend].get_state_attrs(record).get(
                        'readonly', False)))
            event = goocalendar.Event(label, start, end, text_color=text_color,
                bg_color=bg_color, all_day=all_day, editable=event_editable)
            event.record = record
            event_store.add(event)
        self.event_store = event_store

        self.grab_focus(self.get_root_item())
