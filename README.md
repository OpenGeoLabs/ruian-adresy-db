# RUIAN Adresní body do databáze

Skript pro import [adresních bodů RUIAN](https://nahlizenidokn.cuzk.cz/stahniadresnimistaruian.aspx) do databáze [PostgreSQL](http://postgresql.org)/[PostGIS](http://postgis.org) a [SQLite](http://sqlite.org)/[Spatialite](https://www.gaia-gis.it/fossil/libspatialite/index).

## Instalace a závislosti

Skript využívá [SQLalchemy](https://www.sqlalchemy.org/) a
[GeoAlchemy2](https://geoalchemy-2.readthedocs.io/en/latest/),
[PyProj](https://pypi.org/project/pyproj/) a
[Shapely](https://pypi.org/project/Shapely/). Skript je napsán pro Python3.

```
pip install requirements.txt
```

## Použití

```
ruian-addresses2db.py [-h] [-v] --connection CONNECTION [--schema SCHEMA]
```

### PostgreSQL

#### Vytvoření databáze

```
$ createdb adresy
$ psql adresy

adresy=> CREATE EXTENSION postgis;
adresy=> CREATE SCHEMA adresy;
adresy=> \q
```

#### Import adres

```
ruian-adressses2db.py --connection "postgresql://uzivatel:heselo@localhost:5432/adresy" \
                      --schema adresy
```

### SQLite

Je potřeba mít nainstalovanou nadstavbu
[Spatialite](https://www.gaia-gis.it/fossil/libspatialite/index) a natvrdo je
předpokládáno, že existuje soubor `/usr/lib/x86_64-linux-gnu/mod_spatialite.so`

```
ruian-adressses2db.py --connection "sqlite:///adresy.sqlite"
```

## Licence

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

## Autoři

Jáchym Čepicky `jachym.cepicky opengeolabs.cz`

[OpenGeoLabs s.r.o.](http://opengeolabs.cz)
