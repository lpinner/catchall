"""
Calculate path distance from an ArcGIS least cost backlink raster

I wrote this before I discovered the flow length tool does the same thing if you convert the backlink raster
to a flow direction raster `flowdir = Int(0.5 * 2 ** backlink)`

However... this is significantly faster than the ArcGIS tool: for a 250m raster covering continental Australia (18500*16500 pixels) 
this script takes ~1min, while the ArcGIS FlowLength tool takes >15min, not including the time to calculate the flow direction raster. 
Although ArcGIS can process larger rasters as it doesn't read the whole thing into memory.

License is Apache 2.0

"""
import rasterio, numpy, numba


@numba.jit(nopython=True, nogil=True, parallel=True, fastmath=True)
def _path_distance(arr, output, nodata, multiplier=1.0):
    for row in range(arr.shape[0]):
        for col in range(arr.shape[1]):
            idx = start_idx = row, col
            path = arr[idx].item()
            i = 0
            dist = 0.0
            # print(i, path, dist)
            while i < 10000:
                if path == 0:
                    break
                elif path == nodata:
                    dist = -1.0
                    break
                elif path % 2 == 1:  # Odd = up/down/left/right
                    dist += (1 * multiplier)
                    if path == 1:  # Right (1)
                        idx = idx[0], idx[1] + 1
                    elif path == 3:  # Down
                        idx = idx[0] + 1, idx[1]
                    elif path == 5:  # Left
                        idx = idx[0], idx[1] - 1
                    elif path == 7:  # Up
                        idx = idx[0] - 1, idx[1]

                else:  # Even = diagonal
                    dist += (2.0 ** 0.5 * multiplier)
                    if path == 2:  # LR
                        idx = idx[0] + 1, idx[1] + 1
                    elif path == 4:  # LL
                        idx = idx[0] + 1, idx[1] - 1
                    elif path == 6:  # UL
                        idx = idx[0] - 1, idx[1] - 1
                    elif path == 8:  # UR
                        idx = idx[0] - 1, idx[1] + 1

                path = arr[idx].item()
                i += 1
            output[start_idx] = dist

        if row % 100 == 0:
            print(row)


def path_distance(backlink_raster, output_raster):

    with rasterio.open(backlink_raster) as ras:
        md = ras.profile
        arr = ras.read().squeeze()
        nodata = md['nodata']
        res = ras.res[0]  # Cellsize, assumes square pixels

    md['dtype'] = 'float32'
    md['nodata'] = -1
    output = numpy.zeros(arr.shape, dtype=md['dtype'])

    _path_distance(arr, output, nodata, res)

    with rasterio.open(output_raster, mode='w', **md) as ras:
        ras.write(output[numpy.newaxis])


if __name__ == '__main__':
    import sys
    path_distance(sys.argv[1:))  #Expects sys.argv[1:] == backlink_raster, output_raster
