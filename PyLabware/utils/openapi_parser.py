import json
import logging
import sys
from copy import deepcopy
from typing import Dict, List, Optional, Union

import yaml

# Literals for parsing configurations
# $ref placeholder parameters
CONFIG_REF_PLACEHOLDER = "$ref"
CONFIG_REF_PATH_PREFIX = "#"
CONFIG_REF_PATH_SEPARATOR = "/"
# Name of the lowest level node where the actual data lives
CONFIG_DATA_NODE_KEY = "properties"

# Literals for parsing API paths
API_GETTER_METHODS = ["GET"]
API_SETTER_METHODS = ["PUT", "POST", "DELETE"]
# Name of the lowest level node where the actual data lives
API_DATA_NODE_KEY = "schema"

GET_COMMAND_TEMPLATE = {"name": None,
                        "method": None,
                        "endpoint": None,
                        "path": None,
                        "reply": {"type": None}
                        }

SET_COMMAND_TEMPLATE = {"name": None,
                        "method": None,
                        "endpoint": None,
                        "type": None,
                        "check": {},
                        "path": None
                        }


class OpenAPIParser:
    """ Simple one-shot parser to generated commands in SL2-compatible dictionary format from OpenAPI definitions.
    """

    def __init__(self, yamlfile: str = None, jsonfile: str = None):

        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

        # Only one of JSON or YAML files has to bre provided
        if (yamlfile and jsonfile) or not (yamlfile or jsonfile):
            raise ValueError("One of - JSON or YAML file name - has to be provided!")
        if yamlfile:
            self.logger.info("Reading YAML file...")
            with open(yamlfile, encoding='utf-8') as f:
                self.openapi_config = yaml.safe_load(f)
        # YAML can read correct JSON as well, but let's not rely on that
        if jsonfile:
            self.logger.info("Reading JSON file...")
            with open(jsonfile, encoding='utf-8') as f:
                self.openapi_config = json.load(f)
        # Get top level version and description, remove them from dict
        self.openapi_info = self.openapi_config.pop("info", None)
        self.openapi_paths = self.openapi_config.pop("paths", None)
        self.logger.info("Loaded OpenAPI configuration.")

        self.all_commands = []

    def run(self) -> None:
        """ Generates command dictionary from JSON/YAML OpenAPI configration
        and prints it out
        """
        self.all_commands = []
        # Replaces all $ref entries in config with what they point to
        self.logger.info("run():: Replacing references in schemas...")
        self.recursive_replace_refs(self.openapi_config, self.openapi_config)
        # Now openapi_config contains fully unwrapped configuration specification
        # We can use it as reference dict to update paths
        self.logger.info("run():: Replacing references in paths...")
        self.recursive_replace_refs(self.openapi_paths, self.openapi_config)

        # Now we have full configuration starting from API paths with all parameters populated.
        # We can create our command dictionaries
        self.logger.info("run():: Building command set...")
        for endpoint_name, path in self.openapi_paths.items():

            # Get full list of parameters for every endpoint (everything in schema)
            endpoint_data = self.recursive_find_dict_key(path, API_DATA_NODE_KEY)
            if endpoint_data != []:

                # Now we need to construct a command for each item in endpoint data
                # entry is a dict {"path":List, "data":Dict}
                # entry["data"] usually contains multiple parameters, e.g.
                # {'systemClass': {'type': 'string', 'readOnly': True, 'nullable': True},
                #  'systemLine': {'type': 'string', 'readOnly': True, 'nullable': True},
                #  ...
                # }
                # which have to be split to separate SL2 commands
                # entry["path"] is a node path in JSON schema to the data dict
                for entry in endpoint_data:
                    for param_name, param_dict in entry["data"].items():
                        # First, get rid of fucking useless oneOf keys
                        # They are used for JSON schema validation, absolute PITA
                        # for parameters parsing
                        self.recursive_reduce(param_dict, "oneOf")
                        if not isinstance(param_dict, dict):
                            self.logger.warning("run():: Wrong parameter configuration for %s %s.%s - not a dictionary!", endpoint_name, '.'.join(entry['path']), param_name)
                            continue
                        self.all_commands.extend(self.make_command(endpoint_name, entry["path"], param_name, param_dict))
            else:
                self.logger.warning("run():: No schema found for endpoint %s", endpoint_name)

    def print_commands(self, stream=None, fstring: str = "{0} = {1}\n") -> None:
        """ Prints out generated command set in the required format.
            Use the following placeholders for commands:
            {0} - command name
            {1} - command body
        """

        if stream is None:
            stream = sys.stdout
        for cmd in self.all_commands:
            stream.write(fstring.format(cmd["name"], cmd))

    def print_getters_setters(self, stream=None) -> None:
        """ Prints out minimal set of SL2 setter/getter functions for all commands
        """

        getter = """def {0}(self) -> {1}:
    \"\"\"
    \"\"\"\n
    return self.send(self.cmd.{2})\n\n"""

        setter = """def {0}(self, value: {1}) -> None:
    \"\"\"
    \"\"\"\n
    self.send(self.cmd.{2}, value)\n\n"""

        if stream is None:
            stream = sys.stdout

        for cmd in self.all_commands:
            funcname = cmd["name"].lower()
            if cmd["method"] in API_GETTER_METHODS:
                stream.write(getter.format(funcname, cmd["reply"]["type"].__name__, cmd["name"]))
            else:
                stream.write(setter.format(funcname, cmd["type"].__name__, cmd["name"]))

    def recursive_replace_refs(self, search_dict: Union[Dict, List], refs_dict: Dict) -> None:
        """ Recursively goes through the container <search_dict> and replaces all
        occurrences of the {REF_PLACEHOLDER:ref} with the corresponding node
        extracted from refs_dict
        """

        self.logger.debug("recursive_replace_refs():: Searching in: %s", search_dict)
        # Unify iterable syntax for dicts and lists
        if isinstance(search_dict, dict):
            iter_seq = search_dict.copy().items()
        elif isinstance(search_dict, list):
            iter_seq = enumerate(search_dict.copy())
        for key, value in iter_seq:
            # If value is another container - recur
            if isinstance(value, dict) or isinstance(value, list):
                self.logger.debug("recursive_replace_refs():: %s - going in", key)
                self.recursive_replace_refs(value, refs_dict)
            # If key is ref placeholder - replace
            elif key == CONFIG_REF_PLACEHOLDER:
                # Get replacement node path
                replacement_node_path = value.strip(CONFIG_REF_PATH_PREFIX + CONFIG_REF_PATH_SEPARATOR).split(CONFIG_REF_PATH_SEPARATOR)
                self.logger.debug("recursive_replace_refs():: Replacement path: %s", replacement_node_path)
                replacement_object = refs_dict
                # Descend down the path through refs_dict and get the node
                for node in replacement_node_path:
                    replacement_object = replacement_object[node]
                #  If there's another DATA_NODE_KEY within the replacement object (e.g. enum with description) - extract it
                # This might be a bit dodgy as properties would be better extracted recursively too
                if CONFIG_DATA_NODE_KEY in replacement_object.keys():
                    replacement_object = replacement_object[CONFIG_DATA_NODE_KEY]
                self.logger.debug("recursive_replace_refs():: Search dict: %s", search_dict)
                self.logger.debug("recursive_replace_refs():: Replacement: %s", replacement_object)
                search_dict.pop(key)
                # Otherwise just replace with the found node itself
                search_dict.update(replacement_object)
            else:
                self.logger.debug("recursive_replace_refs()::%s - skipping", key)
                continue

    def recursive_find_dict_key(self,
                                search_dict: Dict,
                                key_to_find: str,
                                path: Optional[List] = None,
                                results: Optional[List] = None) -> Dict:
        """ Recursively searches search_dict for given key_name and returns it's value
        and the path to it as a list
        """
        if path is None:
            path = []
        if results is None:
            results = []
        keys = search_dict.keys()
        self.logger.debug("recursive_find_dict_key():: Searching path %s\nTop-level keys: %s", path, list(keys))
        for key in keys:
            path.append(key)
            self.logger.debug("recursive_find_dict_key():: Checking %s...", path)
            if key == key_to_find:
                self.logger.debug("recursive_find_dict_key()::>>>>Found %s in %s", key_to_find, path)
                results.append({"path": path.copy(), "data": search_dict[key]})
                path.pop()
                continue
            else:
                if isinstance(search_dict[key], dict):
                    self.logger.debug("recursive_find_dict_key():: Going in.")
                    # Jump into the rabbit hole
                    self.recursive_find_dict_key(search_dict[key], key_to_find, path, results)
                else:
                    self.logger.debug("recursive_find_dict_key():: Skipping.")
            path.pop()
        return results

    def recursive_reduce(self, search_dict, key_to_remove):
        """ Recursively goes through the dictionary and replaces all key_to_remove
        hits with key_to_remove values, e.g.:
        d={"k1":v1, "k2":v2, "k3":[{"k4":v4}]}
        -> recursive_reduce(d, k3) ->
        {"k1":v1, "k2":v2, ""k4":v4}
        This function ASSUMES that the value of key_to_remove is a list with dictionaries.
        """
        if not isinstance(search_dict, dict):
            return
        parent_dict = search_dict.copy()
        for k, v in parent_dict.items():
            if k == key_to_remove:
                if isinstance(search_dict[k], list):
                    for item in search_dict[k]:
                        try:
                            search_dict.update(item)
                            # None is neede so that it wouldn't fail when it
                            # tries to pop the same key on the nex for iteration
                            # or recursion reentry
                            search_dict.pop(k, None)
                            # We have updated original dict so we need
                            # to re-run search on updated version
                            self.recursive_reduce(search_dict, key_to_remove)
                        except (TypeError, ValueError):
                            self.logger.error("recursive_reduce():: Can't update source dictionary with reduced value %s!", item)
                else:
                    self.logger.error("recursive_reduce():: Can't reduce key %s with non-iterable value %s!", k, search_dict[k])
            elif isinstance(v, dict):
                search_dict[k] = self.recursive_reduce(v, key_to_remove)
        return search_dict

    def make_command(self, endpoint_name, schema_path, param_name, param_data):
        """ Creates PyLabware command dictionary
        """
        type_mappings = {"number": float, "integer": int, "string": str, "boolean": bool, "array": list}

        self.logger.info("make_command():: Trying to build command for %s %s %s", endpoint_name, schema_path, param_name.upper())

        # There can be multiple nested values in the param_dict passed.
        # But an actual parameter entry would always have "type" key
        subparams = self.recursive_find_dict_key(param_data, "type")
        commands = []

        for param in subparams:
            # Skip array elements - we will make one command to get whole array contents
            if "items" in param["path"]:
                self.logger.info("make_command():: Skipping array path %s", param["path"])
                continue
            # Skip GET requests with non-200 reply codes
            if "get" in schema_path and "200" not in schema_path:
                self.logger.info("make_command():: Skipping non-200 GET reply path %s", param["path"])
                continue
            # Skip responses to PUT requests
            if "put" in schema_path and "responses" in schema_path:
                self.logger.info("make_command():: Skipping PUT response %s", param["path"])
                continue
            # Skip top-level containers with data type - object
            if param["data"] == "object":
                self.logger.info("make_command():: Skipping top-level object %s", param["path"])
                continue

            # Otherwise make command
            self.logger.debug("make_command():: Building command for %s", param["path"])
            method = schema_path[0].upper()
            if method in API_GETTER_METHODS:
                cmd = deepcopy(GET_COMMAND_TEMPLATE)
            elif method in API_SETTER_METHODS:
                cmd = deepcopy(SET_COMMAND_TEMPLATE)
            else:
                self.logger.warning("make_command():: Unknown method %s for endpoint %s, aborting command build.", cmd["method"], endpoint_name)
                continue

            cmd["method"] = method
            cmd["endpoint"] = endpoint_name
            # Build path
            # First element of the path is top-level variable name passed to the function call
            path = [param_name]
            # Plus any extra sub-levels
            path.extend(param["path"])
            # Last element would be always "type" -
            # that's how recursive_find_dict_key() works. Pop it
            path.pop()
            cmd["path"] = path

            # Now having the full path, we can extract relevant sub-dictionary from param_data.
            # The sub-dictionary can contain other goodies such as validation values in enum keys.
            command_data = param_data
            if len(cmd["path"]) == 1:
                command_data = param_data
            for item in cmd["path"][1:]:
                command_data = command_data[item]

            # Skip read-only properties in PUT requests
            if cmd["method"] in API_SETTER_METHODS and command_data.get("readOnly", False):
                self.logger.info("Skipping read-only property %s in method %s", cmd["path"], cmd["method"])
                continue

            # Create the name
            if cmd["method"] == "GET":
                cmd_name = cmd["method"] + "_"
            else:
                cmd_name = "SET_"
            # Update it so that it reflects the path
            cmd_name += "_".join(cmd["path"])
            cmd_name = cmd_name.upper()
            cmd["name"] = cmd_name

            # Set validation values for setters, if provided
            if method in API_SETTER_METHODS:
                # values
                if "enum" in command_data.keys():
                    cmd["check"].update({"values": command_data["enum"]})
                # min/max
                if "minimum" in command_data.keys():
                    cmd["check"].update({"min": command_data["minimum"]})
                if "maximum" in command_data.keys():
                    cmd["check"].update({"max": command_data["maximum"]})
                # If there are no hits set check to None
                if cmd["check"] == {}:
                    cmd["check"] = None

            # Finally, set type
            if method in API_GETTER_METHODS:
                cmd["reply"]["type"] = type_mappings.get(param["data"], "str")
            else:
                cmd["type"] = type_mappings.get(param["data"], "str")
            self.logger.debug("Built command %s", cmd)
            commands.append(cmd)
            self.logger.info("make_command():: Command %s built successfully.", cmd["name"])
        return commands


