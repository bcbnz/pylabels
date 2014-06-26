pylabels is a Python library for creating PDFs to print sheets of
labels. It uses the `ReportLab PDF
toolkit <http://www.reportlab.com/software/opensource/>`_ to produce
the PDF.

Basically, the user creates a set of specifications of the label sizes
etc, writes a callback function which does the actual drawing, and gives
these two items to a Sheet object. Items are then added to the sheet
using the add\_label() method (or add\_labels() to add all items from an
iterable).

The callback function is called once for each item, being given a
ReportLab Drawing object representing the label, its width and height,
and the item to draw on the label. Any of the standard ReportLab drawing
methods can be used, with pylabels automatically adding a clipping path
around each label to prevent it interfering with other labels.

Once all the items have been added, the labels can be saved as a PDF, or
a preview of a page can be saved as an image.

Website
-------

pylabels is hosted on GitHub at https://github.com/blairbonnett/pylabels/

Examples
--------

The following examples are available in the demos directory on GitHub:

-  `Basic <https://github.com/blairbonnett/pylabels/blob/1.0.1/demos/basic.py>`_ - a introduction to the basic use of
   pylabels.
-  `Partial pages <https://github.com/blairbonnett/pylabels/blob/1.0.1/demos/partial_page.py>`_ - how to produce partial
   pages (i.e., pages with some of the labels previously used).
-  `Background colours <https://github.com/blairbonnett/pylabels/blob/1.0.1/demos/background_colours.py>`_ - examples of solid,
   striped and hatched backgrounds of different colours.
-  `Nametags <https://github.com/blairbonnett/pylabels/blob/1.0.1/demos/nametags.py>`_ - creates a set of nametags from the
   list of names in the names.txt file. Includes the use of two custom
   fonts, font size selection, and centred text.
-  `Image preview <https://github.com/blairbonnett/pylabels/blob/1.0.1/demos/preview.py>`_ - generates image previews of
   two of the pages from the nametags demo.

Demo fonts
----------

The following fonts are used in the demo scripts and are included in the
demos folder:

-  Judson Bold - http://openfontlibrary.org/en/font/judson (Open Font
   License)
-  KatamotzIkasi - http://openfontlibrary.org/en/font/katamotzikasi
   (GPL)

License
-------

Copyright (C) 2012, 2013, 2014 Blair Bonnett

pylabels is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

pylabels is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with pylabels. If not, see http://www.gnu.org/licenses/.
