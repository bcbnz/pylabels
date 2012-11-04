# This file is part of pylabels, a Python library to create PDFs for printing
# labels.
# Copyright (C) 2012 Blair Bonnett
#
# pylabels is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# pylabels is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# pylabels.  If not, see <http://www.gnu.org/licenses/>.

class InvalidDimension(ValueError):
    """Raised when a sheet specification has inconsistent dimensions. """
    pass

def create(sheet_width, sheet_height, num_columns, num_rows, label_width,
           label_height, **kwargs):
    """Create a set of specifications for a single sheet. All dimensions are
    given in millimetres.

    The following arguments are required and cannot be less than one:

    sheet_width: width of the sheet.
    sheet_height: height of the sheet.
    num_columns: number of columns of labels on the sheet.
    num_rows: number of rows of labels on the sheet.
    label_width: width of each label.
    label_height: height of each label.

    The following margins can be manually specified:

    left_margin: gap between the left edge of the sheet and the first column.
    column_gap: internal gap between columns.
    right_margin: gap between the right edge of the sheet and the last column.
    top_margin: gap between the top edge of the sheet and the first row.
    row_gap: internal gap between rows.
    bottom_margin: gap between the bottom edge of the sheet and the last row.

    If any of these margins are not given, then any remaining space is divided
    equally amongst them. If all the width or all the height margins are given,
    they must exactly use up any space.

    The following additional dimensions can be specified:

    corner_radius: gives the label rounded corners with the given radius.

    If any given dimension is invalid (i.e., it means the labels cannot fit on
    the sheet) then an InvalidDimension exception will be raised with the
    dimension that caused the problem.

    """
    # Pull out the basic details.
    spec = {
        'sheet_width': float(sheet_width),
        'sheet_height': float(sheet_height),
        'num_columns': int(num_columns),
        'num_rows': int(num_rows),
        'label_width': float(label_width),
        'label_height': float(label_height),
    }

    # Check the values are positive.
    for key, value in spec.items():
        if value < 1:
            raise InvalidDimension("{0:s} must be positive.".format(key))

    # Check the amount of space left in each dimension.
    wspace = spec['sheet_width'] - (spec['label_width'] * spec['num_columns'])
    if wspace < 0:
        raise InvalidDimension("Labels are too wide to fit on the sheet.")
    hspace = spec['sheet_height'] - (spec['label_height'] * spec['num_rows'])
    if hspace < 0:
        raise InvalidDimension("Labels are too tall to fit on the sheet.")

    # How many ways we have to divide available space for unspecified margins.
    wdiv = 2 + (spec['num_columns'] - 1)
    hdiv = 2 + (spec['num_rows'] - 1)

    # Check the margins are not negative.
    for key, value in kwargs.items():
        if value < 0:
            raise InvalidDimension("{0:s} cannot be negative.".format(key))

    # Check any given margins for the width.
    if 'left_margin' in kwargs:
        spec['left_margin'] = float(kwargs['left_margin'])
        wspace -= spec['left_margin']
        if wspace < 0:
            raise InvalidDimension("Left margin is too wide.")
        wdiv -= 1
    if 'column_gap' in kwargs:
        spec['column_gap'] = float(kwargs['column_gap'])
        wspace -= (spec['column_gap'] * (spec['num_columns'] - 1))
        if wspace < 0:
            raise InvalidDimension("Column gap is too wide.")
        wdiv -= (spec['num_columns'] - 1)
    if 'right_margin' in kwargs:
        spec['right_margin'] = float(kwargs['right_margin'])
        wspace -= spec['right_margin']
        if wspace < 0:
            raise InvalidDimension("Right margin is too wide.")
        wdiv -= 1

    # And again for the height.
    if 'top_margin' in kwargs:
        spec['top_margin'] = float(kwargs['top_margin'])
        hspace -= spec['top_margin']
        if hspace < 0:
            raise InvalidDimension("Top margin is too tall.")
        hdiv -= 1
    if 'row_gap' in kwargs:
        spec['row_gap'] = float(kwargs['row_gap'])
        hspace -= (spec['row_gap'] * (spec['num_rows'] - 1))
        if hspace < 0:
            raise InvalidDimension("Row gap is too tall.")
        hdiv -= (spec['num_rows'] - 1)
    if 'bottom_margin' in kwargs:
        spec['bottom_margin'] = float(kwargs['bottom_margin'])
        hspace -= spec['bottom_margin']
        if hspace < 0:
            raise InvalidDimension("Bottom margin is too tall.")
        hdiv -= 1

    # All margins specified but space left over.
    if wdiv == 0 and wspace != 0:
        raise InvalidDimension("Not all width used by manually specified dimensions.")
    if hdiv == 0 and hspace != 0:
        raise InvalidDimension("Not all height used by manual specified dimensions.")

    # Allocate any automatically sized margins.
    if wdiv > 0:
        autow = wspace / wdiv
        spec['left_margin'] = spec.get('left_margin', autow)
        spec['column_gap'] = spec.get('column_gap', autow)
        spec['right_margin'] = spec.get('right_margin', autow)
    if hdiv > 0:
        autoh = hspace / hdiv
        spec['top_margin'] = spec.get('top_margin', autoh)
        spec['row_gap'] = spec.get('row_gap', autoh)
        spec['bottom_margin'] = spec.get('bottom_margin', autoh)

    # Check additional properties.
    if 'corner_radius' in kwargs:
        corner_radius = float(kwargs['corner_radius'])
        if corner_radius < 0:
            raise InvalidDimension("Corner radius cannot be less than zero.")
        if corner_radius > (spec["label_width"] / 2):
            raise InvalidDimension("Corner radius cannot be more than half the label width.")
        if corner_radius > (spec["label_height"] / 2):
            raise InvalidDimension("Corner radius cannot be more than half the label height.")
        spec['corner_radius'] = corner_radius
    else:
        spec['corner_radius'] = None

    # Done.
    return spec
