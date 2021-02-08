# switchboard-tool-json-to-cmdi

Converters between the Switchboard tool description JSON format and the equivalent CLARIAH CMDI representation.

Usage example: convert all tools in a folder from Switchboard to CLARIAH format:

```
$ python3 switchboard_tool_json_to_cmdi.py   -I ../switchboard-tool-registry/tools
```

Reverse usage example: convert one tool from the CLARIAH format to the Switchboard format:

```
$ python3 clariah_cmdi_to_switchboard_json.py   ../application-descriptions/standalone-applications/TextGridRep.xml
```