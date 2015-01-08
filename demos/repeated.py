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

import labels
from reportlab.graphics import shapes

# Create an A4 portrait (210mm x 297mm) sheets with 2 columns and 8 rows of
# labels. Each label is 90mm x 25mm with a 2mm rounded corner. The margins are
# automatically calculated.
specs = labels.Specification(210, 297, 2, 8, 90, 25, corner_radius=2)

# Create a function to draw each label. This will be given the ReportLab drawing
# object to draw on, the dimensions (NB. these will be in points, the unit
# ReportLab uses) of the label, and the object to render.
def draw_label(label, width, height, obj):
    # To demonstrate that this is only called once for each label, no matter
    # how many times it is repeated on the sheet.
    print('Drawing "{0:s}".'.format(str(obj)))

    # Just convert the object to a string and print this at the bottom left of
    # the label.
    label.add(shapes.String(2, 2, str(obj), fontName="Helvetica", fontSize=40))

# Create the sheet.
sheet = labels.Sheet(specs, draw_label, border=True)

# Mark some of the labels on the first page as already used.
sheet.partial_page(1, ((1, 1), (2, 2), (4, 2)))

# Add a couple of labels.
sheet.add_label("Hello")
sheet.add_label("World", count=3)

# Since the second page hasn't started yet, we can mark some of its labels as
# already used too.
sheet.partial_page(2, ((2, 1), (3, 1)))

# We can also add each item from an iterable, either once...
sheet.add_labels(range(3, 8))

# ...a constant number of times...
sheet.add_labels(range(8, 15), count=2)

# ...or a variable number of times. Note that the extra items in the count
# iterator are ignored.
sheet.add_labels(range(15, 22), count=range(1, 100))

# If there are more objects than count values, those without count values
# are skipped (note that 'Three' does not appear in the output).
sheet.add_labels(['One', 'Two', 'Three'], count=[3,2])

# Any oversize label is automatically trimmed to prevent it messing up others.
sheet.add_label("Oversized label here")

# Save the file and we are done.
sheet.save('repeated.pdf')
print("{0:d} label(s) output on {1:d} page(s).".format(sheet.label_count, sheet.page_count))
