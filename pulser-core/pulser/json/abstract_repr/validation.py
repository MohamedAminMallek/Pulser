# Copyright 2022 Pulser Development Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Function for validation of JSON serialization to abstract representation."""
import json
from typing import Literal

from pulser.json.abstract_repr import SCHEMAS
import fastjsonschema

registry = {
    "device-schema.json": SCHEMAS["device"]["definitions"],
    "layout-schema.json": SCHEMAS["layout"]["definitions"],
    "register-schema.json": SCHEMAS["register"]["definitions"],
    "noise-schema.json": SCHEMAS["noise"],
}

def resolve_references(schema, registry):
    if isinstance(schema, dict):
        if "$ref" in schema and schema["$ref"] in registry:
            v = schema.pop("$ref")
            schema.update(**registry[v])
            return schema
        else:
            return {
                k: resolve_references(v, registry)
                for k, v in schema.items()
            }
    elif isinstance(schema, list):
        return [resolve_references(item, registry) for item in schema]
    else:
        return schema

VALIDATORS = {
    name: fastjsonschema.compile(
        resolve_references(SCHEMAS[name], registry)
    )
    for name in ["sequence", "device", "layout", "register", "noise"]
}

def validate_abstract_repr(
    obj_str: str,
    name: Literal["sequence", "device", "layout", "register", "noise"],
) -> None:
    """Validate the abstract representation of an object.

    Args:
        obj_str: A JSON-formatted string encoding the object.
        name: The type of object to validate (can be "sequence" or
        "device").
    """
    VALIDATORS[name](json.loads(obj_str))