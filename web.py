import os

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE

from flask import Flask, render_template

import lantern


app = Flask(__name__)




@app.route('/')
def home():
    l = lantern.Lantern(os.environ['LANTERN_USER'], os.environ['LANTERN_PASSWORD'])
    payload = {
        'group_name': l.group_name,
        'today': round(l.today()['from_grid'] / 3600000),
        'month': round(l.month()['from_grid'] / 3600000),
        'year': round(l.year()['from_grid'] / 3600000),
    }
    return render_template('index.html', **payload)


@app.route('/day')
def day():
    l = lantern.Lantern(os.environ['LANTERN_USER'], os.environ['LANTERN_PASSWORD'])
    today = l.today()
    groups = list(lantern.flatten(today['sub_groups']))
    data = lantern.decode_block_to_kwh(groups[-1])

    x = list(range(len(data)))
    y = data

    fig = figure(plot_height=400, plot_width=600)
    fig.line(x, y, line_width=4)

    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    script, div = components(fig)

    return render_template(
        'day.html',
        plot_script=script,
        plot_div=div,
        js_resources=js_resources,
        css_resources=css_resources,
    )
    # return encode_utf8(html)


@app.route('/month')
def month():
    return 'This is the month view'


@app.route('/year')
def year():
    return 'This is the year view'

@app.route('/panel')
def panel_config():
    l = lantern.Lantern(os.environ['LANTERN_USER'], os.environ['LANTERN_PASSWORD'])

    config = l.config

    panels = {}

    for panel in config['panels']:
        panels[panel['index']] = lantern.Panel(**panel)
        print(panels[panel['index']])

    breaker_groups = lantern.flatten(config['breaker_groups'][0]['sub_groups'])

    for group in breaker_groups:
        for breaker in group['breakers']:
            panel_index = breaker['panel']
            panels[panel_index].breakers.append(lantern.Breaker(**breaker))

    return render_template('panel.html', panels=panels)
