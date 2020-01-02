# RUIAN do databáze

Sada skriptů pro import [adresních bodů RUIAN](https://nahlizenidokn.cuzk.cz/stahniadresnimistaruian.aspx) a územních jednotek z [veřejného dálkového přístupu](https://vdp.cuzk.cz/vdp/ruian/vymennyformat/vyhledej) (Kraje, Obce, ...)
do databáze [PostgreSQL](http://postgresql.org)/[PostGIS](http://postgis.org) ~~a [SQLite](http://sqlite.org)/[Spatialite](https://www.gaia-gis.it/fossil/libspatialite/index)~~.

## Instalace a závislosti

Skripty využívají [SQLalchemy](https://www.sqlalchemy.org/) a
[GeoAlchemy2](https://geoalchemy-2.readthedocs.io/en/latest/),
[gdaltools](https://pypi.org/project/pygdaltools/),
[PyProj](https://pypi.org/project/pyproj/) a
[Shapely](https://pypi.org/project/Shapely/). Skript je napsán pro Python3.

```
pip install requirements.txt
```

## Použití - Import adres

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

#### Nastavení souř. systému

Pro správné fungování je potřeba nastavit souř. systém S-JTSK s transformačními
parametry `towgs84`:

```
INSERT into spatial_ref_sys (srid, auth_name, auth_srid, proj4text, srtext)
values ( 5514, 'EPSG', 5514,
'+proj=krovak +lat_0=49.5 +lon_0=24.83333333333333 +alpha=30.28813972222222 +k=0.9999 +x_0=0 +y_0=0 +ellps=bessel +towgs84=570.8,85.7,462.8,4.998,1.587,5.261,3.56 +units=m +no_defs ',
'PROJCS["S-JTSK / Krovak East North",GEOGCS["S-JTSK",DATUM["System_Jednotne_Trigonometricke_Site_Katastralni",SPHEROID["Bessel 1841",6377397.155,299.1528128,AUTHORITY["EPSG","7004"]],TOWGS84[570.8,85.7,462.8,4.998,1.587,5.261,3.56],AUTHORITY["EPSG","6156"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4156"]],PROJECTION["Krovak"],PARAMETER["latitude_of_center",49.5],PARAMETER["longitude_of_center",24.83333333333333],PARAMETER["azimuth",30.28813972222222],PARAMETER["pseudo_standard_parallel_1",78.5],PARAMETER["scale_factor",0.9999],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],AUTHORITY["EPSG","5514"]]');
```

nebo

```
UPDATE spatial_ref_sys set proj4text='+proj=krovak +lat_0=49.5 +lon_0=24.83333333333333 +alpha=30.28813972222222 +k=0.9999 +x_0=0 +y_0=0 +ellps=bessel +towgs84=570.8,85.7,462.8,4.998,1.587,5.261,3.56 +units=m +no_defs '
srtext='PROJCS["S-JTSK / Krovak East North",GEOGCS["S-JTSK",DATUM["System_Jednotne_Trigonometricke_Site_Katastralni",SPHEROID["Bessel
1841",6377397.155,299.1528128,AUTHORITY["EPSG","7004"]],TOWGS84[570.8,85.7,462.8,4.998,1.587,5.261,3.56],AUTHORITY["EPSG","6156"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4156"]],PROJECTION["Krovak"],PARAMETER["latitude_of_center",49.5],PARAMETER["longitude_of_center",24.83333333333333],PARAMETER["azimuth",30.28813972222222],PARAMETER["pseudo_standard_parallel_1",78.5],PARAMETER["scale_factor",0.9999],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],AUTHORITY["EPSG","5514"]]'
where srid = 5514;
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
```

Viz [dokumentace k adresním bodům RUIAN](http://vdp.cuzk.cz/vymenny_format/csv/ad-csv-struktura.pdf)

## Použití - Import Krajů, Okresů, ORP, POÚ a Obcí

**Poznámka:** Funguje pouze nad PostgreSQL/PostGIS

Data jsou importována do tabulek `kraje`, `orp`, `okresy`, `pou` a `obce`. Při
každém importu jsou stažena čerstvá data z databáze RUIAN a původní data jsou
přemazána (čistý import). Výsledná data obsahují hranice územních jednotek
pouze  v souř. systému S-JTSK.

```
python3 ruian-adm2db.py --connection "host=localhost user=user dbname=ruian port=5432 password=XXXXXX"

```

Parametr `connection` odpovídá textovému řetězci pro použití v [knihovně GDAL](https://gdal.org/drivers/vector/pg.html).

### Po importu

Je dobré vytvořit prostorové indexy a provézt příkaz `VACUUM ANALYZE` pro lepší
uspořádání dat.

```
CREATE INDEX kraje_geom_idx ON kraje USING GIST (originalnihranice);
CREATE INDEX okresy_geom_idx ON okresy USING GIST (originalnihranice);
CREATE INDEX orp_geom_idx ON orp USING GIST (originalnihranice);
CREATE INDEX pou_geom_idx ON pou USING GIST (originalnihranice);
CREATE INDEX obce_geom_idx ON obce USING GIST (originalnihranice);
VACUUM ANALYZE;
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
