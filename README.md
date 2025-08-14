# untl-to-zotero-rdf

A script for converting UNTL collection metadata into Zotero RDF format.
This script was created with the initial use case of exporting [IIPC WAC
presentations](https://digital.library.unt.edu/explore/collections/IIPCM/) from the [UNT Digital Library](https://digital.library.unt.edu).
It should similarly work to export items of presentation type from other
collections, but will need additional work for other item types.


Requirements
------------
* Python 3


Installation
------------

```bash
git clone https://github.com/ldko/untl-to-zotero-rdf.git
cd untl-to-zotero-rdf
python -m venv env
pip install -r requirements.txt
```


Usage
-----
untl_to_zotero_rdf.py [-h] [-o OUTPUT] [-y YEAR] [--cache] collection

Convert UNTL metadata into Zotero RDF format.

Downloads UNTL metadata for a UNT Digital Library collection and
produces a Zotero RDF file for import into Zotero.

positional arguments:
  collection            UNT Digital Library collection id to process

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file where Zotero RDF should be written
  -y YEAR, --year YEAR  Limits items included in the Zotero RDF output to those accessioned in the given year
  --cache               Use previously retrieved XML for your collection (helpful for dev/testing purposes)

Examples
--------
To run the script, ensure you are in the untl-to-zotero-rdf directory and
activate the virtual environment created during installation:

```bash
source env/bin/activate
```

Then you can process all IIPC WAC presentations with this command:

```bash
python untl_to_zotero_rdf.py IIPCM
```

You can also limit the output to contain items created in a specific year:

```bash
python untl_to_zotero_rdf.py IIPCM -y 2025
```

By default, output will be written to a file called `zotero_rdf.xml`.
To indicate an alternate output location, use the `-o` flag:

```bash
python untl_to_zotero_rdf.py IIPCM -y 2025 -o my_new_rdf.xml
```

Note, running the script produces a file called `cached_untl_metadata.xml`.
This is the raw data pulled from the UNT Digital Library OAI-PMH API.
This file can be used for subsequent runs of the script by indicating the
`--cache` flag. This can be useful for development and testing purposes.
