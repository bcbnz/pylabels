# This file is part of pylabels, a Python library to create PDFs for printing
# labels.
# Copyright (C) 2015 Blair Bonnett
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


# This demonstrates adding a background image to a sheet. There are three ways
# a background can be added: from a file, from a ReportLab Image, or a
# ReportLab drawing.
# If you have label sheets with preprinted information (e.g., a header/footer
# with company logos) this can be useful for previewing how the final printed
# labels would look. You would then disable the background to generate the
# final PDF.


import labels
from reportlab.graphics import shapes
import os.path

# Paths to the images used for backgrounds.
dirname = os.path.dirname(__file__)
file1 = os.path.join(dirname, "page_background_1.png")
file2 = os.path.join(dirname, "page_background_2.png")

# Create a function to draw each label. This will be given the ReportLab drawing
# object to draw on, the dimensions (NB. these will be in points, the unit
# ReportLab uses) of the label, and the object to render.
def draw_label(label, width, height, obj):
    # Just convert the object to a string and print this at the bottom left of
    # the label.
    label.add(shapes.String(2, 2, str(obj), fontName="Helvetica", fontSize=40))

# Since we are generating three PDFs for comparison, define a function to process one.
def process_sheet(specs, filename):
    # Create the sheet.
    sheet = labels.Sheet(specs, draw_label, border=True)

    # Add a couple of labels.
    sheet.add_label("Hello")
    sheet.add_label("World")

    # We can also add each item from an iterable.
    sheet.add_labels(range(3, 22))

    # Note that any oversize label is automatically trimmed to prevent it messing up
    # other labels.
    sheet.add_label("Oversized label here")

    # Save the file and we are done.
    sheet.save(filename)
    print("{0:s}: {1:d} label(s) output on {2:d} page(s).".format(filename, sheet.label_count, sheet.page_count))

# Option one: background from a file.
specs = labels.Specification(210, 297, 2, 8, 90, 25, corner_radius=2, background_filename=file1)
process_sheet(specs, "page_background_file.pdf")

# Option two: background from a ReportLab image.
# Note we just load it from file, but you could do something fancier...
# The size parameters don't matter as pylabels will scale it to fit the page.
specs = labels.Specification(210, 297, 2, 8, 90, 25, corner_radius=2, background_image=shapes.Image(0, 0, 750, 1055, file2))
process_sheet(specs, "page_background_image.pdf")

# Option three: use a ReportLab drawing.
# Again, this will be automatically scaled so choose the size to suit you.
# Using the size of the page sounds like a sensible option.
bg = shapes.Drawing(width=210, height=297)
bg.add(shapes.String(105, 50, "My cool background", textAnchor="middle"))
bg.add(shapes.Wedge(10, 155, 95, 30, 90, fillColor='green'))
specs = labels.Specification(210, 297, 2, 8, 90, 25, corner_radius=2, background_image=bg)
process_sheet(specs, "page_background_drawing.pdf")
