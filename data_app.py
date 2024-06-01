import pandas as pd
import squarify
from bokeh.plotting import figure
from bokeh.io import curdoc
from bokeh.models import HoverTool, ColumnDataSource, Select
from bokeh.layouts import column, gridplot
from bokeh.transform import cumsum
from bokeh.palettes import Category10, Category20c
from math import pi
import numpy as np
from bokeh.tile_providers import get_provider, Vendors

# Chargement des données
covid_morocco = pd.read_csv('covid19-morocco.csv')
covid_morocco_regions = pd.read_csv('covid19-morocco-regions.csv')
regions_morocco = pd.read_csv('regions-morocco.csv')

# Figure 1: Cas cumulés, récupérations et décès
p1 = figure(x_axis_type="datetime", title="COVID-19 au Maroc - Cas Cumulés, Récupérations et Décès", width=400, height=300)
p1.background_fill_color = "#f5f5f5"
p1.border_fill_color = "#ffffff"
p1.line(pd.to_datetime(covid_morocco['date']), covid_morocco['total_cases'], legend_label="Total Cases", line_width=2, name="Total Cases")
p1.line(pd.to_datetime(covid_morocco['date']), covid_morocco['recovered'], legend_label="Recovered", line_width=2, color="green", name="Recovered")
p1.line(pd.to_datetime(covid_morocco['date']), covid_morocco['total_deaths'], legend_label="Total Deaths", line_width=2, color="red", name="Total Deaths")
hover = HoverTool()
hover.tooltips = [("Date", "@x{%F}"), ("Value", "@y")]
hover.formatters = {'@x': 'datetime'}
p1.add_tools(hover)
p1.legend.location = "top_left"

# Filtrer les données pour obtenir les dernières valeurs
latest_data = covid_morocco.iloc[-1]

# Préparer les données pour Bokeh
variables = ['active_cases', 'total_deaths', 'recovered']
labels = ['Actif', 'Décès', 'Rétabli']
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

values = latest_data[variables].values.flatten().tolist()

# Utiliser squarify pour calculer les dimensions des carrés
rects = squarify.normalize_sizes(values, 1, 1)
rects = squarify.squarify(rects, 0, 0, 1, 1)

source_data = {
    'x': [r['x'] + r['dx']/2 for r in rects],
    'y': [r['y'] + r['dy']/2 for r in rects],
    'width': [r['dx'] for r in rects],
    'height': [r['dy'] for r in rects],
    'label': labels,
    'value': values,
    'color': colors
}
source = ColumnDataSource(source_data)

# Créer la figure pour le treemap
p2 = figure(width=400, height=300, title="COVID-19 Morocco Treemap", x_range=(0, 1), y_range=(0, 1), tools="hover", tooltips=[("Variable", "@label"), ("Value", "@value")])
p2.background_fill_color = "#f5f5f5"
p2.border_fill_color = "#ffffff"

# Ajouter les rectangles
p2.rect(x='x', y='y', width='width', height='height', source=source, color='color', line_color='white')

# Ajouter les étiquettes des catégories avec ajustement de la taille
for i in range(len(source_data['label'])):
    width = source_data['width'][i]
    height = source_data['height'][i]
    size = '10pt'
    if width * height > 0.1:
        size = '14pt'
    elif width * height > 0.05:
        size = '12pt'
    elif width * height > 0.01:
        size = '10pt'
    else:
        size = '8pt'
    p2.text(x=[source_data['x'][i]], y=[source_data['y'][i]], text=[source_data['label'][i]], text_align="center", text_baseline="middle", text_color="white", text_font_size=size)

# Supprimer les axes x et y
p2.xaxis.visible = False
p2.yaxis.visible = False

# Préparer les données pour le graphique en secteurs
dictionary_labels = {
    'TTH': 'Tanger-Tétouane-Al Hoceima',
    'OR': 'Oriental',
    'FM': 'Fès-Meknès',
    'RSK': 'Rabat-Salé-Kénitra',
    'BK': 'Béni Mellal-Khénifra',
    'CS': 'Casablanca-Settat',
    'MS': 'Marrakech-Safi',
    'DT': 'Drâa-Tafilalet',
    'SM': 'Souss-Massa',
    'GO': 'Guelmim-Oued Noun',
    'LS': 'Laâyoune-Sakia El Hamra',
    'DO': 'Dakhla-Oued Ed-Dahab'
}

covid_morocco_regions = covid_morocco_regions.set_index('Date')
regions = [covid_morocco_regions[x].iloc[-1] for x in dictionary_labels]
labels = [dictionary_labels[x] for x in dictionary_labels]

# Préparer les données pour Bokeh
data_dict = {'regions': regions, 'labels': labels}
data = pd.DataFrame(data_dict)
data['angle'] = data['regions'] / data['regions'].sum() * 2 * pi
data['color'] = Category20c[len(data)]

# Créer un graphique en secteurs avec Bokeh
p3 = figure(height=300, width=400, title="Répartition des cas COVID-19 par région", toolbar_location=None, tools="hover", tooltips="@labels: @regions", x_range=(-0.5, 1.0))
p3.background_fill_color = "#f5f5f5"
p3.border_fill_color = "#ffffff"

