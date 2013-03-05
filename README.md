========
pylabels
========

pylabels is a Python library for creating PDFs to print sheets of labels. It
uses the [ReportLab PDF toolkit][1] to produce the PDF.

Basically, the user creates a set of specifications of the label sizes etc,
writes a callback function which does the actual drawing, and gives these two
items to a Sheet object. Items are then added to the sheet using the
add_label() method (or add_labels() to add all items from an iterable).

The callback function is called once for each item, being given a ReportLab
Drawing object representing the label, its width and height, and the item to
draw on the label. Any of the standard ReportLab drawing methods can be used,
with pylabels automatically adding a clipping path around each label to prevent
it interfering with other labels.

Once all the items have been added, the labels can be saved as a PDF, or a
preview of a page can be saved as an image.

[1]: http://www.reportlab.com/software/opensource/

Examples
========

The following examples are available in the demos directory:

* [Basic](demos/basic.py) - a introduction to the basic use of pylabels.
* [Partial pages](demos/partial_page.py) - how to produce partial pages (i.e.,
  pages with some of the labels previously used).
* [Nametags](demos/nametags.py) - creates a set of nametags from the list of
  names in the names.txt file. Includes the use of two custom fonts, font size
  selection, and centred text.
* [Image preview](demos/preview.py) - generates image previews of two of the
  pages from the nametags demo.

Demo fonts
==========

The following fonts are used in the demo scripts and are included in the demos
folder:

* Judson Bold - http://openfontlibrary.org/en/font/judson (Open Font License)
* KatamotzIkasi - http://openfontlibrary.org/en/font/katamotzikasi (GPL)

License
=======

Copyright (C) 2012, 2013 Blair Bonnett

pylabels is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

pylabels is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
pylabels.  If not, see <http://www.gnu.org/licenses/>.
