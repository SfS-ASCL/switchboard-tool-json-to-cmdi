#!/usr/bin/env python3
from __future__ import print_function, absolute_import

import sys, getopt
from datetime import date
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

def ad_remove(root, xpath):
    x = root.find("e:Components/p:applicationDescription/" + xpath, NS)
    print (x)
    x.find("..").remove(x)

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
        entries = [{'input_file':input_file, 'output_file':output_file}]
        return entries

    entries = [{'input_file': join(input_dir, f)}
             for f in listdir(input_dir)
             if isfile(join(input_dir, f)) and f.endswith(".json")]
    for e in entries:
        [name, ext] = splitext(basename(e['input_file']))
        name = join(input_dir, name+".cmdi.xml")
        name = name.replace(' -> ', '_')
        name = name.replace('->', '_')
        name = name.replace('(', '_')
        name = name.replace(')', '_')
        name = name.replace('\'s', '_')
        name = name.replace(' ', '_')
        name = name.replace('_-', '_')
        name = name.replace('-_', '_')
        name = name.replace('__', '_')
        name = name.replace('_.', '.')
        e['output_file'] = name
    return entries


def convert(input, output):
    set_text(output, "e:Header/e:MdCreationDate", date.today().isoformat())
    set_text(output, "e:Resources/e:ResourceProxyList/e:ResourceProxy/e:ResourceRef", input['homepage'].strip())

    ad_set_text(output, "p:applicationName", input['name'].strip())
    ad_set_text(output, "p:applicationLogo", LOGO_URL_PREFIX + input['logo'])
    if input.get('version'):
        ad_set_text(output, "p:softwareVersion", input['version'].strip())
    ad_set_text(output, "p:applicationSubCategory", input['task'].strip())
    ad_set_text(output, "p:maturityLevel", input['deployment'].strip())
    ad_set_text(output, "p:Description", input['description'].strip())
    if input['url'] and input['url'].startswith('https://'):
        ad_set_text(output, "p:encryptedCommunication", "https")

    if input['authentication'] and input['authentication'] != "no":
        if "Requires a CLARIN Service Provider Federation account" in input['authentication']:
            ad_set_text(output, "p:authentication", "Shibboleth")
        elif input['authentication'].startswith("Yes."):
            ad_set_text(output, "p:authentication", "proprietary")
        else:
            ad_set_text(output, "p:authentication", "unknown")
        ad_set_text(output, "p:authenticationDescription", input['authentication'].strip())

    if input['creators']:
        ad_set_text(output, "p:Creators/p:Descriptions/p:Description", input['creators'].strip())

    ad_set_text(output, "p:applicationContacts/p:hoster/p:location", input['location'].strip())

    if input['contact']:
        if input['contact']['email']:
            ad_set_text(output, "p:applicationContacts/p:technicalContacts/p:contactEMail", input['contact']['email'].strip())
        if input['contact']['person']:
            name = input['contact']['person'] or ""
            names = name.split(sep=' ', maxsplit=1)
            if names and names[0]:
                ad_set_text(output, "p:applicationContacts/p:technicalContacts/p:Person/p:firstName", names[0])
            if names and len(names) > 1 and names[1]:
                ad_set_text(output, "p:applicationContacts/p:technicalContacts/p:Person/p:lastName", names[1])

    ad_set_text(output, "p:webApplication/p:APIAccess/p:APIAccessLink/p:URL", input['url'].strip())

    if input['langEncoding']:
        ad_set_text(output, "p:webApplication/p:APIAccess/p:APIAccessLink/p:languageEncoding", input['langEncoding'].strip())

    parametersxml = output.find("e:Components/p:applicationDescription/p:webApplication/p:APIAccess/p:APIAccessLink/p:parameters", NS)
    for param in input['parameters']:
        pxml = subelement_p(parametersxml, "parameter")
        if param in ['input', 'lang', 'type']:
            pxml.set("role", param)
        name = param
        if input.get('mapping') and input['mapping'].get(name):
            name = input['mapping'][name].strip()
        subelement_p(pxml, "name").text = name
        if input['parameters'][param]:
            subelement_p(pxml, "value").text = input['parameters'][param].strip()
        else:
            subelement_p(pxml, "value")

    if input['licence']:
        ad_set_text(output, "p:webApplication/p:licenseInformation", input['licence'].strip())
    else:
        webappxml = output.find("e:Components/p:applicationDescription/p:webApplication", NS)
        license = output.find("e:Components/p:applicationDescription/p:webApplication/p:licenseInformation", NS)
        webappxml.remove(license)

    inputsxml = output.find("e:Components/p:applicationDescription/p:inputFormats", NS)
    for lang in input['languages']:
        subelement_p(inputsxml, "supportedLanguage").text = lang.strip()
    for mediatype in input['mimetypes']:
        inxml = subelement_p(inputsxml, "format")
        subelement_p(inxml, "mediaType").text = mediatype.strip()

    outputssxml = output.find("e:Components/p:applicationDescription/p:outputFormats", NS)
    for outputtype in input['output']:
        outxml = subelement_p(outputssxml, "format")
        subelement_p(outxml, "mediaType").text = outputtype.strip()



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
