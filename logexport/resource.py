from dataclasses import dataclass

from azure.mgmt.core.tools import parse_resource_id


@dataclass
class Resource:
    id: str
    name: str | None
    group: str | None
    category: str | None
    typ: str | None


def resource_from_id_and_category(id: str, category: str | None) -> Resource:
    parsed = parse_resource_id(id)
    resource = Resource(id, None, None, category, None)
    match parsed.get("name"):
        case int(name):
            resource.name = str(name)
        case other:
            resource.name = other

    match parsed.get("resource_group"):
        case int(group):
            resource.group = str(group)
        case other:
            resource.group = other

    match parsed.get("type"):
        case int(typ):
            resource.typ = str(typ)
        case other:
            resource.typ = other

    return resource
