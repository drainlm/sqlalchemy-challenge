# Dependencies
import datetime as dt
import numpy as np
import pandas as pd

# Flask
from flask import Flask, jsonify

# SQLAlchemy
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

# Database setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(autoload_with=engine)
Measurement = Base.classes.measurement
Station = Base.classes.station
session = Session(bind=engine) # create a session object

# Flask setup
app = Flask(__name__)

# Routes
@app.route("/")
def home():
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    # 1 year ago from the last data point 
    latest_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = (dt.datetime.strptime(latest_date, '%Y-%m-%d') - dt.timedelta(days=365)).strftime('%Y-%m-%d')
    # Query last 12 months of precipitation
    results = session.query(Measurement.date, Measurement.prcp)\
                     .filter(Measurement.date >= one_year_ago)\
                     .order_by(Measurement.date).all()
    session.close()
    # Convert to dictionary
    prcp_dict = {}
    for date, prcp in results:
        prcp_dict[date] = prcp
    return jsonify(prcp_dict)

@app.route("/api/v1.0/stations")
def stations():
    # Query all stations
    results = session.query(Station.station).all()

    # Convert list 
    stations = list(np.ravel(results))

    # JSON list of stations
    return jsonify(stations)

@app.route("/api/v1.0/tobs")
def tobs():
    # Find the most active station
    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()

    # 1 year ago from the last data point
    latest_date = session.query(Measurement.date).\
        filter(Measurement.station == most_active_station[0]).\
        order_by(Measurement.date.desc()).first()

    latest_date = dt.datetime.strptime(latest_date[0], "%Y-%m-%d")
    one_year_ago = latest_date - dt.timedelta(days=365)

    # Query the temperature obs in most active station for the last year
    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station[0]).\
        filter(Measurement.date >= one_year_ago).all()

    # Convert to dictionary
    tobs_dict = {}
    for result in results:
        tobs_dict[result[0]] = result[1]

    # JSON tobs dictionary
    return jsonify(tobs_dict)

@app.route("/api/v1.0/<start>")
def start_date(start):
    # Query for TMIN, TAVG, and TMAX for all dates greater than or equal to the start date
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")

    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
        .filter(Measurement.date >= start_date)\
        .all()

    # Create a dictionary 
    temp_dict = {'TMIN': results[0][0], 'TAVG': round(results[0][1], 2), 'TMAX': results[0][2]}

    # JSON temp dictionary
    return jsonify(temp_dict)


@app.route("/api/v1.0/<start>/<end>")
def start_end_date(start, end):
    # Query for TMIN, TAVG, and TMAX for dates between the start and end dates, inclusive
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")
    end_date = dt.datetime.strptime(end, "%Y-%m-%d")
    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
        .filter(Measurement.date >= start_date)\
        .filter(Measurement.date <= end_date)\
        .all()

    # Create a dictionary with the results
    temp_dict = {'TMIN': results[0][0], 'TAVG': round(results[0][1], 2), 'TMAX': results[0][2]}

    # Return the JSON representation of the dictionary
    return jsonify(temp_dict)
if __name__ == '__main__':
    app.run()

