"""Convert UNTL metadata into Zotero RDF format.

Downloads UNTL metadata for a UNT Digital Library collection and
produces a Zotero RDF file for import into Zotero.
"""


#!/usr/bin/env python

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from io import BytesIO
from urllib.request import urlopen

import pyuntl.untldoc


TYPES = {'image_presentation': 'presentation'}

ACCESS = {'public': 'https://digital2.library.unt.edu/vocabularies/rights-access/#public'}

MEETING_PATTERN = re.compile(r'(?P<meeting>.*\d{4})(?:[,.] (?P<locality>[^0-9]+))?')


class ZoteroXML():
    """Class for producing a Zotero RDF format file from ElementTree objects."""

    def __init__(self, records=[]):
        self.records = records

    def add_item_record(self, record_element):
        """Add a single item record."""
        self.records.append(record_element)

    def write_zotero_xml_file(self, output_path='zotero_rdf.xml'):
        """Write an XML file in Zotero RDF format."""
        rdf = ET.Element('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF')
        rdf.set('xmlns:z', 'http://www.zotero.org/namespaces/export#')
        rdf.set('xmlns:dc', 'http://purl.org/dc/elements/1.1/')
        rdf.set('xmlns:vcard', 'http://nwalsh.com/rdf/vCard#')
        rdf.set('xmlns:foaf', 'http://xmlns.com/foaf/0.1/')
        rdf.set('xmlns:dcterms', 'http://purl.org/dc/terms/')
        rdf.set('xmlns:bib', 'http://purl.org/net/biblio#')

        rdf.extend(self.records)
        tree = ET.ElementTree(rdf)
        ET.indent(tree)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)


class ZoteroItem():
    """Base class for generating Zotero records from pyuntl data."""

    def __init__(self, untl_data, **kwargs):
        self.untl_data = untl_data
        self.about_uri = self.get_about_uri()
        self.title = self.get_title()
        self.subjects = self.get_subjects()
        self.abstract = self.get_abstract()
        self.creation_date = self.get_creation_date()
        self.access = self.get_access()
        self.languages = self.get_languages()

    def get_about_uri(self):
        """Get itemURL."""
        uri = ''
        identifiers = self.untl_data.get('identifier', [])
        for identifier in identifiers:
            if identifier.get('qualifier', '') == 'itemURL':
                uri = identifier.get('content', '')
        return uri

    def get_subjects(self):
        """Get subjects."""
        subjects = []
        dc_subjects = self.untl_data.get('subject', [])
        for subject in dc_subjects:
            subject_value = subject.get('content', '')
            if subject_value:
                subjects.append(subject_value)
        return subjects

    def get_title(self):
        """Get official title."""
        official_title = ''
        titles = self.untl_data.get('title', [])
        for title in titles:
            if title.get('qualifier', '') == 'officialtitle':
                title_value = title.get('content', '')
                if title_value:
                    official_title = title_value
                    break
        return official_title

    def get_abstract(self):
        """Pull abstract from UNTL description."""
        abstract = ''
        descriptions = self.untl_data.get('description', [])
        for description in descriptions:
            if description.get('qualifier', '') == 'content':
                text = description.get('content', '')
                if text:
                    abstract = text
                    break
        return abstract

    def get_creation_date(self):
        """Get date of creation."""
        creation_date = ''
        dates = self.untl_data.get('date', [])
        for date in dates:
            if date.get('qualifier', '') == 'creation':
                date_value = date.get('content', '')
                if date_value:
                    creation_date = date_value
                    break
        return creation_date

    def get_access(self):
        """Get access rights."""
        access = ''
        rights = self.untl_data.get('rights', [])
        for right in rights:
            if right.get('qualifier', '') == 'access':
                right_value = right.get('content', '')
                if right_value:
                    access = right_value
                    break
        return ACCESS.get(access, access)

    def get_languages(self):
        """Get list of languages of an item."""
        language_list = []
        languages = self.untl_data.get('language', [])
        for language in languages:
            language_value = language.get('content', '')
            if language_value:
                language_list.append(language_value)
        return language_list


