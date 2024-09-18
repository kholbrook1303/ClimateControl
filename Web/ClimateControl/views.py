"""
Routes and views for the flask application.
"""
import logging
import traceback
import sys

from collections import OrderedDict
from datetime import datetime, timedelta
from flask import render_template, request

from bokeh.embed import components
from bokeh.models.axes import LinearAxis
from bokeh.models.ranges import Range1d
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.themes.theme import Theme

sys.path.append('/opt/ClimateControl/')

from lib.config import Config
from lib.db import SQLite
from lib.properties import ClimateControlVariable

from ClimateControl import app

logging.basicConfig(filename='ccweb.log', level=logging.DEBUG)

@app.route('/')
@app.route('/home')
def home():
    print (request.args)
    """Renders the ClimateControl page."""
    data = request.args.get('timespan_interval', None)
    if data:
        timespan, interval = [int(data[i:i+2]) for i in range(0, len(data), 2)]
    else:
        timespan = int(request.args.get('timespan', 24))
        interval = int(request.args.get('interval', 5))
    
    try:
        config = Config()
        sqlite = SQLite()
        date_criteria = (datetime.utcnow() - timedelta(hours=timespan)).strftime('%Y%m%d%H%M')
        query = "SELECT strftime('%Y', date), " \
            "strftime('%j', date), " \
            "strftime('%H', date), " \
            "strftime('%M', date), " \
            "avg(value), var, date " \
            "FROM sensorout " \
            "WHERE date >= DATETIME('now', '-" + str(timespan) + " hour') " \
            "GROUP BY  strftime('%Y', date), value, var " \
            "ORDER BY date ASC;"
        app.logger.debug(query)
        results = sqlite.cur.execute(query)

        variables = dict()
        for result in results:
            app.logger.debug(result)
            var = result[5]
            ccv = ClimateControlVariable[var].value
            data = int(result[4])
            date = datetime.strptime(result[6], '%Y-%m-%d %H:%M:%S.%f')
            
            if not variables.get(var):
                variables[var] = {
                    'x'         : [date],
                    'y'         : [data],
                    'variable'  : ccv
                    }
                    
            else:
                variables[var]['x'].append(date)
                variables[var]['y'].append(data)
                
        variables = OrderedDict(sorted(variables.items(), key=lambda x: x[0]))
        
        # Initialize plot
        plot = figure(
            width           = 800,
            x_axis_label    = 'DateTime',
            x_axis_type     = 'datetime',
            y_axis_type     = 'linear',
            title           = 'Trending Environment Variables',
            )
        
        plot.axis[0].axis_label_text_color = "white"
        plot.axis[0].axis_label_text_font_style = 'bold italic'
        plot.axis[0].axis_line_color = "white"
        plot.axis[0].major_label_text_color = "white"
        plot.axis[0].major_tick_line_color = "white"
        plot.axis[0].minor_tick_line_color = "white"
        
        idx = 0
        plots = list()
        current_variables = list()
        for var, var_meta in variables.items():
            if var == 'tempC':
                continue
            
            idx += 1
            
            current_variables.append({
                'current_time': var_meta['x'][-1:][0].strftime("%Y/%m/%d %H:%M:%S"),
                'current_measurement': round(var_meta['y'][-1:][0], 2),
                'identity': var_meta['variable'].description,
                'unit': var_meta['variable'].chart_unit
                })

            y_range_name = 'default'
            if idx > 1:
                y_range_name = var_meta['variable'].name
                if idx == 2:
                    plot.extra_y_ranges = {
                        var_meta['variable'].name: Range1d(
                            start=var_meta['variable'].chart_range_min, 
                            end=var_meta['variable'].chart_range_max
                            )
                        }
                else:
                    plot.extra_y_ranges[var_meta['variable'].name] = Range1d(
                        start=var_meta['variable'].chart_range_min, 
                        end=var_meta['variable'].chart_range_max
                        )
                    
                plot.add_layout(LinearAxis(
                    y_range_name=var_meta['variable'].name,
                    ), 'right')
            # else:
            #     plot.y_range = Range1d(
            #         start=var_meta['variable'].chart_range_min,
            #         end=var_meta['variable'].chart_range_max
            #         )
                
            plot.axis[idx].axis_label = var_meta['variable'].description
            plot.axis[idx].axis_label_text_color=var_meta['variable'].chart_color
            plot.axis[idx].axis_label_text_font_style='bold italic'
            plot.axis[idx].axis_line_color=var_meta['variable'].chart_color
            plot.axis[idx].major_label_text_color=var_meta['variable'].chart_color
            plot.axis[idx].major_tick_line_color=var_meta['variable'].chart_color
            plot.axis[idx].minor_tick_line_color=var_meta['variable'].chart_color
                
            plot.line(
                x=var_meta['x'],
                y=var_meta['y'],
                line_width=2,
                color=var_meta['variable'].chart_color,
                y_range_name=y_range_name,
                legend_label=var_meta['variable'].description
                )
        
        plot.toolbar.logo = None
        plot.toolbar_location = "above"
        plot.legend.location  = 'bottom_center'
        plot.legend.orientation = "horizontal"
        plot.legend.click_policy = 'mute'
        plot.legend.background_fill_color = "#2F2F2F"
        plot.legend.border_line_color = "white"
        plot.legend.label_text_color = "white"

        plots.append(plot)
                
        current_variables = sorted(current_variables, key=lambda d: d['identity'])
            
        # Get Chart Components
        theme = Theme(json={
            'attrs' : {
                'Plot': {
                    'background_fill_color': '#2F2F2F',
                    'border_fill_color': '#2F2F2F',
                    'outline_line_color': 'white',
                },
                'Axis': {
                    'axis_line_color': None,
                },
                'Grid': {
                    'grid_line_dash': [6, 4],
                    'grid_line_alpha': .3,
                },
                'Title': {
                    'text_color': 'white'
                }
            }
        })
        script, div = components(plots, theme=theme)

        # grab the static resources
        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()

        # Return the components to the HTML template
        return render_template(
            'index.html',
            title='Climate Control Automation',
            plot_script=script,
            plot_divs=div,
            js_resources=js_resources,
            css_resources=css_resources,
            current_variables=current_variables
        )
    
    except Exception as e:
        app.logger.exception(e)
        traceback.print_exc()
        
    return render_template(
        'index.html',
        title='Climate Control Automation',
        year=datetime.now().year,
    )