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
        self.__position = [1, 0]
        self.__pagesize = [specs['num_rows'], specs['num_columns']]
        self.__lw = specs['label_width'] * mm
        self.__lh = specs['label_height'] * mm
        self.__used = {}

    def partial_page(self, page, used_labels):
        """Allows a page to be marked as already partially used so you can
        generate a PDF to print on the remaining labels.

        :param page: The page number to mark as partially used. The page must
                     not have already been started, i.e., for page 1 this must
                     be called before any labels have been started, for page 2
                     this must be called before the first page is full and so
                     on.
        :param used_labels: An iterable of (row, column) pairs marking which
                            labels have been used already. The rows and columns
                            must be within the bounds of the sheet.

        """
        # Check the page number is valid.
        if page <= self.pages:
            raise ValueError("Page {0:d} has already started, cannot mark used labels now.".format(page))

        # Add these to any existing labels marked as used.
        used = self.__used.get(page, set())
        for row, column in used_labels:
            # Check the index is valid.
            if row < 1 or row > self.specs['num_rows']:
                raise IndexError("Invalid row number: {0:d}.".format(row))
            if column < 1 or column > self.specs['num_columns']:
                raise IndexError("Invalid column number: {0:d}.".format(column))

            # Add it.
            used.add((int(row), int(column)))

        # Save the details.
        self.__used[page] = used

    def __start_file(self):
        pagesize=(self.specs['sheet_width']*mm, self.specs['sheet_height']*mm)
        self.__canvas = Canvas(self.filename, pagesize=pagesize)

    def __next_label(self):
        # Special case for the very first label.
        if self.pages == 0:
            self.pages = 1

        # Filled up a page.
        if self.__position == self.__pagesize:
            self.__canvas.showPage()
            self.__position = [1, 0]
            self.pages += 1

        # Filled up a row.
        elif self.__position[1] == self.specs['num_columns']:
            self.__position[0] += 1
            self.__position[1] = 0

        # Move to the next column.
        self.__position[1] += 1

    def __next_unused_label(self):
        self.__next_label()
        if self.pages in self.__used:
            while tuple(self.__position) in self.__used[self.pages]:
                self.__next_label()
        self.labels += 1

    def add_label(self, obj):
        """Add a label to the sheet. The argument is the object to draw which
        will be passed to the drawing function.

        """
        # If this is the first label, create the canvas.
        if not self.__canvas:
            self.__start_file()

        # Find the next available label.
        self.__next_unused_label()

        # Calculate the bottom edge of the label.
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
