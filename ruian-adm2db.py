#!/usr/bin/env python3

"""
Script for loading latest RUIAN administrative areas to database


Description:

    Database can be PostgreSQL with PostGIS extension or SQLite / Spatialite
    file database.


Dependencies:

    pip install sqlalchemy geoalchemy2 shapely pyproj requests


Author:

    Jachym Cepicky <jachym.cepicky opengeolabs cz>
    http://opengeolabs.cz

Developed with support and for needs of CzechInvest.org

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
import logging
import os
import csv
import requests
import datetime
from calendar import monthrange
import tempfile
from zipfile import ZipFile
import gdaltools
import atexit
import shutil

ZSJ_URL = 'https://vdp.cuzk.cz/vymenny_format/soucasna/{date}_ST_UKSH.xml.zip'
OBCE_CISELNIK = 'https://www.cuzk.cz/CUZK/media/CiselnikyISUI/UI_OBEC/UI_OBEC.zip?ext=.zip'
OBEC_URL = 'https://vdp.cuzk.cz/vymenny_format/soucasna/{date}_OB_{kod}_UKSH.xml.zip'

TO_BE_REMOVED = []

logger = logging.getLogger('RUIAN2DB')
logger.setLevel(logging.INFO)


@atexit.register
def clear():
    global TO_BE_REMOVED

    for mydir in TO_BE_REMOVED:
        print(f"removing {mydir}")
        shutil.rmtree(mydir)


def _get_date():

    now = datetime.datetime.now()
    month = now.month-1
    year = now.year
    if month == 0:
        month = 12
        year = now.year - 1
    days = monthrange(year=year, month=month)
    return "{}{:02d}{}".format(year, month, days[1])


def get_data(url, pref="obce"):

    global TO_BE_REMOVED
    out_dir_name = tempfile.mkdtemp(prefix=pref)
    out_temp_name = tempfile.mktemp(dir=out_dir_name, suffix=".zip")
    TO_BE_REMOVED.append(out_dir_name)

    with open(out_temp_name, "wb") as out_zip:
        r = requests.get(url, stream=True)
        for chunk in r.iter_content(8192):
            out_zip.write(chunk)

    with ZipFile(out_temp_name, "r") as myzip:
        myzip.extractall(path=out_dir_name)

    return out_dir_name


def get_obce_cislenik():

    url = OBCE_CISELNIK
    dir_name = get_data(url, "obce")
    data = []
    with open(os.path.join(dir_name, "UI_OBEC.csv"), encoding='windows-1250') as obce:
        obecreader = csv.reader(obce, delimiter=";")
        header = True
        for row in obecreader:
            if header:
                header = False
                continue
            if len(row) == 10:
                (
                    kod, nazev, status, pou, okres, sm_rozsah,
                    sm_typ, platne_od, platne_do, datum
                ) = row

                data.append(
                    {
                            "kod": kod,
                            "nazev": nazev,
                            "status": status,
                            "pou": pou,
                            "okres": okres,
                            "sm_rozsah": sm_rozsah,
                            "sm_typ": sm_typ,
                            "platne_od": platne_od,
                            "platne_do": platne_do,
                            "datum": datum
                    }
                )
    return data


def get_data_zsj(url, pref, zipfile=None):
    """Download fresh data from CUZK server - always last day of previous month
    """

    global logger

    last_day = _get_date()
    url = ZSJ_URL.format(date=last_day)

    if not zipfile:
        logger.info('Downloading data')
        out_dir_name = get_data(url, pref)
        data_file = f"{last_day}_ST_UKSH.xml"
        out_temp_name = os.path.join(out_dir_name, data_file)
    else:
        logger.info(f'Using existing zipfile [{zipfile}]')
        out_temp_name = zipfile

    return out_temp_name


def get_obec_file(kod):
    """Download fresh data from CUZK server - always last day of previous month
    """

    global logger

    last_day = _get_date()
    url = OBEC_URL.format(date=last_day, kod=kod)
    out_dir_name = get_data(url, "obec")
    data_file = f"{last_day}_OB_{kod}_UKSH.xml"
    output_file_name = os.path.join(out_dir_name, data_file)
    return output_file_name


def myint(number):
    """Convert to integer, None otherwice
    """
    try:
        return int(number)
    except ValueError as e:
        return None


def _get_connection(connection):

    connection = connection.replace("PG:", "").strip()

    data = {}

    for kv in connection.split(" "):
        k, v = kv.split("=")
        data[k] = v

    return data


def import_zsj(connection, schema, zipfile, kraje=False, vusc=False,
        okresy=False, orp=False, pou=False):

    global logger
    zsj_file_name = get_data_zsj(ZSJ_URL, "zsj", zipfile)
    connection_params = _get_connection(connection)
    if schema:
        connection_params["schema"] = schema

    ogr = gdaltools.ogr2ogr()
    ogr.set_output_mode(
            data_source_mode=ogr.MODE_DS_CREATE_OR_UPDATE,
            layer_mode=ogr.MODE_LAYER_OVERWRITE
    )
    conn = gdaltools.PgConnectionString(**connection_params)

    if kraje:
        logger.info('Importing kraje')
        ogr.set_input(zsj_file_name, table_name="Kraje")
        ogr.set_output(conn, table_name="kraje", srs="EPSG:5514")
        ogr.execute()

    if vusc:
        logger.info('Importing vusc')
        ogr.set_input(zsj_file_name, table_name="Vusc")
        ogr.set_output(conn, table_name="vusc", srs="EPSG:5514")
        ogr.execute()

    if okresy:
        logger.info('Importing okresy')
        ogr.set_input(zsj_file_name, table_name="Okresy")
        ogr.set_output(conn, table_name="okresy", srs="EPSG:5514")
        ogr.execute()

    if orp:
        logger.info('Importing orp')
        ogr.set_input(zsj_file_name, table_name="Orp")
        ogr.set_output(conn, table_name="orp", srs="EPSG:5514")
        ogr.execute()

    if pou:
        logger.info('Importing pou')
        ogr.set_input(zsj_file_name, table_name="Pou")
        ogr.set_output(conn, table_name="pou", srs="EPSG:5514")
        ogr.execute()


def import_obce(connection, schema, obec=False, ku=False, casti_obci=False, ulice=False,
        casti_obci=False, parcely=False, stav_objekty=False, adresy=False):

    global logger

    connection_params = _get_connection(connection)
    if schema:
        connection_params["schema"] = schema

    ogr = gdaltools.ogr2ogr()
    ogr.set_output_mode(
        data_source_mode=ogr.MODE_DS_CREATE_OR_UPDATE,
        layer_mode=ogr.MODE_LAYER_OVERWRITE
    )
    conn = gdaltools.PgConnectionString(**connection_params)

    obce_cislenik = get_obce_cislenik()
    for obec in obce_cislenik:
        if not obec["platne_do"]:
            kod = obec["kod"]
            obec_file = get_obec_file(kod)

            logger.info(f"Importing obec {obec['kod']} - {obec['nazev']}")

            if obec:
                ogr.set_input(obec_file, table_name="Obce")
                ogr.set_output(conn, table_name="obce", srs="EPSG:5514")
                ogr.execute()

            if ku:
                ogr.set_input(obec_file, table_name="KatastralniUzemi")
                ogr.set_output(conn, table_name="katastralni_uzemi", srs="EPSG:5514")
                ogr.execute()

            if casti_obci:
                ogr.set_input(obec_file, table_name="Ulice")
                ogr.set_output(conn, table_name="CastiObci", srs="EPSG:5514")
                ogr.execute()

            if ulice:
                ogr.set_input(obec_file, table_name="Ulice")
                ogr.set_output(conn, table_name="ulice", srs="EPSG:5514")
                ogr.execute()

            if parcely:
                ogr.set_input(obec_file, table_name="Parcely")
                ogr.set_output(conn, table_name="parcely", srs="EPSG:5514")
                ogr.execute()

            if stav_objekty:
                ogr.set_input(obec_file, table_name="StavebniObjekty")
                ogr.set_output(conn, table_name="stavebni_objekty", srs="EPSG:5514")
                ogr.execute()

            if adresy:
                ogr.set_input(obec_file, table_name="AdresniMista")
                ogr.set_output(conn, table_name="adresni_mista", srs="EPSG:5514")
                ogr.execute()

            # from now on, just append
            ogr.set_output_mode(
                data_source_mode=ogr.MODE_DS_CREATE_OR_UPDATE,
                layer_mode=ogr.MODE_LAYER_APPEND
            )


def main(connection, schema=None, verbose=False, zipfile=None,
        kraje=False, vusc=False, okresy=False, orp=False, pou=False,
        obec=False, ku=False, casti_obci=False, ulice=False, parcely=False, stav_objekty=False,
        adresy=False):

    global logger

    if kraje or vusc or okresy or orp or pou:
        import_zsj(connection, schema, zipfile,
                kraje, vusc, okresy, orp, pou)

    if obec or ku or casti_obci or ulice or parcely or stav_objekty or adresy:
        import_obce(connection, schema, obec, ku, casti_obci, ulice,
                parcely, stav_objekty, adresy)

def parse_args():
    parser = argparse.ArgumentParser(
        description='Import address points from RUIAN to PostgreSQL database'
    )
    parser.add_argument('-v', action='store_true', help='Verbose')
    parser.add_argument('-kr', action='store_true', help='Naimportovat kraje')
    parser.add_argument('-vc', action='store_true', help='Naimportovat vyšší celky')
    parser.add_argument('-ok', action='store_true', help='Naimportovat okresy')
    parser.add_argument('-op', action='store_true', help='Naimportovat ORP')
    parser.add_argument('-pu', action='store_true', help='Naimportovat POU')
    parser.add_argument('-ob', action='store_true', help='Naimportovat obce')
    parser.add_argument('-ku', action='store_true', help='Naimportovat katastrální území')
    parser.add_argument('-co', action='store_true', help='Naimportovat části obcí')
    parser.add_argument('-ul', action='store_true', help='Naimportovat ulice')
    parser.add_argument('-pa', action='store_true', help='Naimportovat parcely')
    parser.add_argument('-so', action='store_true', help='Naimportovat stavební objekty')
    parser.add_argument('-ad', action='store_true', help='Naimportovat adresni mista')

    parser.add_argument('--connection', required=True,
            help='OGR Postgres Connection string https://gdal.org/drivers/vector/pg.html')
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

    main(args.connection, args.schema, args.v, args.input,
            args.kr, args.vc, args.ok, args.op, args.pu,
            args.ob, args.ku, args.co, args.ul, args.pa, args.so, args.ad)
