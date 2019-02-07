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

from itertools import product
import rasterio as rio
from rasterio import windows


def overlapping_tiles(src, overlap, width, height, boundless=False):
    """"width & height not including overlap i.e requesting a 256x256 window with 
        1px overlap will return a 258x258 window (for non edge windows)"""
    offsets = product(range(0, src.meta['width'], width), range(0, src.meta['height'], height))
    big_window = windows.Window(col_off=0, row_off=0, width=src.meta['width'], height=src.meta['height'])
    for col_off, row_off in offsets:

        window = windows.Window(
            col_off=col_off - overlap,
            row_off=row_off - overlap,
            width=width + overlap * 2,
            height=height + overlap * 2)

        if boundless:
            yield window
        else:
            yield window.intersection(big_window)


def overlapping_blocks(src, overlap=0, band=1, boundless=False):

    big_window = windows.Window(col_off=0, row_off=0, width=src.meta['width'], height=src.meta['height'])
    for ji, window in src.block_windows(band):

        if overlap == 0:
            yield window

        else:
            window = windows.Window(
                col_off=window.col_off - overlap,
                row_off=window.row_off - overlap,
                width=window.width + overlap * 2,
                height=window.height + overlap * 2)
            if boundless:
                yield window
            else:
                yield window.intersection(big_window)
