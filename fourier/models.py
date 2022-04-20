from flask_sqlalchemy import SQLAlchemy
from fourier import app
import os

db = SQLAlchemy(app)


class Asset_Type(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64))


class Asset(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	symbol = db.Column(db.String(16))
	description = db.Column(db.String(64))
	type_id = db.Column(db.Integer, db.ForeignKey(Asset_Type.id, ondelete="CASCADE"), nullable=False)
	type = db.relationship(Asset_Type, backref='assets')


def populate_db():
	db.create_all()
	if not Asset.query.first():
		import csv
		tables = {
			'Asset_Type': Asset_Type,
			'Asset': Asset
		}

		for table, model in tables.items():
			with open(f'fourier/static/test_table_data/{table.lower()}.csv', 'r') as file:
				reader = csv.DictReader(file, delimiter=',')
				for row in reader:
					data = {k: v for k, v in row.items() if v}
					obj = model(**data)
					db.session.add(obj)
			db.session.commit()
