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

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm

class Sheet(object):
    """Create one or more sheets of labels.
    """

    def __init__(self, filename, specs, drawing_callable, border=False):
        """
        :param filename: Name of the PDF file to save the labels as. Any
                         existing content will be overwritten.
        :param specs: Sheet specification dictionary from the
                      sheet_specifications.create() function.
        :param drawing_callable: The function to call to draw an individual
                                 label. This will get 5 parameters: the left and
                                 bottom positions of the label, its width and
                                 height, and the object to draw. The position
                                 and dimensions will be in points, the unit of
                                 choice for ReportLab.
        :param border: Draw a border around each label.

        """
        # Save our arguments.
        self.filename = filename
        self.specs = specs
        self.drawing_callable = drawing_callable
        self.border = border

        # Initialise page and label counters.
        self.labels = 0
        self.pages = 0

        # Set up some internal variables.
        self.__canvas = None
        self.__position = [1, 1]
        self.__lw = specs['label_width'] * mm
        self.__lh = specs['label_height'] * mm

    def __start_file(self):
        pagesize=(self.specs['sheet_width']*mm, self.specs['sheet_height']*mm)
        self.__canvas = Canvas(self.filename, pagesize=pagesize)

    def add_label(self, obj):
        """Add a label to the sheet. The argument is the object to draw which
        will be passed to the drawing function.

        """
        # If this is the first label, create the canvas.
        if not self.__canvas:
            self.__start_file()

        # Update the counters.
        self.labels += 1
        if self.__position == [1, 1]:
            self.pages += 1

        # Calculate the bottom edge of the next label.
        bottom = self.specs['sheet_height'] - self.specs['top_margin']
        bottom -= (self.specs['label_height'] * self.__position[0])
        bottom -= (self.specs['row_gap'] * (self.__position[0] - 1))
        bottom *= mm

        # And the left edge.
        left = self.specs['left_margin']
        left += (self.specs['label_width'] * (self.__position[1] - 1))
        left += (self.specs['column_gap'] * (self.__position[1] - 1))
        left *= mm

        # Save the state of the canvas to protect against changes made by the
        # drawing function.
        self.__canvas.saveState()

        # Create a clipping path to prevent the drawing of this label covering
        # other drawings.
        clip = self.__canvas.beginPath()
        clip.rect(left, bottom, self.__lw, self.__lh)
        self.__canvas.clipPath(clip, stroke=0)

        # Call the drawing function.
        self.drawing_callable(self.__canvas, left, bottom, self.__lw, self.__lh, obj)

        # Restore the state.
        self.__canvas.restoreState()

        # Draw the border if requested.
        if self.border:
            self.__canvas.rect(left, bottom, self.__lw, self.__lh)

        # Move to the next column.
        self.__position[1] += 1

        # Filled up a row.
        if self.__position[1] > self.specs['num_columns']:
            # Next row, first column.
            self.__position[0] += 1
            self.__position[1] = 1

            # Filled up a page.
            if self.__position[0] > self.specs['num_rows']:
                # Move to the next page, first row.
                self.__canvas.showPage()
                self.__position[0] = 1

    def add_labels(self, obj_iterable):
        """Add multiple labels. Each item in the given iterable will be passed
        to add_label().

        """
        for obj in obj_iterable:
            self.add_label(obj)

    def save(self):
        """Save the file. Until this is called, the output is not written to the
        file. Calling this has the side-affect of starting a new page.

        """
        if self.__canvas:
            self.__canvas.save()
            self.__position = [1, 1]
