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

import labels.sheet_specifications
import labels.sheet

# Create an A4 portrait (210mm x 297mm) sheets with 2 columns and 8 rows of
# labels. Each label is 90mm x 25mm with a 2mm rounded corner. The margins are
# automatically calculated.
specs = labels.sheet_specifications.create(210, 297, 2, 8, 90, 25, corner_radius=2)

# Create a function to draw each label. This will be given the ReportLab canvas
# to draw on, the position and dimensions (NB. these will be in points, the
# unit ReportLab uses) of the current label, and the object to draw on the
# label.
def draw_label(canvas, left, bottom, width, height, obj):
    # Just convert the object to a string and print this at the bottom left of
    # the label.
    canvas.setFont("Helvetica", 40)
    canvas.drawString(left, bottom, str(obj))

# Create the sheet.
sheet = labels.sheet.Sheet('basic.pdf', specs, draw_label, border=True)

# Add a couple of labels.
sheet.add_label("Hello")
sheet.add_label("World")

# We can also add each item from an iterable.
sheet.add_labels(range(3, 22))

# Note that any oversize label is automatically trimmed to prevent it messing up
# other labels.
sheet.add_label("Oversized label here")

# Save the file and we are done.
sheet.save()
print("{0:d} label(s) output on {1:d} page(s).".format(sheet.labels, sheet.pages))