class ZoteroPresentation(ZoteroItem):
    """Class to produce Zotero XML for a conference presentation from pyuntl data."""

    def __init__(self, untl_data, **kwargs):
        super().__init__(untl_data, **kwargs)
        self.presenters = self.get_presenters()
        self.relations = self.get_relations()
        self.description = self.get_description()
        self.meeting, self.locality = self.get_meeting_name_locality()

    def generate_record(self):
        """Generate Zotero RDF XML from a untl dictionary for a presentation."""
        conference_proceedings = ET.Element('bib:ConferenceProceedings')
        conference_proceedings.set('rdf:about', self.about_uri)
        ET.SubElement(conference_proceedings, 'z:itemType').text = 'presentation'

        publisher = ET.SubElement(conference_proceedings, 'dc:publisher')
        organization = ET.SubElement(publisher, 'foaf:Organization')
        adr = ET.SubElement(organization, 'vcard:adr')
        address = ET.SubElement(adr, 'vcard:Address')
        ET.SubElement(address, 'vcard:locality').text = self.locality

        presenters_element = ET.SubElement(conference_proceedings, 'z:presenters')
        seq = ET.SubElement(presenters_element, 'rdf:Seq')
        for presenter in self.presenters:
            li = ET.SubElement(seq, 'rdf:li')
            person = ET.SubElement(li, 'foaf:Person')
            ET.SubElement(person, 'foaf:surname').text = presenter['surname']
            ET.SubElement(person, 'foaf:givenName').text = presenter['given_name']
        for subject in self.subjects:
            ET.SubElement(conference_proceedings, 'dc:subject').text = subject
        ET.SubElement(conference_proceedings, 'dc:title').text = self.title
        ET.SubElement(conference_proceedings, 'dcterms:abstract').text = self.abstract
        ET.SubElement(conference_proceedings, 'dc:date').text = self.creation_date
        for language in self.languages:
            ET.SubElement(conference_proceedings, 'z:language').text = language
        identifier = ET.SubElement(conference_proceedings, 'dc:identifier')
        uri = ET.SubElement(identifier, 'dcterms:URI')
        ET.SubElement(uri, 'rdf:value').text = self.about_uri
        ET.SubElement(conference_proceedings, 'dc:rights').text = self.access
        ET.SubElement(conference_proceedings, 'dc:description').text = self.description
        ET.SubElement(conference_proceedings, 'z:meetingName').text = self.meeting
        return conference_proceedings

    def get_presenters(self):
        """Get list of presenters"""
        presenters = []
        creators = self.untl_data.get('creator', [])
        for creator in creators:
            if creator.get('content', {}).get('type', '') == 'per':
                name = creator.get('content', {}).get('name', '') 
                if name:
                    name_parts = name.split(',', 1)
                    surname = name_parts[0].strip()
                    given_name = ''
                    if len(name_parts) == 2:
                        given_name = name_parts[1].strip()
                    presenters.append({'surname': surname,  'given_name': given_name})
        return(presenters)

    def get_meeting_name_locality(self):
        """Parse meeting name and locality from publication info."""
        meeting = ''
        locality = ''
        sources = self.untl_data.get('source', [])
        for source in sources:
            if source.get('qualifier', '') == 'conference':
                conference_info = source.get('content', '')
                if conference_info:
                     # Try and parse the info into a meeting name ending in a date,
                     #  and a locality if present.
                     info_match = MEETING_PATTERN.search(conference_info)
                     if info_match:
                         meeting = info_match.group('meeting')
                         if info_match.group('locality') is not None:
                             locality = info_match.group('locality').rstrip('.')
        return meeting, locality

    def get_relations(self):
        """Get related items."""
        relationships = []
        relations = self.untl_data.get('relation', [])
        for relation in relations:
            relation_value = relation.get('content', '')
            if relation_value:
                relationships.append(relation_value)
        return relationships

    def get_description(self):
        """Generate description containing related items info."""
        description = ''
        if self.relations:
            for relation in self.relations:
                description += f'Related to: {relation}.\n'
        return description


def get_untl_collection(collection_id):
    """Pull down UNTL metadata from a UNT Digital Library collection."""
    metadata_url = (f'https://digital.library.unt.edu/explore/collections/'
                    f'{collection_id}/oai/?verb=ListRecords&metadataPrefix=untl')
    try:
        return urlopen(metadata_url).read()
    except Exception as err:
        sys.exit(f'{err}: {metadata_url}')


def main():
    """Writes Zotero RDF metadata for UNTL objects to import into Zotero.

    Pulls collection metadata in UNTL format from the UNT Digital Library,
    converts the data from each collection item to Zotero RDF, and writes it
    to a file.
    """
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('collection',
                        help='UNT Digital Library collection id to process')
    parser.add_argument('-o', '--output',
                        help='Output file where Zotero RDF should be written',
                        default='zotero_rdf.xml')
    parser.add_argument('-y', '--year',
                        help='Limits items included in the Zotero RDF output'
                             ' to those accessioned in the given year')
    parser.add_argument('--cache',
                        help='Use previously retrieved XML for your collection'
                             ' (helpful for dev/testing purposes)',
                        action='store_true')
    args =  parser.parse_args()

    if not os.path.isfile('cached_untl_metadata.xml') or not args.cache:
        # Pull live metadata if not using cached version
        untl_metadata = get_untl_collection(args.collection)
        with open('cached_untl_metadata.xml', 'wb') as untl_f:
            untl_f.write(untl_metadata)
    tree = ET.parse('cached_untl_metadata.xml')
    zotero_xml = ZoteroXML()
    for child in tree.iter('{http://www.openarchives.org/OAI/2.0/}metadata'):
        untl_root = child[0]
        untl_dict = pyuntl.untldoc.untlxml2pydict(BytesIO(ET.tostring(untl_root, 'utf-8')))
        # If year is specified, only process items created that year.
        if args.year:
            creation_date = None
            for untl_date in untl_dict.get('date', []):
                if untl_date.get('qualifier', '') == 'creation':
                    creation_date = untl_date.get('content', '')
                    break
            if not creation_date or args.year not in creation_date:
                # Creation date is not the year indicated by user.
                continue
        record = ZoteroPresentation(untl_dict)
        presentation = record.generate_record()
        zotero_xml.add_item_record(presentation)
    zotero_xml.write_zotero_xml_file(args.output)


if __name__ == '__main__':
    main()
