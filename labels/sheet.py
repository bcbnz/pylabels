# This file is part of pylabels, a Python library to create PDFs for printing
# labels.
# Copyright (C) 2012, 2013, 2014 Blair Bonnett
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
from reportlab.graphics import shapes
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.graphics import renderPDF
from reportlab.graphics import renderPM
from reportlab.graphics.shapes import Drawing, ArcPath
from copy import deepcopy

from decimal import Decimal
mm = Decimal(mm)

class Sheet(object):
    """Create one or more sheets of labels.

    """

    def __init__(self, specification, drawing_callable, pages_to_draw=None, border=False, shade_missing=False):
        """
        Parameters
        ----------
        specification: labels.Specification instance
            The sizes etc of the label sheets.
        drawing_callable: callable
            A function (or other callable object) to call to draw an individual
            label. It will be given four parameters specifying the label. In
            order, these are a `reportlab.graphics.shapes.Drawing` instance to
            draw the label on, the width of the label, the height of the label,
            and the object to draw. The dimensions will be in points, the unit
            of choice for ReportLab.
        pages_to_draw: list of positive integers, default None
            The list pages to actually draw labels on. This is intended to be
            used with the preview methods to avoid drawing labels that will
            never be displayed. A value of None means draw all pages.
        border: Boolean, default False
            Whether or not to draw a border around each label.
        shade_missing: Boolean or ReportLab colour, default False
            Whether or not to shade missing labels (those specified through the
            partial_pages method). False means leave the labels unshaded. If a
            ReportLab colour is given, the labels will be shaded in that colour.
            A value of True will result in the missing labels being shaded in
            the hex colour 0xBBBBBB (a medium-light grey).

        Notes
        -----
        If you specify a pages_to_draw list, pages not in that list will be
        blank since the drawing function will not be called on that page. This
        could have a side-affect if you rely on the drawing function modifying
        some global values. For example, in the nametags.py and preview.py demo
        scripts, the colours for each label are picked by a pseduo-random number
        generator. However, in the preview script, this generator is not
        advanced and so the colours on the last page differ between the preview
        and the actual output.

        """
        # Save our arguments.
        specification._calculate()
        self.specs = deepcopy(specification)
        self.drawing_callable = drawing_callable
        self.pages_to_draw = pages_to_draw
        self.border = border
        if shade_missing == True:
            self.shade_missing = colors.HexColor(0xBBBBBB)
        else:
            self.shade_missing = shade_missing

        # Set up some internal variables.
        self._lw = self.specs.label_width * mm
        self._lh = self.specs.label_height * mm
        self._cr = self.specs.corner_radius * mm
        self._used = {}
        self._pages = []
        self._current_page = None

        # Page information.
        self._pagesize = (float(self.specs.sheet_width*mm), float(self.specs.sheet_height*mm))
        self._numlabels = [self.specs.rows, self.specs.columns]
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

        Parameters
        ----------
        page: positive integer
            The page number to mark as partially used. The page must not have
            already been started, i.e., for page 1 this must be called before
            any labels have been started, for page 2 this must be called before
            the first page is full and so on.
        used_labels: iterable
            An iterable of (row, column) pairs marking which labels have been
            used already. The rows and columns must be within the bounds of the
            sheet.

        """
        # Check the page number is valid.
        if page <= self.page_count:
            raise ValueError("Page {0:d} has already started, cannot mark used labels now.".format(page))

        # Add these to any existing labels marked as used.
        used = self._used.get(page, set())
        for row, column in used_labels:
            # Check the index is valid.
            if row < 1 or row > self.specs.rows:
                raise IndexError("Invalid row number: {0:d}.".format(row))
            if column < 1 or column > self.specs.columns:
                raise IndexError("Invalid column number: {0:d}.".format(column))

            # Add it.
            used.add((int(row), int(column)))

        # Save the details.
        self._used[page] = used

    def _new_page(self):
        """Helper function to start a new page. Not intended for external use.

        """
        self._current_page = Drawing(*self._pagesize)
        self._pages.append(self._current_page)
        self.page_count += 1
        self._position = [1, 0]

    def _next_label(self):
        """Helper method to move to the next label. Not intended for external use.

        This does not increment the label_count attribute as the next label may
        not be usable (it may have been marked as missing through
        partial_pages). See _next_unused_label for generally more useful method.

        """
        # Special case for the very first label.
        if self.page_count == 0:
            self._new_page()

        # Filled up a page.
        elif self._position == self._numlabels:
            self._new_page()

        # Filled up a row.
        elif self._position[1] == self.specs.columns:
            self._position[0] += 1
            self._position[1] = 0

        # Move to the next column.
        self._position[1] += 1

    def _next_unused_label(self):
        """Helper method to move to the next unused label. Not intended for external use.

        This method will shade in any missing labels if desired, and will
        increment the label_count attribute once a suitable label position has
        been found.

        """
        self._next_label()

        # This label may be missing.
        if self.page_count in self._used:
            # Keep try while the label is missing.
            missing = self._used.get(self.page_count, set())
            while tuple(self._position) in missing:
                # Throw the missing information away now we have used it. This
                # allows the _shade_remaining_missing method to work.
                missing.discard(tuple(self._position))

                # Shade the missing label if desired.
                if self.shade_missing:
                    self._draw_label(self._missing_label)

                # Try our luck with the next label.
                self._next_label()
                missing = self._used.get(self.page_count, set())

        # Increment the count now we have found a suitable position.
        self.label_count += 1

    def _missing_label(self, label, width, height, obj=None):
        """Helper drawing callable to shade a missing label. Not intended for external use.

        """
        # Sanity check. Should never be False if we get here but who knows.
        if not self.shade_missing:
            return

        # Shade a rectangle over the entire bounding box. The clipping path will
        # take care of any rounded corners.
        r = shapes.Rect(0, 0, width, height)
        r.fillColor = self.shade_missing
        r.strokeColor = None
        label.add(r)

    def _shade_remaining_missing(self):
        """Helper method to shade any missing labels remaining on the current
        page. Not intended for external use.

        Note that this will modify the internal _position attribute and should
        therefore only be used once all the 'real' labels have been drawn.

        """
        # Sanity check.
        if not self.shade_missing:
            return

        # Run through each missing label left in the current page and shade it.
        missing = self._used.get(self.page_count, set())
        for position in missing:
            self._position = position
            self._draw_label(self._missing_label)

    def _draw_label(self, drawing_callable, obj=None):
        """Helper method to draw on the current label. Not intended for external use.

        """
        # Create a drawing object for this label and add the border.
        label = Drawing(float(self._lw), float(self._lh))
        label.add(self._border)
        if self._border_visible:
            label.add(self._border_visible)

        # Call the drawing function.
        drawing_callable(label, float(self._lw), float(self._lh), obj)

        # Calculate the bottom edge of the label.
        bottom = self.specs.sheet_height - self.specs.top_margin
        bottom -= (self.specs.label_height * self._position[0])
        bottom -= (self.specs.row_gap * (self._position[0] - 1))
        bottom *= mm

        # And the left edge.
        left = self.specs.left_margin
        left += (self.specs.label_width * (self._position[1] - 1))
        left += (self.specs.column_gap * (self._position[1] - 1))
        left *= mm

        # Render the label on the sheet.
        label.shift(float(left), float(bottom))
        self._current_page.add(label)

    def add_label(self, obj):
        """Add a label to the sheet.

        Parameters
        ----------
        obj:
            The object to draw on the label. This is passed without modification
            or copying to the drawing function.

        """
        # Find the next available label.
        self._next_unused_label()

        # Have we been told to skip this page?
        if self.pages_to_draw and self.page_count not in self.pages_to_draw:
            return

        # Draw it.
        self._draw_label(self.drawing_callable, obj)

    def add_labels(self, objects):
        """Add multiple labels to the sheet.

        Parameters
        ----------
        objects: iterable
            An iterable of the objects to add. Each of these will be passed to
            the add_label method. Note that if this is a generator it will be
            consumed.

        """
        for obj in objects:
            self.add_label(obj)

    def save(self, filelike):
        """Save the file as a PDF.

        Parameters
        ----------
        filelike: path or file-like object
            The filename or file-like object to save the labels under. Any
            existing contents will be overwritten.

        """
        # Shade any remaining missing labels if desired.
        self._shade_remaining_missing()

        # Create a canvas.
        canvas = Canvas(filelike, pagesize=self._pagesize)

        # Render each created page onto the canvas.
        for page in self._pages:
            renderPDF.draw(page, canvas, 0, 0)
            canvas.showPage()

        # Done.
        canvas.save()

    def preview(self, page, filelike, format='png', dpi=72, background_colour=0xFFFFFF):
        """Render a preview image of a page.

        Parameters
        ----------
        page: positive integer
            Which page to render. Must be in the range [1, page_count]
        filelike: path or file-like object
            Can be a filename as a string, a Python file object, or something
            which behaves like a Python file object.  For example, if you were
            using the Django web framework, an HttpResponse object could be
            passed to render the preview to the browser (as long as you remember
            to set the mimetype of the response).  If you pass a filename, the
            existing contents will be overwritten.
        format: string
            The image format to use for the preview. ReportLab uses the Python
            Imaging Library (PIL) internally, so any PIL format should be
            supported.
        dpi: positive real
            The dots-per-inch to use when rendering.
        background_colour: Hex colour specification
            What color background to use.

        Notes
        -----
        If you are creating this sheet for a preview only, you can pass the
        pages_to_draw parameter to the constructor to avoid the drawing function
        being called for all the labels on pages you'll never look at. If you
        preview a page you did not tell the sheet to draw, you will get a blank
        image.

        Raises
        ------
        ValueError:
            If the page number is not valid.

        """
        # Check the page number.
        if page < 1 or page > self.page_count:
            raise ValueError("Invalid page number; should be between 1 and {0:d}.".format(self.page_count))

        # Shade any remaining missing labels if desired.
        self._shade_remaining_missing()

        # Let ReportLab do the heavy lifting.
        renderPM.drawToFile(self._pages[page-1], file_like, format, dpi, background_colour)

    def preview_string(self, page, format='png', dpi=72, background_colour=0xFFFFFF):
        """Render a preview image of a page as a string.

        Parameters
        ----------
        page: positive integer
            Which page to render. Must be in the range [1, page_count]
        format: string
            The image format to use for the preview. ReportLab uses the Python
            Imaging Library (PIL) internally, so any PIL format should be
            supported.
        dpi: positive real
            The dots-per-inch to use when rendering.
        background_colour: Hex colour specification
            What color background to use.

        Notes
        -----
        If you are creating this sheet for a preview only, you can pass the
        pages_to_draw parameter to the constructor to avoid the drawing function
        being called for all the labels on pages you'll never look at. If you
        preview a page you did not tell the sheet to draw, you will get a blank
        image.

        Raises
        ------
        ValueError:
            If the page number is not valid.

        """
        # Check the page number.
        if page < 1 or page > self.page_count:
            raise ValueError("Invalid page number; should be between 1 and {0:d}.".format(self.page_count))

        # Shade any remaining missing labels if desired.
        self._shade_remaining_missing()

        # Let ReportLab do the heavy lifting.
        return renderPM.drawToString(self._pages[page-1], format, dpi, background_colour)
