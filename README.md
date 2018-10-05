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

## Database schema
```
                                       Table "addresses"
┌───────────────────────┬──────────────────────┬───────────┬──────────┬──────────────────────────────┐
│        Column         │         Type         │ Collation │ Nullable │           Default            │
├───────────────────────┼──────────────────────┼───────────┼──────────┼──────────────────────────────┤
│ kod_adm               │ integer              │           │ not null │ nextval('addresses_kod_adm_s…│
│                       │                      │           │          │…eq'::regclass)               │
│ obec_kod              │ integer              │           │          │                              │
│ obec_nazev            │ character varying    │           │          │                              │
│ momc_kod              │ integer              │           │          │                              │
│ momc_nazev            │ character varying    │           │          │                              │
│ mop_kod               │ integer              │           │          │                              │
│ mop_nazev             │ character varying    │           │          │                              │
│ cast_obce_kod         │ integer              │           │          │                              │
│ cast_obce_nazev       │ character varying    │           │          │                              │
│ ulice_kod             │ integer              │           │          │                              │
│ ulice_nazev           │ character varying    │           │          │                              │
│ typ_so                │ character varying    │           │          │                              │
│ cislo_domovni         │ integer              │           │          │                              │
│ cislo_orientacni      │ integer              │           │          │                              │
│ cislo_orientacni_znak │ character varying    │           │          │                              │
│ psc                   │ integer              │           │          │                              │
│ plati_od              │ date                 │           │          │                              │
│ geometry              │ geometry(Point,4326) │           │          │                              │
│ geometry_jtsk         │ geometry(Point,5514) │           │          │                              │
└───────────────────────┴──────────────────────┴───────────┴──────────┴──────────────────────────────┘
Indexes:
    "addresses_pkey" PRIMARY KEY, btree (kod_adm)
    "idx_addresses_geometry" gist (geometry)
    "idx_addresses_geometry_jtsk" gist (geometry_jtsk)
````

Viz [dokumentace k adresním bodům RUIAN](http://vdp.cuzk.cz/vymenny_format/csv/ad-csv-struktura.pdf)

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
