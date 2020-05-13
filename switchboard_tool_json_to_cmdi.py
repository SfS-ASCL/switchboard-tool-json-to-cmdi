#!/usr/bin/env python3
from __future__ import print_function, absolute_import

import sys, getopt
from datetime import datetime
from os import listdir
from os.path import basename, splitext, isfile, join

import json
from xml.etree import ElementTree


HELP = """Usage:
    switchboard_tool_json_to_cmdi.py -i <SWITCHBOARD_TOOL_JSON_FILE> -o <OUTPUT_FILE_NAME>
    -- or --
    switchboard_tool_json_to_cmdi.py -I <SWITCHBOARD_TOOL_JSON_DIRECTORY>"""

NS = {'e': "http://www.clarin.eu/cmd/1", # e from envelope
      'p': "http://www.clarin.eu/cmd/1/profiles/clarin.eu:cr1:p_1588142628405"} # p from profile

LOGO_URL_PREFIX = "https://github.com/clarin-eric/switchboard-tool-registry/raw/master/logos/"

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def print_json(x):
    print(json.dumps(x, indent=4))

def set_text(root, xpath, text):
    root.find(xpath, NS).text = text

def ad_set_text(root, xpath, text):
    set_text(root, "e:Components/p:applicationDescription/" + xpath, text)

def subelement_p(parent, name):
    return ElementTree.SubElement(parent, "{{{}}}{}".format(NS['p'], name))

def ad_add_element_text(root, xpath, name, text):
    parent = root.find("e:Components/p:applicationDescription/" + xpath, NS)
    subelement_p(parent, name).text = text


def take_arguments(argv):
    try:
        opts, args = getopt.getopt(argv,"hi:o:I:")
    except getopt.GetoptError:
        print(HELP)
        sys.exit(2)

    input_file = None
    output_file = None
    input_dir = None
    for opt, arg in opts:
        if opt == '-h':
            print(HELP)
            sys.exit()
        elif opt in ("-i"):
            input_file = arg
        elif opt in ("-o"):
            output_file = arg
        elif opt in ("-I"):
            input_dir = arg

    if not input_file and not input_dir:
        eprint("Missing input file or directory argument")
        print(HELP)
        sys.exit(2)
    if not output_file and not input_dir:
        eprint("Missing output file argument")
        print(HELP)
        sys.exit(2)

    if not input_dir:
        entries = [{input_file, output_file}]
        return entries

    entries = [{'input_file': join(input_dir, f)}
             for f in listdir(input_dir)
             if isfile(join(input_dir, f)) and f.endswith(".json")]
    for e in entries:
        [name, ext] = splitext(basename(e['input_file']))
        e['output_file'] = join(input_dir, name+".cmdi.xml")
    return entries


def convert(input, output):
    set_text(output, "e:Header/e:MdCreationDate", datetime.now().isoformat())
    set_text(output, "e:Resources/e:ResourceProxyList/e:ResourceProxy/e:ResourceRef", input['homepage'])

    ad_set_text(output, "p:applicationName", input['name'])
    ad_set_text(output, "p:applicationLogo", LOGO_URL_PREFIX + input['logo'])
    if input['version']:
        ad_set_text(output, "p:version", input['version'])
    ad_set_text(output, "p:applicationSubCategory", input['task'])
    ad_set_text(output, "p:maturityLevel", input['deployment'])
    ad_set_text(output, "p:Description", input['description'])
    if input['url'] and input['url'].startswith('https://'):
        ad_set_text(output, "p:encryptedCommunication", "https ")

    if input['authentication'] and input['authentication'] != "no":
        ad_set_text(output, "p:authentication", input['authentication'])

    if input['creators']:
        ad_set_text(output, "p:Creators/p:Descriptions/p:Description", input['creators'])

    ad_set_text(output, "p:applicationContacts/p:hoster/p:location", input['location'])

    if input['contact']:
        if input['contact']['email']:
            ad_set_text(output, "p:applicationContacts/p:technicalContacts/p:contactEMail", input['contact']['email'])
        if input['contact']['person']:
            name = input['contact']['person'] or ""
            names = name.split(sep=' ', maxsplit=1)
            if names and names[0]:
                ad_set_text(output, "p:applicationContacts/p:technicalContacts/p:Person/p:firstName", names[0])
            if names and len(names) > 1 and names[1]:
                ad_set_text(output, "p:applicationContacts/p:technicalContacts/p:Person/p:lastName", names[1])

    ad_set_text(output, "p:webApplication/p:APIaccess/p:APIAccessLink/p:URL", input['url'])

    if input['langEncoding']:
        ad_set_text(output, "p:webApplication/p:APIaccess/p:APIAccessLink/p:languageEncoding", input['langEncoding'])

    parametersxml = output.find("e:Components/p:applicationDescription/p:webApplication/p:APIaccess/p:APIAccessLink/p:parameters", NS)
    for param in input['parameters']:
        pxml = subelement_p(parametersxml, "parameter")
        name = param
        if input.get('mapping') and input['mapping'].get(name):
            name = input['mapping'][name]
        subelement_p(pxml, "name").text = param
        if input['parameters'][param]:
            subelement_p(pxml, "value").text = input['parameters'][param]

    for mediatype in input['mimetypes']:
        ad_add_element_text(output, "p:inputFormats/p:inputFormat", "mediaType", mediatype)
    for lang in input['languages']:
        ad_add_element_text(output, "p:inputFormats/p:inputFormat", "supportedLanguage", lang)

    for outputtype in input['output']:
        ad_add_element_text(output, "p:outputFormats/p:outputFormat", "mediaType", outputtype)

    # if input['licence']:
    #     ad_set_text(output, "p:sourceLicence", input['licence'])



def main(argv):
    entries = take_arguments(argv)

    for entry in entries:
        with open(entry['input_file']) as f:
            input = json.load(f)
        output_tree = ElementTree.parse("./template.xml")
        convert(input, output_tree.getroot())
        output_tree.write(entry['output_file'])


if __name__ == "__main__":
    main(sys.argv[1:])
