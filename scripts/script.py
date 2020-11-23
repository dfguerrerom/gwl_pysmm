import numpy as np
import pandas as pd
import geemap

from datetime import datetime, date
from ipywidgets import interact, HTML, interact_manual, interactive, HBox, VBox, fixed, widgets

import ee
import matplotlib.pyplot as plt


ee.Initialize()
aoi_ee = ee.FeatureCollection('users/dafguerrerom/FAO/PYSMM/all_sipalaga_phu_points')

Map = geemap.Map(center=[-2.12, 113.83], zoom=6)
Map.layout.height='250px'
Map.layout.width='250px'
Map.clear_controls()
Map.add_basemap('Google Satellite')

# Widgets
def create_wpoints(data):
    options = data.index.unique(level=0).values.tolist()
    options.sort()
    
    w_points = widgets.Dropdown(
        options=options,
        value=options[0],
        description='ID:',
        disabled=False,
    )
    return w_points

w_measures = widgets.Dropdown(
    options = ['GWL_max', 'GWL_min', 'GWL_rata', 'SM_max', 'SM_min', 'SM_rata', 'Total'],
    value = 'GWL_max'
)

start_date = datetime(2014, 1, 1)
end_date = date.today()
dates = pd.date_range(start_date, end_date, freq='M')

options = [(date.strftime(' %b %Y '), date) for date in dates]
index = (0, len(options)-1)

w_date_slider = widgets.SelectionRangeSlider(
    options=options,
    index=index,
    description='Dates',
    orientation='horizontal',
    layout={'width': '500px'}
)

w_temp = widgets.Dropdown(
    options=[('Daily', 'd'),('Monthly','m'), ('Yearly','y')],
    value='d',
    description='Group by:',
    disabled=False,
)

def show_figure(w_date_slider, w_measure, w_points, w_temp, combined_data):
    
    data = combined_data
    ts = data.loc[w_points][w_date_slider[0]:w_date_slider[1]].groupby(pd.Grouper(freq=w_temp)).mean()
    date = ts.index
    
    field_measure = ts['smm'].interpolate(method='linear')
    smm_measure = ts[w_measure].interpolate(method='linear')
    
#     display(field_measure.describe())
    
    fig,ax = plt.subplots()
    # make a plot
    ax.plot(date, field_measure, color="red", marker="o")
    # set x-axis label
    ax.set_xlabel("year",fontsize=14)
    # set y-axis label
    ax.set_ylabel("Soil Moisture",color="red",fontsize=14)
    
    # twin object for two different y-axis on the sample plot
    ax2=ax.twinx()
    # make a plot with different y-axis using second axis object
    ax2.plot(date, smm_measure, color="blue", marker="o")
    ax2.set_ylabel(w_measure, color="blue", fontsize=14)

    # Display Map
    selected_feature = aoi_ee.filterMetadata('stasiun', 'equals', w_points).geometry()
    square = selected_feature.buffer(ee.Number(10000).sqrt().divide(2), 1).bounds()
    empty = ee.Image().byte();
    outline = empty.paint(featureCollection=square, color=1, width=2)
    Map.addLayer(outline, {'palette': 'FF0000'}, 'edges');
    Map.centerObject(square, zoom=15)
    
combined_data = pd.read_pickle('./data/Combined_sipalaga_all_unnested.pkl')

run_figure = interactive(show_figure, {'manual':True}, 
                     w_date_slider=w_date_slider, 
                     w_measure=w_measures, 
                     w_points=create_wpoints(combined_data), 
                    w_temp=w_temp,
                    combined_data=fixed(combined_data))

run_figure.children[-2].description = 'Show figure'

def ui():
    display(HBox([run_figure.children[1],run_figure.children[2], run_figure.children[3]]))
    display(HBox([run_figure.children[0], run_figure.children[-2]]))
    display(HBox([Map]))
    display(HBox([run_figure.children[-1]]))
