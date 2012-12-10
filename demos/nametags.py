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

import labels
import os.path
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth
from reportlab.graphics import shapes
from reportlab.lib import colors
import random

# Create an A4 portrait (210mm x 297mm) sheets with 2 columns and 8 rows of
# labels. Each label is 90mm x 25mm with a 2mm rounded corner. The margins are
# automatically calculated.
specs = labels.sheet_specifications.create(210, 297, 2, 8, 90, 25, corner_radius=2)

# Get the path to the demos directory.
base_path = os.path.dirname(__file__)

# Add some fonts.
registerFont(TTFont('Judson Bold', os.path.join(base_path, 'Judson-Bold.ttf')))
registerFont(TTFont('KatamotzIkasi', os.path.join(base_path, 'KatamotzIkasi.ttf')))

# Create a function to draw each label. This will be given the ReportLab drawing
# object to draw on, the dimensions (NB. these will be in points, the unit
# ReportLab uses) of the label, and the name to put on the tag.
def write_name(label, width, height, name):
    # Write the title.
    label.add(shapes.String(5, height-20, "Hello, my name is",
                            fontName="Judson Bold", fontSize=20))

    # Measure the width of the name and shrink the font size until it fits.
    font_size = 50
    text_width = width - 10
    name_width = stringWidth(name, "KatamotzIkasi", font_size)
    while name_width > text_width:
        font_size *= 0.8
        name_width = stringWidth(name, "KatamotzIkasi", font_size)

    # Write out the name in the centre of the label with a random colour.
    s = shapes.String(width/2.0, 15, name, textAnchor="middle")
    s.fontName = "KatamotzIkasi"
    s.fontSize = font_size
    s.fillColor = random.choice((colors.black, colors.blue, colors.red, colors.green))
    label.add(s)

# Create the sheet.
sheet = labels.sheet.Sheet('nametags.pdf', specs, write_name, border=True)

# Use an external file as the data source. NB. we need to remove the newline
# character from each line.
with open(os.path.join(base_path, "names.txt")) as names:
    sheet.add_labels(name.strip() for name in names)

# Save the file and we are done.
sheet.save()
print("{0:d} label(s) output on {1:d} page(s).".format(sheet.labels, sheet.pages))
