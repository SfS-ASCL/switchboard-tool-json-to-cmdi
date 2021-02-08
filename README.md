# switchboard-tool-json-to-cmdi

Converters between the Switchboard tool description JSON format and the equivalent CLARIAH CMDI representation.

## Service maintenance plan

1 a. Convert all Swithboard tools to the CLARIAH format:

```
$ cd switchboard-tool-json-to-cmdi
$ python3 switchboard_tool_json_to_cmdi.py   -I ../switchboard-tool-registry/tools
$ mv ../switchboard-tool-registry/toos/*.cmdi.xml ../../application-descriptions/switchboard-web-applications/
```

1 b. Go to the newly converted services, remove services which are already better described in the CLARIAH format, verify the changes, and commit the changes in git:

```
$ cd ../application-descriptions/switchboard-web-applications
$ git diff
$ # rm ...
$ git add .
$ git commit -m 'update switchboard tools' .
```

2 a. Convert the CLARIAH tools which are not derived from the Switchboard into the Switchboard tool JSON format:

```
$ cd switchboard-tool-json-to-cmdi
$ for f in ../application-descriptions/standalone-applications/*; do python3 clariah_cmdi_to_switchboard_json.py $f; done
$ mv *.json ../switchboard-tool-registry/tools
$ mv ../switchboard-tool-registry/tools/json_tool_template.json . # move back the template json
```

2 b. Go to the newly converted services, verify the changes and commit the desired changes in git:

```
$ cd ../switchboard-tool-registry/tools
$ git diff
$ git add .
$ git commit -m 'update tools originating from CLARIAH' .
```
