"""
ArcGIS Pro Python Script Tool to convert a Feature Class to KML
that uses GDAL instead of ArcGIS so the output KML keeps its
attributes as ExtendedData/SchemaData/SimpleData elements
instead of dumping them as HTML into the description element.

Parameters:
    Label            Name   Data Type     Type     Direction Filter
    In Feature Class in_fc  Feature Class Required Input
    Output KML       out_kml File         Required Output    File (kml)
"""

# Copyright 2019 Luke Pinner
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
import arcpy
from osgeo import gdal


def callback(complete, message, *args, **kwargs):
    if bool(message):
        arcpy.AddMessage(message)
    arcpy.SetProgressorPosition(int(complete * 100))


if __name__ == '__main__':
    gdal.UseExceptions()

    in_fc = arcpy.GetParameterAsText(0)
    out_kml = arcpy.GetParameterAsText(1)
    lyr = None

    arcpy.SetProgressor("step", "Exporting features to KML...", 0, 100, 1)

    if '.gdb' in in_fc:  # FileGDB FeatureClass
        in_fc = Path(in_fc)
        lyr = in_fc.name
        in_fc = in_fc.parent

        if not in_fc.name.endswith('.gdb'):  # inside a Feature Dataset
            lyr = '{}\\{}'.format(in_fc.name, lyr)
            in_fc = in_fc.parent

        in_fc = str(in_fc)

    ds = gdal.OpenEx(in_fc, gdal.OF_VECTOR)

    vto = gdal.VectorTranslateOptions(format='KML', datasetCreationOptions=['NameField=None'],
                                      layers=lyr, callback=callback)
    gdal.VectorTranslate(out_kml, ds, options=vto)
