# This file is part of pylabels, a Python library to create PDFs for printing
# labels.
# Copyright (C) 2012, 2013 Blair Bonnett
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
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.graphics import renderPDF
from reportlab.graphics import renderPM
from reportlab.graphics.shapes import Drawing, ArcPath

from decimal import Decimal
mm = Decimal(mm)

class Sheet(object):
    """Create one or more sheets of labels.

    """

    def __init__(self, specs, drawing_callable, pages_to_draw=None, border=False):
        """
        :param specs: Sheet specification dictionary from the
                      sheet_specifications.create() function.
        :param drawing_callable: The function to call to draw an individual
                                 label. This will get 4 parameters: a ReportLab
                                 Drawing object to draw the label on, its width
                                 and height, and the object to draw. The
                                 dimensions will be in points, the unit of
                                 choice for ReportLab.
        :param pages_to_draw: A list of pages to actually draw labels on. This
                              is intended to be used with the :method:`preview`
                              to avoid drawing labels that will never be
                              displayed. A value of ``None`` (the default) means
                              draw all pages.
        :param border: Whether or not to draw a border around each label.

        Note that if you specify a ``pages_to_draw`` list, pages not in that
        list will be blank since the drawing function will not be called on that
        page. This could have a side-affect if you rely on the drawing function
        modifying some global values. For example, in the nametags.py and preview.py demo
        scripts, the colours for each label are picked by a pseduo-random number
        generator. However, in the preview script, this generator is not
        advanced and so the colours on the last page are different.

        """
        # Save our arguments.
        self.specs = specs
        self.drawing_callable = drawing_callable
        self.pages_to_draw = pages_to_draw
        self.border = border

        # Set up some internal variables.
        self._lw = specs['label_width'] * mm
        self._lh = specs['label_height'] * mm
        self._cr = (specs['corner_radius'] or 0) * mm
        self._used = {}
        self._pages = []
        self._current_page = None

        # Page information.
        self._pagesize = (float(self.specs['sheet_width']*mm), float(self.specs['sheet_height']*mm))
        self._numlabels = [self.specs['num_rows'], self.specs['num_columns']]
        self._position = [1, 0]
        self.label_count = 0
        self.page_count = 0

        # Have to create the border from a path so we can use it as a clip path.
        border = ArcPath()

        # Copy some properties to a local scope.
        h, w, cr = float(self._lh), float(self._lw), float(self._cr)

        # If the border has rounded corners.
        if self._cr:
            border.moveTo(w - cr, 0)
            border.addArc(w - cr, cr, cr, -90, 0)
            border.lineTo(w, h - cr)
            border.addArc(w - cr, h - cr, cr, 0, 90)
            border.lineTo(cr, h)
            border.addArc(cr, h - cr, cr, 90, 180)
            border.lineTo(0, cr)
            border.addArc(cr, cr, cr, 180, 270)
            border.closePath()

        # No rounded corners.
        else:
            border.moveTo(0, 0)
            border.lineTo(w, 0)
            border.lineTo(w, h)
            border.lineTo(0, h)
            border.closePath()

        # Use it as a clip path.
        border.isClipPath = 1
        border.strokeColor = None
        border.fillColor = None

        # And done.
        self._border = border

        # The border doesn't show up if its part of a clipping path when
        # outputting to an image. If its needed, make a copy and turn the
        # clipping path off.
        if self.border:
            from copy import copy
            self._border_visible = copy(self._border)
            self._border_visible.isClipPath = 0
            self._border_visible.strokeWidth = 1
            self._border_visible.strokeColor = colors.black
        else:
            self._border_visible = None

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
        if page <= self.page_count:
            raise ValueError("Page {0:d} has already started, cannot mark used labels now.".format(page))

        # Add these to any existing labels marked as used.
        used = self._used.get(page, set())
        for row, column in used_labels:
            # Check the index is valid.
            if row < 1 or row > self.specs['num_rows']:
                raise IndexError("Invalid row number: {0:d}.".format(row))
            if column < 1 or column > self.specs['num_columns']:
                raise IndexError("Invalid column number: {0:d}.".format(column))

            # Add it.
            used.add((int(row), int(column)))

        # Save the details.
        self._used[page] = used

    def _new_page(self):
        self._current_page = Drawing(*self._pagesize)
        self._pages.append(self._current_page)
        self.page_count += 1
        self._position = [1, 0]

    def _next_label(self):
        # Special case for the very first label.
        if self.page_count == 0:
            self._new_page()

        # Filled up a page.
        elif self._position == self._numlabels:
            self._new_page()

        # Filled up a row.
        elif self._position[1] == self.specs['num_columns']:
            self._position[0] += 1
            self._position[1] = 0

        # Move to the next column.
        self._position[1] += 1

    def _next_unused_label(self):
        self._next_label()
        if self.page_count in self._used:
            while tuple(self._position) in self._used[self.page_count]:
                self._next_label()
        self.label_count += 1

    def add_label(self, obj):
        """Add a label to the sheet.

        :param obj: The object to draw on the label. This is passed without
                    modification or copying to the drawing function.

        """
        # Find the next available label.
        self._next_unused_label()
        if self.pages_to_draw and self.page_count not in self.pages_to_draw:
            return

        # Create a drawing object for this label and add the border.
        label = Drawing(float(self._lw), float(self._lh))
        label.add(self._border)
        if self._border_visible:
            label.add(self._border_visible)

        # Call the drawing function.
        self.drawing_callable(label, float(self._lw), float(self._lh), obj)

        # Calculate the bottom edge of the label.
        bottom = self.specs['sheet_height'] - self.specs['top_margin']
        bottom -= (self.specs['label_height'] * self._position[0])
        bottom -= (self.specs['row_gap'] * (self._position[0] - 1))
        bottom *= mm

        # And the left edge.
        left = self.specs['left_margin']
        left += (self.specs['label_width'] * (self._position[1] - 1))
        left += (self.specs['column_gap'] * (self._position[1] - 1))
        left *= mm

        # Render the label on the sheet.
        label.shift(float(left), float(bottom))
        self._current_page.add(label)

    def add_labels(self, obj_iterable):
        """Add multiple labels to the sheet.

        :param obj_iterable: An iterable of the objects to add. Each of these
                             will be passed to :method:`add_label`. Note that,
                             if this is a generator, it will be consumed.

        """
        for obj in obj_iterable:
            self.add_label(obj)

    def save(self, filename):
        """Save the file as a PDF.

        :param filename: The filename to save the labels under. Any existing
                         contents will be overwritten.

        """
        canvas = Canvas(filename, pagesize=self._pagesize)
        for page in self._pages:
            renderPDF.draw(page, canvas, 0, 0)
            canvas.showPage()
        canvas.save()

    def preview(self, page, file_like, format='png', dpi=72, background_color=0xFFFFFF):
        """Render a preview image of a page.

        :param page: Which page to render.
        :param file_like: Can be a filename as a string, a Python file object,
                          or something which behaves like a Python file object.
                          For example, if you were using the Django web
                          framework, an HttpResponse object could be
                          passed to render the preview to the browser (as long
                          as you remember to set the mimetype of the response).
                          If you pass a filename, the existing contents will be
                          overwritten.
        :param format: The format to render the page as.
        :param dpi: The dots-per-inch to use when rendering.
        :param background_color: What color background to use.

        If you are creating this sheet for a preview only, then use the
        ``pages`` parameter to the constructor to avoid the drawing function
        being called for all the labels on pages you'll never look at. If you
        preview a page you did not tell the sheet to draw, you will get a blank
        image.

        """
        if page < 1 or page > self.page_count:
            raise ValueError("Invalid page number; should be between 1 and {0:d}.".format(self.page_count))
        renderPM.drawToFile(self._pages[page-1], file_like, format, dpi, background_color)
