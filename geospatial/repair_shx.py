import os
from shapefile import (Reader, Writer)

try:  # Py2 (I haven't actually tested on python 2...)
    from StringIO import StringIO as IO
except ImportError:  # Py3
    from io import BytesIO as IO

def main(shp):
    shp, _ = os.path.splitext(shp)
    with IO() as shpio, IO() as dbfio:  # Don't overwrite existing .shp, .dbf
        with Reader(shp) as r, Writer(shp=shpio, dbf=dbfio, shx=shp+'.shx') as w:
            w.fields = r.fields[1:]  # skip first deletion field
            for rec in r.iterShapeRecords():
                w.record(*rec.record)
                w.shape(rec.shape)

if __name__ == '__main__':
    import sys
    main(sys.argv[1])
