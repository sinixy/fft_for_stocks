from flask import flash, request, render_template, make_response, send_from_directory
from datetime import datetime, timedelta
from fourier.models import *
from fourier.extrapolation import fourier_extrapolation
from fourier import app
from plotly.utils import PlotlyJSONEncoder
from pandas import date_range
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
import yfinance as yf



@app.before_first_request
def before_first_request():
	populate_db()


@app.route('/about')
def about():
	asset_types = Asset_Type.query.all()
	return render_template('about.html', asset_types=asset_types)


@app.route('/update_chart', methods=['GET'])
def update_chart():
	data = request.args
	change_date = int(data.get('changeDate'))
	symbol = data.get('asset')
	if change_date:
		chart_data = get_chart(
			symbol,
			data.get('train_start'),
			data.get('train_end'),
			data.get('prediction_end')
		)
		if chart_data['return_code'] == 200:
			return {
				'data': chart_data,
				'errors': []
			}
		elif chart_data['return_code'] == 400:
			return {
				'data': {},
				'errors': ['Дату введено некоректно!']
			}
		else:
			return {
				'data': {},
				'errors': ['Помилка!']
			}
	elif symbol:
		chart_data = get_chart(symbol)
		return {
			'data': chart_data,
			'errors': []
		}
	else:
		return {'data': {}, 'errors': ['Bad request']}, 400


@app.route('/', defaults={'u_path': ''})
@app.route('/<path:u_path>')
def index(u_path):
	asset_types = Asset_Type.query.all()
	if u_path:
		market = u_path.lower()
		at_dict = {i.name.lower(): i.id for i in asset_types}
		if u_path in at_dict.keys():
			type_id = at_dict[u_path]
			assets = Asset.query.filter_by(type_id=type_id)
			target = assets[0]
			chart_data = get_chart(target.symbol)
			status = chart_data['return_code']
			if status == 200:
				return render_template(
					'chart.html',
					chart_data={'data': chart_data, 'errors': []},
					assets=assets,
					asset_types=asset_types,
				)
	return render_template('about.html', asset_types=asset_types)


def get_chart(symbol, train_start=None, train_end=None, prediction_end=None):
	'''
	train_start - початок області тренувальних даних
	train_end - кінець області тренувальних даних == початок області прогнозування
	prediction_end - кінець області прогнозування
	'''
	def str_to_datetime(s):
		if type(s) == str:
			return datetime.strptime(s, '%d-%m-%Y')
		return s
	train_start = str_to_datetime(train_start)
	train_end = str_to_datetime(train_end)
	prediction_end = str_to_datetime(prediction_end)

	data = yf.download(symbol)
	start_date = data.iloc[0].name.to_pydatetime()
	if train_start and train_end and prediction_end:
		if train_start < train_end < prediction_end:
			if train_start < start_date:
				train_start = start_date
			train_end += timedelta(days=1)
		else:
			return {
				'return_code': 400
			}
	else:
		year_ago = datetime.now() - timedelta(days=365)
		train_start = year_ago if start_date < year_ago else start_date
		train_end = data.iloc[-30].name.to_pydatetime()
		prediction_end = data.iloc[-1].name.to_pydatetime()

	train = data.loc[train_start:train_end, 'Adj Close']

	n_predict = (prediction_end - train_end).days + 1
	prediction_index = train.index.to_list() + date_range(train_end, periods=n_predict).to_list()
	Y = fourier_extrapolation(train.values, n_predict)

	fig = go.Figure()
	fig.add_trace(go.Scatter(
		x=train.index,
		y=train.values,
		name='Навчальні данні'
	))
	
	test = data.loc[train_end:prediction_end, 'Adj Close']
	if test.size != 0:
		fig.add_trace(go.Scatter(
			x=test.index,
			y=test.values,
			line={'width': 3},
			name='Реальні данні'
		))
	fig.add_trace(go.Scatter(
		x=prediction_index,
		y=Y,
		opacity=0.5,
		name='Прогноз'
	))

	chart = json.dumps(fig, cls=PlotlyJSONEncoder)
	return {
		'chart': chart,
		'start_date': start_date.strftime('%d-%m-%Y'),
		'train_start': train_start.strftime('%d-%m-%Y'),
		'train_end': train_end.strftime('%d-%m-%Y'),
		'prediction_end': prediction_end.strftime('%d-%m-%Y'),
		'return_code': 200
	}



if __name__ == "__main__":
	app.run(debug=True)