p3.wedge(x=0, y=1, radius=0.4, start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'), line_color="white", fill_color='color', legend_field='labels', source=data)
p3.axis.axis_label = None
p3.axis.visible = False
p3.grid.grid_line_color = None

# Map of COVID-19 Cases in Morocco
dregions = pd.read_csv('covid19-morocco-regions.csv')
regions_info = pd.read_csv('regions-morocco.csv')
regions_info.columns = ['Region_full', 'Region', 'Latitude', 'Longitude', 'Population', 'Contribution_GDP']
dregions.columns = ['Date', 'Confirmed', 'Deaths', 'Recovered', 'Excluded', 'TTH', 'OR', 'FM', 'RSK', 'BK', 'CS', 'MS', 'DT', 'SM', 'GO', 'LS', 'DO']
dregions['Date'] = pd.to_datetime(dregions['Date'])

dregions_melted = dregions.melt(id_vars=['Date'], var_name='Region', value_name='Ncases')
region_codes = regions_info['Region'].unique()
dregions_melted = dregions_melted[dregions_melted['Region'].isin(region_codes)]
combined_df = pd.merge(dregions_melted, regions_info, on='Region', how='left', suffixes=('_cases', '_info'))

def merc(lat, lon):
    k = 6378137
    x = lon * (k * np.pi / 180.0)
    y = np.log(np.tan((90 + lat) * np.pi / 360.0)) * k
    return (x, y)

def prepare_data(DATE):
    row = combined_df[combined_df.Date == DATE]
    df = {'latitude': row['Latitude'], 'longitude': row['Longitude'], 'region': row['Region_full'], 'Ncases': row['Ncases']}
    df = pd.DataFrame(df)
    if not df.empty:
        df['mercator_x'], df['mercator_y'] = zip(*df.apply(lambda row: merc(row['latitude'], row['longitude']), axis=1))
    return df

def normalize_sizes(sizes, min_size=10, max_size=50):
    if sizes.empty:
        return sizes
    norm_sizes = (sizes - sizes.min()) / (sizes.max() - sizes.min())
    return min_size + norm_sizes * (max_size - min_size)

def CovidMap(DATE):
    df = prepare_data(DATE)
    if df.empty:
        return None
    df['size'] = normalize_sizes(df['Ncases'])
    source = ColumnDataSource(df)
    tile_provider = get_provider(Vendors.CARTODBPOSITRON)
    p8 = figure(title=f"Map of COVID-19 Cases in Morocco by {DATE}", x_axis_type="mercator", y_axis_type="mercator", width=400, height=300)
    p8.add_tile(tile_provider)
    p8.add_tools(HoverTool(tooltips=[("Region", "@region"), ("Cases", "@Ncases")]))
    p8.circle(x='mercator_x', y='mercator_y', size='size', fill_color="red", fill_alpha=0.6, source=source)
    return p8

DATE = pd.to_datetime('2020-10-02')
p8 = CovidMap(DATE)

covid_morocco_regions = pd.read_csv('covid19-morocco-regions.csv')

covid_morocco_regions['Date'] = pd.to_datetime(covid_morocco_regions['Date'])


line_data = covid_morocco_regions.melt(id_vars='Date', value_vars=['TTH', 'OR', 'FM', 'RSK', 'BK', 'CS', 'MS', 'DT', 'SM', 'GO', 'LS', 'DO'], var_name='Region', value_name='Cases')
source = ColumnDataSource(data={'Date': [], 'Cases': []})
p = figure(height=300, width=400, title='Total Evolution of COVID-19 Cases per Region', x_axis_type='datetime')
line = p.line('Date', 'Cases', source=source, line_width=2, color=Category10[10][0])

def update_plot(attr, old, new):
    region = select.value
    new_data = line_data[line_data['Region'] == region]
    source.data = {'Date': new_data['Date'], 'Cases': new_data['Cases']}
    p.title.text = f'Total Evolution of COVID-19 Cases in {region}'

select = Select(title='Select Region:', value='TTH', options=['TTH', 'OR', 'FM', 'RSK', 'BK', 'CS', 'MS', 'DT', 'SM', 'GO', 'LS', 'DO'])
select.on_change('value', update_plot)
update_plot(None, None, None)
layout = column(select, p)

# Charger les données
covid_morocco_regions = pd.read_csv('covid19-morocco-regions.csv')

# Préparer les données
covid_morocco_regions['Date'] = pd.to_datetime(covid_morocco_regions['Date'])

# Créer une source de données pour Bokeh
source_tests_negatifs = ColumnDataSource(data={
    'Date': pd.to_datetime(covid_morocco_regions['Date']),
    'Excluded': covid_morocco_regions['Excluded']
})

# Créer la figure
p4 = figure(height=400, width=700, title='Evolution of Negative Tests (Excluded) per Day', x_axis_type='datetime')
p4.background_fill_color = "#f5f5f5"  # Changer la couleur de fond
p4.border_fill_color = "#ffffff"      # Changer la couleur de bordure
p4.line('Date', 'Excluded', source=source_tests_negatifs, line_width=2, color='blue', legend_label='Excluded')

# Ajouter un outil de survol
hover_tests_negatifs = HoverTool()
hover_tests_negatifs.tooltips = [("Date", "@Date{%F}"), ("Excluded", "@Excluded")]
hover_tests_negatifs.formatters = {'@Date': 'datetime'}
p4.add_tools(hover_tests_negatifs)

# Ajouter une légende et des étiquettes d'axes
p4.legend.location = "top_left"
p4.xaxis.axis_label = 'Date'
p4.yaxis.axis_label = 'Number of Negative Tests'

# Organiser les visualisations
nlayout = gridplot([[p1, p2, p3], [layout, p8, p4]], sizing_mode='stretch_both')
curdoc().add_root(nlayout)
curdoc().title = "COVID-19 Dashboard Morocco"
