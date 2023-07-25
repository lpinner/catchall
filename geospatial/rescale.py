"""
License is Apache 2.0
"""

def rescale(raster, out_min=0, out_max=1):
    arr_min, arr_max = raster.minimum, raster.maximum
    return out_min + ((((raster - arr_min)) * (out_max - out_min)) / (arr_max - arr_min))



if __name__ == '__main__':
    import arcpy
    raster = arcpy.Raster(arcpy.Describe(arcpy.GetParameter(0)).catalogPath)
    out_min = arcpy.GetParameter(1)
    out_max = arcpy.GetParameter(2)
    out_raster = arcpy.GetParameterAsText(3)

    raster = rescale(raster, out_min, out_max)
    raster.save(out_raster)
