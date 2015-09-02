# This file is part of pylabels, a Python library to create PDFs for printing
# labels.
# Copyright (C) 2012, 2013, 2014, 2015 Blair Bonnett
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

from decimal import Decimal
import json


class InvalidDimension(ValueError):
    """Raised when a sheet specification has inconsistent dimensions. """
    pass


class Specification(object):
    """Specification for a sheet of labels.

    All dimensions are given in millimetres. If any of the margins are not
    given, then any remaining space is divided equally amongst them. If all the
    width or all the height margins are given, they must exactly use up all
    non-label space on the sheet.

    """
    def __init__(self, sheet_width, sheet_height, columns, rows, label_width, label_height, **kwargs):
        """
        Required parameters
        -------------------
        sheet_width, sheet_height: positive dimension
            The size of the sheet.

        columns, rows: positive integer
            The number of labels on the sheet.

        label_width, label_size: positive dimension
            The size of each label.

        Margins and gaps
        ----------------
        left_margin: positive dimension
            The gap between the left edge of the sheet and the first column.
        column_gap: positive dimension
            The internal gap between columns.
        right_margin: positive dimension
            The gap between the right edge of the sheet and the last column.
        top_margin: positive dimension
            The gap between the top edge of the sheet and the first row.
        row_gap: positive dimension
            The internal gap between rows.
        bottom_margin: positive dimension
            The gap between the bottom edge of the sheet and the last row.

        Padding
        -------
        left_padding, right_padding, top_padding, bottom_padding: positive dimensions, default 0
            The padding between the edges of the label and the area available
            to draw on.

        Corners
        ---------------------
        corner_radius: positive dimension, default 0
            Gives the labels rounded corners with the given radius.
        padding_radius: positive dimension, default 0
            Give the drawing area rounded corners. If there is no padding, this
            must be set to zero.

        Background
        ----------
        background_image: reportlab.graphics.shape.Image
            An image to use as the background to the page. This will be
            automatically sized to fit the page; make sure it has the correct
            aspect ratio.
        background_filename: string
            Filename of an image to use as a background to the page. If both
            this and background_image are given, then background_image will
            take precedence.

        Raises
        ------
        InvalidDimension
            If any given dimension is invalid (i.e., the labels cannot fit on
            the sheet).

        """
        # Compulsory arguments.
        self._sheet_width = Decimal(sheet_width)
        self._sheet_height = Decimal(sheet_height)
        self._columns = int(columns)
        self._rows = int(rows)
        self._label_width = Decimal(label_width)
        self._label_height = Decimal(label_height)

        # Optional arguments; missing ones will be computed later.
        self._left_margin = kwargs.pop('left_margin', None)
        self._column_gap = kwargs.pop('column_gap', None)
        self._right_margin = kwargs.pop('right_margin', None)
        self._top_margin = kwargs.pop('top_margin', None)
        self._row_gap = kwargs.pop('row_gap', None)
        self._bottom_margin = kwargs.pop('bottom_margin', None)

        # Optional arguments with default values.
        self._left_padding = kwargs.pop('left_padding', 0)
        self._right_padding = kwargs.pop('right_padding', 0)
        self._top_padding = kwargs.pop('top_padding', 0)
        self._bottom_padding = kwargs.pop('bottom_padding', 0)
        self._corner_radius = Decimal(kwargs.pop('corner_radius', 0))
        self._padding_radius = Decimal(kwargs.pop('padding_radius', 0))
        self._background_image = kwargs.pop('background_image', None)
        self._background_filename = kwargs.pop('background_filename', None)

        # Leftover arguments.
        if kwargs:
            args = kwargs.keys()
            if len(args) == 1:
                raise TypeError("Unknown keyword argument {}.".format(args[0]))
            else:
                raise TypeError("Unknown keyword arguments: {}.".format(', '.join(args)))

        # Track which attributes have been automatically set.
        self._autoset = set()

        # Check all the dimensions etc are valid.
        self._calculate()

    def _calculate(self):
        """Checks the dimensions of the sheet are valid and consistent.

        NB: this is called internally when needed; there should be no need for
        user code to call it.

        """
        # Check the dimensions are larger than zero.
        for dimension in ('_sheet_width', '_sheet_height', '_columns', '_rows', '_label_width', '_label_height'):
            if getattr(self, dimension) <= 0:
                name = dimension.replace('_', ' ').strip().capitalize()
                raise InvalidDimension("{0:s} must be greater than zero.".format(name))

        # Check margins / gaps are not smaller than zero if given.
        # At the same time, force the values to decimals.
        for margin in ('_left_margin', '_column_gap', '_right_margin', '_top_margin', '_row_gap', '_bottom_margin',
                       '_left_padding', '_right_padding', '_top_padding', '_bottom_padding'):
            val = getattr(self, margin)
            if val is not None:
                if margin in self._autoset:
                    val = None
                else:
                    val = Decimal(val)
                    if val < 0:
                        name = margin.replace('_', ' ').strip().capitalize()
                        raise InvalidDimension("{0:s} cannot be less than zero.".format(name))
                setattr(self, margin, val)
            else:
                self._autoset.add(margin)

        # Check the corner radius.
        if self._corner_radius < 0:
            raise InvalidDimension("Corner radius cannot be less than zero.")
        if self._corner_radius > (self._label_width / 2):
            raise InvalidDimension("Corner radius cannot be more than half the label width.")
        if self._corner_radius > (self._label_height / 2):
            raise InvalidDimension("Corner radius cannot be more than half the label height.")

        # If there is no padding, we don't need the padding radius.
        if (self._left_padding + self._right_padding + self._top_padding + self._bottom_padding) == 0:
            if self._padding_radius != 0:
                raise InvalidDimension("Padding radius must be zero if there is no padding.")
        else:
            if (self._left_padding + self._right_padding) >= self._label_width:
                raise InvalidDimension("Sum of horizontal padding must be less than the label width.")
            if (self._top_padding + self._bottom_padding) >= self._label_height:
                raise InvalidDimension("Sum of vertical padding must be less than the label height.")
            if self._padding_radius < 0:
                raise InvalidDimension("Padding radius cannot be less than zero.")

        # Calculate the amount of spare space.
        hspace = self._sheet_width - (self._label_width * self._columns)
        vspace = self._sheet_height - (self._label_height * self._rows)

        # Cannot fit.
        if hspace < 0:
            raise InvalidDimension("Labels are too wide to fit on the sheet.")
        if vspace < 0:
            raise InvalidDimension("Labels are too tall to fit on the sheet.")

        # Process the horizontal margins / gaps.
        hcount = 1 + self._columns
        if self._left_margin is not None:
            hspace -= self._left_margin
            if hspace < 0:
                raise InvalidDimension("Left margin is too wide for the labels to fit on the sheet.")
            hcount -= 1
        if self._column_gap is not None:
            hspace -= ((self._columns - 1) * self._column_gap)
            if hspace < 0:
                raise InvalidDimension("Column gap is too wide for the labels to fit on the sheet.")
            hcount -= (self._columns - 1)
        if self._right_margin is not None:
            hspace -= self._right_margin
            if hspace < 0.01 and hspace > -0.01:
                self._right_margin += hspace
                hspace = 0
            if hspace < 0:
                raise InvalidDimension("Right margin is too wide for the labels to fit on the sheet.")
            hcount -= 1

        # Process the vertical margins / gaps.
        vcount = 1 + self._rows
        if self._top_margin is not None:
            vspace -= self._top_margin
            if vspace < 0:
                raise InvalidDimension("Top margin is too tall for the labels to fit on the sheet.")
            vcount -= 1
        if self._row_gap is not None:
            vspace -= ((self._rows - 1) * self._row_gap)
            if vspace < 0:
                raise InvalidDimension("Row gap is too tall for the labels to fit on the sheet.")
            vcount -= (self._rows - 1)
        if self._bottom_margin is not None:
            vspace -= self._bottom_margin
            if vspace < 0.01 and vspace > -0.01:
                self._bottom_margin += vspace
                vspace = 0
            if vspace < 0:
                raise InvalidDimension("Bottom margin is too tall for the labels to fit on the sheet.")
            vcount -= 1

        # If all the margins are specified, they must use up all available space.
        if hcount == 0 and hspace != 0:
            raise InvalidDimension("Not all width used by manually specified margins/gaps; {}mm left.".format(hspace))
        if vcount == 0 and vspace != 0:
            raise InvalidDimension("Not all height used by manually specified margins/gaps; {}mm left.".format(vspace))

        # Split any extra horizontal space and allocate it.
        if hcount:
            auto_margin = hspace / hcount
            for margin in ('_left_margin', '_column_gap', '_right_margin'):
                if getattr(self, margin) is None:
                    setattr(self, margin, auto_margin)

        # And allocate any extra vertical space.
        if vcount:
            auto_margin = vspace / vcount
            for margin in ('_top_margin', '_row_gap', '_bottom_margin'):
                if getattr(self, margin) is None:
                    setattr(self, margin, auto_margin)

    def bounding_boxes(self, mode='fraction', output='dict'):
        """Get the bounding boxes of the labels on a page.

        Parameters
        ----------
        mode: 'fraction', 'actual'
            If 'fraction', the bounding boxes are expressed as a fraction of the
            height and width of the sheet. If 'actual', they are the actual
            position of the labels in millimetres from the top-left of the
            sheet.
        output: 'dict', 'json'
            If 'dict', a dictionary with label identifier tuples (row, column)
            as keys and a dictionary with 'left', 'right', 'top', and 'bottom'
            entries as the values.
            If 'json', a JSON encoded string which represents a dictionary with
            keys of the string format 'rowxcolumn' and each value being a
            bounding box dictionary with 'left', 'right', 'top', and 'bottom'
            entries.

        Returns
        -------
        The bounding boxes in the format set by the output parameter.

        """
        boxes = {}

        # Check the parameters.
        if mode not in ('fraction', 'actual'):
            raise ValueError("Unknown mode {0}.".format(mode))
        if output not in ('dict', 'json'):
            raise ValueError("Unknown output {0}.".format(output))

        # Iterate over the rows.
        for row in range(1, self.rows + 1):
            # Top and bottom of all labels in the row.
            top = self.top_margin + ((row - 1) * (self.label_height + self.row_gap))
            bottom = top + self.label_height

            # Now iterate over all columns in this row.
            for column in range(1, self.columns + 1):
                # Left and right position of this column.
                left = self.left_margin + ((column - 1) * (self.label_width + self.column_gap))
                right = left + self.label_width

                # Output in the appropriate mode format.
                if mode == 'fraction':
                    box = {
                        'top': top / self.sheet_height,
                        'bottom': bottom / self.sheet_height,
                        'left': left / self.sheet_width,
                        'right': right / self.sheet_width,
                    }
                elif mode == 'actual':
                    box = {'top': top, 'bottom': bottom, 'left': left, 'right': right}

                # Add to the collection.
                if output == 'json':
                    boxes['{0:d}x{1:d}'.format(row, column)] = box
                    box['top'] = float(box['top'])
                    box['bottom'] = float(box['bottom'])
                    box['left'] = float(box['left'])
                    box['right'] = float(box['right'])
                else:
                    boxes[(row, column)] = box

        # Done.
        if output == 'json':
            return json.dumps(boxes)
        return boxes

    # Helper function to create an accessor for one of the properties.
    # attr is the 'internal' attribute e.g., _sheet_width.
    def create_accessor(attr, deletable=False):
        # Getter is simple; no processing needed.
        @property
        def accessor(self):
            return getattr(self, attr)

        # Setter is more complicated.
        @accessor.setter
        def accessor(self, value):
            # Store the original value in case we need to reset.
            original = getattr(self, attr)

            # If this was originally autoset or not.
            was_autoset = attr in self._autoset

            # Discard this attribute from the autoset list.
            self._autoset.discard(attr)

            # Set the value and see if it is valid.
            setattr(self, attr, value)
            try:
                self._calculate()
            except:
                # Reset to the original state.
                setattr(self, attr, original)
                if was_autoset:
                    self._autoset.add(attr)

                # Let the error propogate up.
                raise

        # Create a deleter if allowable.
        if deletable:
            @accessor.deleter
            def accessor(self):
                self._autoset.add(attr)
                setattr(self, attr, None)
                self._calculate()

        # And we now have our accessor.
        return accessor

    # Create accessors for all our properties.
    sheet_width = create_accessor('_sheet_width')
    sheet_height = create_accessor('_sheet_height')
    label_width = create_accessor('_label_width')
    label_height = create_accessor('_label_height')
    columns = create_accessor('_columns')
    rows = create_accessor('_rows')
    left_margin = create_accessor('_left_margin', deletable=True)
    column_gap = create_accessor('_column_gap', deletable=True)
    right_margin = create_accessor('_right_margin', deletable=True)
    top_margin = create_accessor('_top_margin', deletable=True)
    row_gap = create_accessor('_row_gap', deletable=True)
    bottom_margin = create_accessor('_bottom_margin', deletable=True)
    corner_radius = create_accessor('_corner_radius')
    padding_radius = create_accessor('_padding_radius')
    background_image = create_accessor('_background_image', deletable=True)
    background_filename = create_accessor('_background_filename', deletable=True)
    left_padding = create_accessor('_left_padding', deletable=True)
    right_padding = create_accessor('_right_padding', deletable=True)
    top_padding = create_accessor('_top_padding', deletable=True)
    bottom_padding = create_accessor('_bottom_padding', deletable=True)

    # Don't need the helper function any more.
    del create_accessor
