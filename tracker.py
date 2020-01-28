from appJar import gui
import requests
import datetime

app = gui()
app.setFont(36)
app.setSize('fullscreen')


class Var:
    area = 'Talladega'
    block = 1
    shift = ''
    labels = {1: 'Assembly',
              2: 'Press',
              3: 'Blasting',
              4: 'Lapper',
              5: 'Pre-Size',
              6: 'Bonding',
              7: 'Finish',
              8: 'Chamfer',
              }
    colors = {'Safety': 'red',
              'Quality': 'white',
              'Delivery': 'blue',
              'NoType': 'blue',
              }


app.addLabel('header', colspan=2)
for seq in [1, 2, 3, 4, 5, 6, 7, 8]:
    meter = 'blockCycles{}'.format(seq)
    app.addMeter(meter, row=seq+1, column=0)
    app.setMeterFill(meter, 'maroon')
    app.setMeterFg(meter, 'white')
    app.setMeterBg(meter, 'dark blue')
    app.setMeterHeight(meter, 72)
    app.setMeterWidth(meter, 480)
    app.addLabel('andon{}'.format(seq), row=seq+1, column=1)


def create_kpi():
    kpi_date = datetime.date.today()
    if Var.shift == 'Grave':
        if datetime.datetime.now().hour < 7:
            kpi_date -= datetime.timedelta(days=1)
    last_kpi = requests.get('https://localhost/api/kpi/{}/{}/{}'.format(
        Var.area, Var.shift, str(kpi_date - datetime.timedelta(days=1))), verify=False)
    if last_kpi.status_code == 200:
        last_plan_cycle_time = last_kpi.json()['plan_cycle_time']
    else:
        last_plan_cycle_time = 54
    data = {'area': 'Talladega',
            'shift': Var.shift,
            'schedule': 'Regular',
            'd': str(kpi_date),
            'demand': 0,
            'plan_cycle_time': last_plan_cycle_time
            }
    try:
        r = requests.post('https://localhost/api/kpi', json=data, verify=False)
        print(r.json())
    except ConnectionError:
        print('Connection Failed')


def tracker():
    now = datetime.datetime.now()
    if now.hour >= 23:
        if now.minute >= 15:
            if Var.shift != 'Grave':
                Var.shift = 'Grave'
                create_kpi()
        Var.block = 1
    elif now.hour >= 15:
        if now.minute >= 15 or now.hour != 15:
            if Var.shift != 'Swing':
                Var.shift = 'Swing'
                create_kpi()
        Var.block = 4 if now.hour >= 21 else 3 if now.hour >= 19 else 2 if now.hour >= 17 else 1
    elif now.hour >= 7:
        if now.minute >= 15 or now.hour != 7:
            if Var.shift != 'Day':
                Var.shift = 'Day'
                create_kpi()
        Var.block = 4 if now.hour >= 13 else 3 if now.hour >= 11 else 2 if now.hour >= 9 else 1
    else:
        if Var.shift != 'Grave':
            Var.shift = 'Grave'
            create_kpi()
        Var.block = 4 if now.hour >= 5 else 3 if now.hour >= 3 else 2 if now.hour >= 1 else 1
    app.setLabel('header', '{} Shift\t\t{}\t\tBlock {}'.format(Var.shift, now.strftime('%I:%M %p'), Var.block))
    kpi_date = datetime.date.today()
    if Var.shift == 'Grave':
        if datetime.datetime.now().hour < 7:
            kpi_date -= datetime.timedelta(days=1)

    r = requests.get('https://localhost/api/cycles/block_tracker/Talladega/{}/{}/0'.format(
        Var.shift, str(kpi_date)), verify=False).json()
    for seq in [1, 2, 3, 4, 5, 6, 7, 8]:
        try:
            name = Var.labels[seq]
            cycles = r[str(seq)]['Cycles']
            expected = r[str(seq)]['Expected']
            responded = bool(r[str(seq)]['Responded'])
            andon_type = r[str(seq)]['Andon_Type']
            app.setMeter('blockCycles{}'.format(seq), (cycles/expected)*100, '{}  {}/{}'.format(name, cycles, expected))
            app.setLabel('andon{}'.format(seq), 'ANDON' if not responded else 'Normal')
            app.setLabelBg('andon{}'.format(seq), Var.colors[andon_type] if not responded else 'green')
        except:
            name = Var.labels[seq]
            app.setMeter('blockCycles{}'.format(seq), 0, name)
            app.setLabel('andon{}'.format(seq), 'N/A')


app.registerEvent(tracker)

if __name__ == '__main__':
    app.go()