if __name__ == "__main__":
    import time
    from argparse import RawTextHelpFormatter, ArgumentParser

    description = "Translate OpenAPI-compatible specification into PyLabware-compatible command set.\n" \
                  "NOTE: The generated command set still requires manual editing before use.\n" \
                  "This parser was developed specifically for Buchi R300 and C815 instruments.\n" \
                  "Compatibility with any other devices is not guaranteed!\n" \

    epilog = "Three files would be generated in the current directory:\n" \
             "commands.py - command definitions & minimal getter/setter functions.\n" \
             "openapi_parser_<datetime>.log - conversion log.\n" \
             "full_schema.json - Full API schema with all references filled in.\n"

    parser = ArgumentParser(description=description, epilog=epilog, formatter_class=RawTextHelpFormatter)
    parser.add_argument("--yaml", metavar="yaml_file", type=str, help="Path to YAML file")
    parser.add_argument("--json", metavar="json_file", type=str, help="Path to JSON file")
    arg = parser.parse_args()

    # Set debug logging & redirect all below INFO to a log file
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    fh = logging.FileHandler(f"openapi_parser_{time.strftime('%d_%m_%Y_%H-%M-%S', time.gmtime())}.log")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    sh.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(sh)
    root_logger.addHandler(fh)

    if arg.yaml:
        p = OpenAPIParser(yamlfile=arg.yaml)
    elif arg.json:
        p = OpenAPIParser(jsonfile=arg.json)
    else:
        parser.print_help()
        sys.exit(0)

    # Run parser & print results to file
    # Create parser
    root_logger.info("\nStarting.\n------------------------------------")

    p.run()
    with open("commands.py", "w") as filestream:
        p.print_commands(filestream)
        filestream.write("\n\n######################################\n\n\n")
        p.print_getters_setters(filestream)

    # Dump full schema
    with open("full_schema.json", "w") as schema_file:
        schema_file.write(json.dumps(p.openapi_paths, indent=2))

    root_logger.info("Parser done.\n\n")
