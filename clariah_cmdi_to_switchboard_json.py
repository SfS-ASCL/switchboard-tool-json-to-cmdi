#!/usr/bin/env python3
from __future__ import print_function, absolute_import
import sys
import json
import os
from xml.etree import ElementTree

NS = {'c': "http://www.clarin.eu/cmd/1", # e from envelope
      'p': "http://www.clarin.eu/cmd/1/profiles/clarin.eu:cr1:p_1588142628405", # p from profile
      'x': "http://www.w3.org/XML/1998/namespace"
      }

def main(argv):
    if len(argv) != 1:
        print("Expected one argument: a CMDI file describing an application", file=sys.stderr)
        print("Arguments are:", argv, file=sys.stderr)
        sys.exit(2)

    filename = argv[0]
    tree = ElementTree.parse(filename)
    with open('json_tool_template.json') as fp:
        dest = json.load(fp)

    for srcres in tree.findall(".//c:ResourceProxy", NS):
        x = text(srcres, "./c:ResourceType")
        if x == "LandingPage":
            copy(srcres, "./c:ResourceRef", dest, 'homepage')

    srcapp = tree.find(".//c:Components/p:applicationDescription", NS)
    copy(srcapp, "./p:applicationName", dest, 'name')
    copy(srcapp, "./p:applicationLogo", dest, 'logo')
    copy(srcapp, "./p:applicationSubCategory", dest, 'task')
    copy(srcapp, "./p:maturityLevel", dest, 'deployment')

    for srcdesc in srcapp.findall("./p:Description", NS):
        copytext(srcdesc, dest, 'description')
        if attr(srcdesc, 'x:lang') == "en":
            break

    auth = text(srcapp, "./p:authentication")
    if auth not in ['none', 'not applicable', 'unknown']:
        dest['authentication'] = auth

    creators = []
    for person in srcapp.findall("./p:Creators/p:Person", NS):
        name = getperson(person)
        if name:
            creators.append(name)
    if creators:
        dest['creators'] = ", ".join(creators)

    locations = text_array(srcapp, "./p:applicationContacts/p:hoster/p:location")
    if locations:
        locations = list(set(locations))
        dest['location'] = "; ".join(sorted(locations))

    keywords = text_array(srcapp, "./p:keyword")
    if keywords:
        dest['keywords'] = keywords

    # todo: (srcapp, "./p:userSupport/p:", dest, '')

    contact = {}
    copy(srcapp, "./p:applicationContacts/p:technicalContacts/p:contactEMail", contact, 'email')
    copy(srcapp, "./p:applicationContacts/p:technicalContacts/p:website", contact, 'url')
    for person in srcapp.findall("./p:applicationContacts/p:technicalContacts/p:Person", NS):
        name = getperson(person)
        if name:
            contact['person'] = name

    if contact:
        dest['contact'] = contact

    stdapp = tree.find(".//p:standaloneApplication", NS)
    if not stdapp:
        print("No standalone application element in {}".format(filename), file=sys.stderr)
        sys.exit(2)

    input = {
        'id': 'input',
        'mediatypes': text_array(srcapp, "./p:inputFormats/p:format/p:mediaType"),
    }
    if not input['mediatypes']:
        print("No input mediatypes in {}".format(filename), file=sys.stderr)
        sys.exit(2)

    copy_all(srcapp, "./p:inputFormats/p:supportedLanguage", input, 'languages')
    dest['inputs'] = [input]

    dest['output'] = text_array(srcapp, "./p:outputFormats/p:format/p:mediaType")

    destapp = dest['standaloneApplication']
    copy_all(stdapp, "./p:availableOnDevice", destapp, 'availableOnDevice')
    copy_all(stdapp, "./p:installURL", destapp, 'installURL')

    dstdllist = []
    for downloadurl in stdapp.findall("./p:downloadURL", NS):
        dstdl = {}
        copy(downloadurl, '.', dstdl, 'url')
        copy_attr(downloadurl, 'type', dstdl, 'type')
        copy_attr(downloadurl, 'targetLang', dstdl, 'targetlang')
        copy_attr(downloadurl, 'targetlang', dstdl, 'targetlang')
        if dstdl and dstdl.get('url') != 'none':
            dstdllist.append(dstdl)
    if dstdllist:
        destapp['downloadURL'] = dstdllist

    copy(stdapp, "./p:applicationSuite", destapp, 'applicationSuite')
    copy(stdapp, "./p:featureList", destapp, 'featureList')
    copy(stdapp, "./p:permissions", destapp, 'permissions')
    copy(stdapp, "./p:releaseNotes", destapp, 'releaseNotes')
    copy(stdapp, "./p:softwareAddOn", destapp, 'softwareAddOn')
    copy(stdapp, "./p:softwareRequirements", destapp, 'softwareRequirements')
    copy(stdapp, "./p:supportingData", destapp, 'supportingData')
    datatransfer = text(stdapp, "./p:dataTransfer")
    if datatransfer in ['local', 'cloud', 'other']:
        copy(datatransfer, destapp, 'dataTransfer')

    copy_all(stdapp, "./p:licenseInformation", destapp, 'licenseInformation')

    srcruntime = stdapp.find("./p:runtimeInformation", NS)
    if srcruntime is not None:
        runtime = {}
        copy(srcruntime, "./p:memoryRequirements", runtime, "memoryRequirements")
        copy(srcruntime, "./p:storageRequirements", runtime, "storageRequirements")
        copy(srcruntime, "./p:processorRequirements", runtime, "processorRequirements")
        copy(srcruntime, "./p:fileSize", runtime, "fileSize")

        copy_all(srcruntime, "./p:runtimeEnvironment", runtime, 'runtimeEnvironment')
        copy_all(srcruntime, "./p:installationLicense", runtime, 'installationLicense')

        dstoslist = []
        for srcos in srcruntime.findall("./p:operatingSystem", NS):
            dstos = {}
            copytext(srcos, dstos, 'name')
            copy_attr(srcos, 'versionFrom', dstos, 'versionFrom')
            copy_attr(srcos, 'versionTo', dstos, 'versionTo')
            if dstos:
                dstoslist.append(dstos)
        if dstoslist:
            runtime['operatingSystem'] = dstoslist
        if runtime:
            destapp['runtimeInformation'] = runtime

    usage = {}
    copy(srcapp, "./p:usageRestrictions/p:individualUserRestrictions", usage, 'individualUserRestrictions')
    t = text(srcapp, "./p:usageRestrictions/p:countriesNotSupported")
    if t and t not in ['none']:
        usage['countriesNotSupported'] = t
    t = text(srcapp, "./p:usageRestrictions/p:countriesSupported")
    if t and t not in ['all']:
        usage['countriesSupported'] = t
    if usage:
        dest['usageRestrictions'] = usage

    newfilebase = os.path.basename(filename)
    newfilename = os.path.splitext(newfilebase)[0]
    with open(newfilename+".json", "w", encoding='utf8') as fp:
        json.dump(dest, fp, indent=4, ensure_ascii=False)
        print("Converted: {}".format(filename), file=sys.stderr)


