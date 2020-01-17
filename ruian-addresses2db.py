#!/usr/bin/env python3

"""
Script for loading latest RUIAN address points to database


Description:

    Database can be PostgreSQL with PostGIS extension or SQLite / Spatialite
    file database.


Dependencies:

    pip install sqlalchemy geoalchemy2 shapely pyproj requests


Author:

    Jachym Cepicky <jachym.cepicky opengeolabs cz>
    http://opengeolabs.cz


License:

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

import argparse
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date
from geoalchemy2 import Geometry
from sqlalchemy.orm import sessionmaker
import os
import csv
from shapely.wkt import loads
from shapely.ops import transform
import pyproj
from functools import partial
import requests
import datetime
from calendar import monthrange
import tempfile
from zipfile import ZipFile
from sqlalchemy.event import listen

DATA_URL = 'http://vdp.cuzk.cz/vymenny_format/csv/{}_OB_ADR_csv.zip'
Base = declarative_base()


class Address(Base):
    """Address class - one to one copy of input CSV file structure according to
    RUIAN documentation
    http://vdp.cuzk.cz/vymenny_format/csv/ad-csv-struktura.pdf
    """

    __tablename__ = 'addresses'
    kod_adm = Column(Integer, primary_key=True)
    obec_kod = Column(Integer)
    obec_nazev = Column(String)
    momc_kod = Column(Integer, nullable=True)
    momc_nazev = Column(String, nullable=True)
    mop_kod = Column(Integer, nullable=True)
    mop_nazev = Column(String, nullable=True)
    cast_obce_kod = Column(Integer, nullable=True)
    cast_obce_nazev = Column(String, nullable=True)
    ulice_kod = Column(Integer, nullable=True)
    ulice_nazev = Column(String, nullable=True)
    typ_so = Column(String)
    cislo_domovni = Column(Integer, nullable=True)
    cislo_orientacni = Column(Integer, nullable=True)
    cislo_orientacni_znak = Column(String)
    psc = Column(Integer)
    plati_od = Column(Date)
    geometry = Column(Geometry('POINT', srid=4326))
    geometry_jtsk = Column(Geometry('POINT', srid=5514))


def get_data(zipfile=None):
    """Download fresh data from CUZK server - always last day of previous month
    """

    now = datetime.datetime.now()
    month = now.month - 1
    year = now.year
    if month == 0:
        month = 12
    if month == 12:
        year = year - 1
    days = monthrange(year=year, month=month)
    date_name = "{}{:02d}{}".format(year, month, days[1])
    url = DATA_URL.format(date_name)
    out_dir_name = tempfile.mkdtemp(prefix="addresses")
    out_temp_name = tempfile.mktemp(dir=out_dir_name, suffix=".zip")

    if not zipfile:
        with open(out_temp_name, "wb") as out_zip:
            print(url)
            r = requests.get(url, stream=True)
            for chunk in r.iter_content(8192):
                out_zip.write(chunk)

    else:
        out_temp_name = zipfile

    with ZipFile(out_temp_name, "r") as myzip:
        myzip.extractall(path=out_dir_name)

    return os.path.join(out_dir_name, "CSV")


def myint(number):
    """Convert to integer, None otherwice
    """
    try:
        return int(number)
    except ValueError as e:
        return None


def get_engine(connection, verbose=False):
    """Create database engine - do some extra tuning for SpatiaLite
    """

    sqlite = connection.find("sqlite") == 0
    so = '/usr/lib/x86_64-linux-gnu/mod_spatialite.so'

    if sqlite:
        def load_spatialite(dbapi_conn, connection_record):
            dbapi_conn.enable_load_extension(True)
            if so:
                dbapi_conn.load_extension(so)
            else:
                raise Exception("File {} not found: ".format(so) +
                                "Spatialite not supported")

    engine = create_engine(connection, echo=verbose)

    if sqlite:
        listen(engine, 'connect', load_spatialite)

    return engine


def main(connection, schema=None, verbose=False, zipfile=None):

    engine = get_engine(connection, verbose)
    if schema:
        Address.__table__.schema = schema

    if engine.dialect.has_table(engine, "addresses", schema=schema):
        Address.__table__.drop(engine)

    Address.__table__.create(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    epsg4326 = pyproj.Proj(init="epsg:4326")
    epsg5514 = pyproj.Proj(
        "+proj=krovak +lat_0=49.5 +lon_0=24.83333333333333 "
        "+alpha=30.28813972222222 +k=0.9999 +x_0=0 +y_0=0 +ellps=bessel "
        "+pm=greenwich +units=m +no_defs "
        "+towgs84=570.8,85.7,462.8,4.998,1.587,5.261,3.56")

    project = partial(pyproj.transform, epsg5514, epsg4326)

    data = []

    src_dir = get_data(zipfile)

    for f in os.listdir(src_dir):
        f = os.path.join(src_dir, f)

        with open(f, encoding="windows-1250", errors="ignore") as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            next(reader, None)
            for row in reader:
                (kod_adm, obec_kod, obec_nazev, momc_kod, momc_nazev, mop_kod,
                 mop_nazev, cast_obce_kod, cast_obce_nazev, ulice_kod,
                 ulice_nazev, typ_so, cislo_domovni, cislo_orientacni,
                 cislo_orientacni_znak, psc, Y, X, plati_od) = row

                if not X and not Y:
                    continue

                X = float(X)*-1
                Y = float(Y)*-1

                geometry = loads('POINT({} {})'.format(Y, X))
                geometry_wgs = transform(project, geometry)

                new_address = Address(
                    kod_adm=myint(kod_adm), obec_kod=myint(obec_kod),
                    obec_nazev=obec_nazev, momc_kod=myint(momc_kod),
                    momc_nazev=momc_nazev, mop_kod=myint(mop_kod),
                    mop_nazev=mop_nazev, cast_obce_kod=myint(cast_obce_kod),
                    cast_obce_nazev=cast_obce_nazev,
                    ulice_kod=myint(ulice_kod),
                    ulice_nazev=ulice_nazev, typ_so=typ_so,
                    cislo_domovni=myint(cislo_domovni),
                    cislo_orientacni=myint(cislo_orientacni),
                    cislo_orientacni_znak=cislo_orientacni_znak,
                    psc=psc, plati_od=plati_od,
                    geometry="SRID=4326;{}".format(geometry_wgs.to_wkt()),
                    geometry_jtsk="SRID=5514;{}".format(geometry.to_wkt())
                )

                data.append(new_address)
                if len(data) == 10000:
                    session.add_all(data)
                    session.commit()
                    data = []
    if len(data) > 0:
        session.add_all(data)
        session.commit()
        data = []


def parse_args():
    parser = argparse.ArgumentParser(
        description='Import address points from RUIAN to PostgreSQL database'
    )
    parser.add_argument('-v', action='store_true', help='Verbose')
    parser.add_argument('--connection', required=True,
                        help='Connection string to the database (sqlalchemy)')
    parser.add_argument('--schema',
                        default=None,
                        help='Database schema')
    parser.add_argument('--input',
                        default=None,
                        help='Input ZIP file')

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    args = parse_args()

    main(args.connection, args.schema, args.v, args.input)
