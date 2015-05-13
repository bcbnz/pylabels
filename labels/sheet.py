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

from reportlab.pdfgen.canvas import Canvas
from reportlab.graphics import shapes
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.graphics import renderPDF
from reportlab.graphics import renderPM
from reportlab.graphics.shapes import Drawing, ArcPath, Image
from copy import copy, deepcopy
from itertools import repeat

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
        self._dw = (self.specs.label_width - self.specs.left_padding - self.specs.right_padding) * mm
        self._dh = (self.specs.label_height - self.specs.top_padding - self.specs.bottom_padding) * mm
        self._lp = self.specs.left_padding * mm
        self._bp = self.specs.bottom_padding * mm
        self._pr = self.specs.padding_radius * mm
        self._used = {}
        self._pages = []
        self._current_page = None

        # Page information.
        self._pagesize = (float(self.specs.sheet_width*mm), float(self.specs.sheet_height*mm))
        self._numlabels = [self.specs.rows, self.specs.columns]
        self._position = [1, 0]
        self.label_count = 0
        self.page_count = 0

        # Background image.
        if self.specs.background_image:
            self._bgimage = deepcopy(self.specs.background_image)

            # Different classes are scaled in different ways...
            if isinstance(self._bgimage, Image):
                self._bgimage.x = 0
                self._bgimage.y = 0
                self._bgimage.width = self._pagesize[0]
                self._bgimage.height = self._pagesize[1]
            elif isinstance(self._bgimage, Drawing):
                self._bgimage.shift(0, 0)
                self._bgimage.scale(self._pagesize[0]/self._bgimage.width, self._pagesize[1]/self._bgimage.height)
            else:
                raise ValueError("Unhandled background type.")

        # Background from a filename.
        elif self.specs.background_filename:
            self._bgimage = Image(0, 0, self._pagesize[0], self._pagesize[1], self.specs.background_filename)

        # No background.
        else:
            self._bgimage = None

        # Borders and clipping paths. We need two clipping paths; one for the
        # label as a whole (which is identical to the border), and one for the
        # available drawing area (i.e., after taking the padding into account).
        # This is necessary because sometimes the drawing area can extend
        # outside the border at the corners, e.g., if there is left padding
        # only and no padding radius, then the 'available' area corners will be
        # square and go outside the label corners if they are rounded.

        # Copy some properties to a local scope.
        h, w, r = float(self._lh), float(self._lw), float(self._cr)

        # Create the border from a path. If the corners are not rounded, skip
        # adding the arcs.
        border = ArcPath()
        if r:
            border.moveTo(w - r, 0)
            border.addArc(w - r, r, r, -90, 0)
            border.lineTo(w, h - r)
            border.addArc(w - r, h - r, r, 0, 90)
            border.lineTo(r, h)
            border.addArc(r, h - r, r, 90, 180)
            border.lineTo(0, r)
            border.addArc(r, r, r, 180, 270)
            border.closePath()
        else:
            border.moveTo(0, 0)
            border.lineTo(w, 0)
            border.lineTo(w, h)
            border.lineTo(0, h)
            border.closePath()

        # Set the properties and store.
        border.isClipPath = 0
        border.strokeWidth = 1
        border.strokeColor = colors.black
        border.fillColor = None
        self._border = border

        # Clip path for the label is the same as the border.
        self._clip_label = deepcopy(border)
        self._clip_label.isClipPath = 1
        self._clip_label.strokeColor = None
        self._clip_label.fillColor = None

        # If there is no padding (i.e., the drawable area is the same as the
        # label area) then we can just use the label clip path for the drawing
        # clip path.
        if (self._dw == self._lw) and (self._dh == self._lh):
            self._clip_drawing = self._clip_label

        # Otherwise we have to generate a separate path.
        else:
            h, w, r = float(self._dh), float(self._dw), float(self._pr)
            clip = ArcPath()
            if r:
                clip.moveTo(w - r, 0)
                clip.addArc(w - r, r, r, -90, 0)
                clip.lineTo(w, h - r)
                clip.addArc(w - r, h - r, r, 0, 90)
                clip.lineTo(r, h)
                clip.addArc(r, h - r, r, 90, 180)
                clip.lineTo(0, r)
                clip.addArc(r, r, r, 180, 270)
                clip.closePath()
            else:
                clip.moveTo(0, 0)
                clip.lineTo(w, 0)
                clip.lineTo(w, h)
                clip.lineTo(0, h)
                clip.closePath()

            # Set the clipping properties.
            clip.isClipPath = 1
            clip.strokeColor = None
            clip.fillColor = None
            self._clip_drawing = clip

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
        if self._bgimage:
            self._current_page.add(self._bgimage)
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
                    self._shade_missing_label()

                # Try our luck with the next label.
                self._next_label()
                missing = self._used.get(self.page_count, set())

        # Increment the count now we have found a suitable position.
        self.label_count += 1

    def _calculate_edges(self):
        """Calculate edges of the current label. Not intended for external use.


        """
        # Calculate the left edge of the label.
        left = self.specs.left_margin
        left += (self.specs.label_width * (self._position[1] - 1))
        if self.specs.column_gap:
            left += (self.specs.column_gap * (self._position[1] - 1))
        left *= mm

        # And the bottom.
        bottom = self.specs.sheet_height - self.specs.top_margin
        bottom -= (self.specs.label_height * self._position[0])
        if self.specs.row_gap:
            bottom -= (self.specs.row_gap * (self._position[0] - 1))
        bottom *= mm

        # Done.
        return float(left), float(bottom)

    def _shade_missing_label(self):
        """Helper method to shade a missing label. Not intended for external use.

        """
        # Start a drawing for the whole label.
        label = Drawing(float(self._lw), float(self._lh))
        label.add(self._clip_label)

        # Fill with a rectangle; the clipping path will take care of the borders.
        r = shapes.Rect(0, 0, float(self._lw), float(self._lh))
        r.fillColor = self.shade_missing
        r.strokeColor = None
        label.add(r)

        # Add the label to the page.
        label.shift(*self._calculate_edges())
        self._current_page.add(label)

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
            self._shade_missing_label()

    def _draw_label(self, obj, count):
        """Helper method to draw on the current label. Not intended for external use.

        """
        # Start a drawing for the whole label.
        label = Drawing(float(self._lw), float(self._lh))
        label.add(self._clip_label)

        # And one for the available area (i.e., after padding).
        available = Drawing(float(self._dw), float(self._dh))
        available.add(self._clip_drawing)

        # Call the drawing function.
        self.drawing_callable(available, float(self._dw), float(self._dh), obj)

        # Render the contents on the label.
        available.shift(float(self._lp), float(self._bp))
        label.add(available)

        # Draw the border if requested.
        if self.border:
            label.add(self._border)

        # Add however many copies we need to.
        for i in range(count):
            # Find the next available label.
            self._next_unused_label()

            # Have we been told to skip this page?
            if self.pages_to_draw and self.page_count not in self.pages_to_draw:
                continue

            # Add the label to the page. ReportLab stores the added drawing by
            # reference so we have to copy it N times.
            thislabel = copy(label)
            thislabel.shift(*self._calculate_edges())
            self._current_page.add(thislabel)

    def add_label(self, obj, count=1):
        """Add a label to the sheet.

        Parameters
        ----------
        obj:
            The object to draw on the label. This is passed without modification
            or copying to the drawing function.
        count: positive integer, default 1
            How many copies of the label to add to the sheet. Note that the
            drawing function will only be called once and the results copied
            for each label. If the drawing function maintains any state
            internally then using this parameter may break it.

        """
        self._draw_label(obj, count)

    def add_labels(self, objects, count=1):
        """Add multiple labels to the sheet.

        Parameters
        ----------
        objects: iterable
            An iterable of the objects to add. Each of these will be passed to
            the add_label method. Note that if this is a generator it will be
            consumed.
        count: positive integer or iterable of positive integers, default 1
            The number of copies of each label to add. If a single integer,
            that many copies of every label are added. If an iterable, then
            each value specifies how many copies of the corresponding label to
            add. The iterables are advanced in parallel until one is exhausted;
            extra values in the other one are ignored. This means that if there
            are fewer count entries than objects, the objects corresponding to
            the missing counts will not be added to the sheet.

            Note that if this is a generator it will be consumed. Also note
            that the drawing function will only be called once for each label
            and the results copied for the repeats. If the drawing function
            maintains any state internally then using this parameter may break
            it.

        """
        # If we can convert it to an int, do so and use the itertools.repeat()
        # method to create an infinite iterator from it. Otherwise, assume it
        # is an iterable or sequence.
        try:
            count = int(count)
        except TypeError:
            pass
        else:
            count = repeat(count)

        # If it is not an iterable (e.g., a list or range object),
        # create an iterator over it.
        if not hasattr(count, 'next') and not hasattr(count, '__next__'):
            count = iter(count)

        # Go through the objects.
        for obj in objects:
            # Check we have a count for this one.
            try:
                thiscount = next(count)
            except StopIteration:
                break

            # Draw it.
            self._draw_label(obj, thiscount)

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

        # Rendering to an image (as opposed to a PDF) requires any background
        # to have an integer width and height if it is a ReportLab Image
        # object. Drawing objects are exempt from this.
        oldw, oldh = None, None
        if isinstance(self._bgimage, Image):
            oldw, oldh = self._bgimage.width, self._bgimage.height
            self._bgimage.width = int(oldw) + 1
            self._bgimage.height = int(oldh) + 1

        # Let ReportLab do the heavy lifting.
        renderPM.drawToFile(self._pages[page-1], filelike, format, dpi, background_colour)

        # Restore the size of the background image if we changed it.
        if oldw:
            self._bgimage.width = oldw
            self._bgimage.height = oldh

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

        # Rendering to an image (as opposed to a PDF) requires any background
        # to have an integer width and height if it is a ReportLab Image
        # object. Drawing objects are exempt from this.
        oldw, oldh = None, None
        if isinstance(self._bgimage, Image):
            oldw, oldh = self._bgimage.width, self._bgimage.height
            self._bgimage.width = int(oldw) + 1
            self._bgimage.height = int(oldh) + 1

        # Let ReportLab do the heavy lifting.
        s = renderPM.drawToString(self._pages[page-1], format, dpi, background_colour)

        # Restore the size of the background image if we changed it.
        if oldw:
            self._bgimage.width = oldw
            self._bgimage.height = oldh

        # Done.
        return s