def getperson(person):
    firstName = text(person, "./p:firstName")
    lastName = text(person, "./p:lastName")
    role = text(person, "./p:role")

    name = ""
    if firstName: name += firstName + " "
    if lastName: name += lastName
    if name and role: name += " (" + role + ")"
    return name

def text(src, path):
    x = src.find(path, NS)
    return x is not None and x.text and x.text.strip() or None

def text_array(src, path):
    all = src.findall(path, NS)
    a = []
    for x in all:
        if x.text:
            n = x.text.strip()
            if n:
                a.append(n)
    return a

def copytext(text, dst, dstkey):
    if text is None:
        return
    if not isinstance(text, str):
        text = text.text
        if text is None:
            return
    if text:
        dst[dstkey] = text.strip()

def copy(src, srcpath, dst, dstkey):
    x = src.find(srcpath, NS)
    copytext(x, dst, dstkey)

def copy_attr(src, attrname, dst, dstkey):
    x = attr(src, attrname)
    copytext(x, dst, dstkey)

def copy_all(src, srcpath, dst, dstkey):
    arr = text_array(src, srcpath)
    if arr:
        dst[dstkey] = arr

def attr(element, name):
    n = name.split(':')
    if len(n) == 1:
        name = n[0]
    else:
        assert len(n) == 2
        name = '{{{0}}}{1}'.format(NS[n[0]], n[1])
    return element.get(name)



if __name__ == "__main__":
    main(sys.argv[1:])


