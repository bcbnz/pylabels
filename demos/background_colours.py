# This file is part of pylabels, a Python library to create PDFs for printing
# labels.
# Copyright (C) 2014 Blair Bonnett
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
from reportlab.graphics.widgets.grids import Grid
from reportlab.lib import colors
import random

# Colours used as backgrounds.
colours = [
    colors.HexColor(0x04F1B1),
    colors.HexColor('#ADADAF'),
    colors.Color(0.5, 0.1, 0.7),
    colors.Color(0.5, 0.1, 0.1, alpha=0.5),
    colors.CMYKColor(0.1, 0.1, 0.6, 0.3),
]

# Create an A4 portrait (210mm x 297mm) sheet with 2 columns and 8 rows of
# labels. Each label is 90mm x 25mm with a 2mm rounded corner. The margins are
# automatically calculated.
specs = labels.Specification(210, 297, 2, 8, 90, 25, corner_radius=2)

# Create a function to draw each label. This will be given the ReportLab drawing
# object to draw on, the dimensions (NB. these will be in points, the unit
# ReportLab uses) of the label, and the object to render.
def draw_label(label, width, height, obj):
    # Pick a background colour.
    colour = random.choice(colours)

    # And a style.
    style = random.choice(('solid', 'stripes', 'hatch'))

    # Draw a solid background.
    if style == 'solid':
        r = shapes.Rect(0, 0, width, height)
        r.fillColor = colour
        r.strokeColor = None
        label.add(r)

    # Both stripes and hatches need vertical stripes.
    if style in ('stripes', 'hatch'):
        g = Grid()
        g.width = width
        g.height = height
        g.delta = width/14.0                        # The width of the stripes.
        g.delta0 = random.random() * (width/14.0)   # Offset of the start of the stripe.
        g.fillColor = None
        g.strokeColor = None
        g.orientation = 'vertical'
        g.stripeColors = (colors.HexColor(0xFFFFFF), colour)
        label.add(g)

    # Draw the horizontal stripes of any hatching.
    # Note the empty parts need to be 'coloured' transparent to avoid
    # hiding the vertical stripes.
    if style == 'hatch':
        g2 = Grid()
        g2.width = width
        g2.height = height
        g2.delta = height/4.0
        g2.delta0 = random.random() * (height/4.0)
        g2.fillColor = None
        g2.strokeColor = None
        g2.orientation = 'horizontal'
        g2.stripeColors = (colors.transparent, colour)
        label.add(g2)

    # Print the label value as a string.
    label.add(shapes.String(2, 2, str(obj), fontName="Helvetica", fontSize=40))

# Create the sheet.
sheet = labels.Sheet(specs, draw_label, border=True)

# Mark some of the labels on the first page as already used.
sheet.partial_page(1, ((1, 1), (2, 2), (4, 2)))

# Add a couple of labels.
sheet.add_label("Hello")
sheet.add_label("World")

# Since the second page hasn't started yet, we can mark some of its labels as
# already used too.
sheet.partial_page(2, ((2, 1), (3, 1)))

# We can also add each item from an iterable.
sheet.add_labels(range(3, 22))

# Note that any oversize label is automatically trimmed to prevent it messing up
# other labels.
sheet.add_label("Oversized label here")

# Save the file and we are done.
sheet.save('background_colours.pdf')
print("{0:d} label(s) output on {1:d} page(s).".format(sheet.label_count, sheet.page_count))
