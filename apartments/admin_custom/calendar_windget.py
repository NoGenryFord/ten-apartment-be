import calendar
from datetime import date
from django.utils.safestring import mark_safe

from apartments.models import Schedule, Apartment

#Calendar Widget
def schedule_calendar(obj):
    if not obj.pk:
        return "Schedule not available"
    #Get schedule on actual mounth
    today = date.today()
    schedule = Schedule.objects.filter(apartment=obj, date__month=today.month, date__year=today.year)

    #Fast search
    status_map = {s.date.day: s.status for s in schedule}

    #status colors
    colors = {
        'available': '#d4edda',
        'booked': '#f8d7da',
        'reserved': '#fff3cd',
        'maintenance': '#e2e3e5'
    }

    cal = calendar.HTMLCalendar(firstweekday=0)
    original_formatday = cal.formatday

    def formatday(day, weekday):
        if day != 0 and day in status_map:
            status = status_map[day]
            color = colors.get(status, 'white')
            return f'<td class="noday" style="background-color: {color}; border: 1px solid #ccc; text-align: center; padding: 5px;"><b>{day}</b><br/><small style="font-size: 8px">{status}</small></td>'
        return original_formatday(day, weekday)

    cal.formatday = formatday
    html = cal.formatmonth(today.year, today.month)
    return mark_safe(f'<div style="max-width: 300px;">{html}</div>')