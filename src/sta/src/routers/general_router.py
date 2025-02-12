import os

from fastapi import Path, Query, Request

from src.settings import settings
from src.sparql import query_handlers
from src.utils import get_bare_request_url, read_queries_from_files, read_select_from_file

resources = {
    "Datastreams": {
        "handler": query_handlers.DatastreamsHandler,
        "select": read_select_from_file("Datastreams"),
        "list": read_queries_from_files("Datastreams", "list"),
        "id": read_queries_from_files("Datastreams", "id"),
    },
    "FeaturesOfInterest": {
        "handler": query_handlers.FeaturesOfInterestHandler,
        "select": read_select_from_file("FeaturesOfInterest"),
        "list": read_queries_from_files("FeaturesOfInterest", "list"),
        "id": read_queries_from_files("FeaturesOfInterest", "id"),
    },
    "HistoricalLocations": {
        "handler": query_handlers.HistoricalLocationsHandler,
        "select": read_select_from_file("HistoricalLocations"),
        "list": read_queries_from_files("HistoricalLocations", "list"),
        "id": read_queries_from_files("HistoricalLocations", "id"),
    },
    "Locations": {
        "handler": query_handlers.LocationsHandler,
        "select": read_select_from_file("Locations"),
        "list": read_queries_from_files("Locations", "list"),
        "id": read_queries_from_files("Locations", "id"),
    },
    "Observations": {
        "handler": query_handlers.ObservationsHandler,
        "select": {
            "simple": read_select_from_file("Observations", "select_simple_result.rq"),
            "normal": read_select_from_file("Observations", "select_normal_result.rq"),
        },
        "list": read_queries_from_files("Observations", "list"),
        "id": read_queries_from_files("Observations", "id"),
    },
    "ObservedProperties": {
        "handler": query_handlers.ObservedPropertiesHandler,
        "select": read_select_from_file("ObservedProperties"),
        "list": read_queries_from_files("ObservedProperties", "list"),
        "id": read_queries_from_files("ObservedProperties", "id"),
    },
    "Sensors": {
        "handler": query_handlers.SensorsHandler,
        "select": read_select_from_file("Sensors"),
        "list": read_queries_from_files("Sensors", "list"),
        "id": read_queries_from_files("Sensors", "id"),
    },
    "Things": {
        "handler": query_handlers.ThingsHandler,
        "select": read_select_from_file("Things"),
        "list": read_queries_from_files("Things", "list"),
        "id": read_queries_from_files("Things", "id"),
    },
}
for resource_name in settings.API_RESOURCES_NAMES:
    for composite_name in os.listdir(f"resources/{resource_name}/"):
        if (
            composite_name != "id"
            and composite_name != "list"
            and composite_name not in ["select.rq", "select_simple_result.rq", "select_normal_result.rq"]
        ):
            composite_name_parts = composite_name.split("_")
            resources[resource_name]["_".join(composite_name_parts)] = read_queries_from_files(
                resource_name, composite_name
            )


def router_list(pilot, resource_name):
    def resource_list(
        request: Request,
        top: int = Query(100, alias="$top"),
        skip: int = Query(0, alias="$skip"),
        filter_option: str = Query(None, alias="$filter"),
    ):
        url = get_bare_request_url(request)
        handler = resources[resource_name]["handler"](
            pilot,
            url,
            resources[resource_name]["select"],
            resources[resource_name]["list"]["count"],
            resources[resource_name]["list"]["where"],
            resources[resource_name]["list"]["bits"],
            top=top,
            skip=skip,
            filter_option=filter_option,
        )
        response = handler.get_response()

        return response

    return resource_list


def router_id(pilot, resource_name):
    def resource_id(request: Request, item_id: str = Path(alias="id")):
        url = get_bare_request_url(request).replace("id", item_id)
        handler = resources[resource_name]["handler"](
            pilot,
            url,
            resources[resource_name]["select"],
            resources[resource_name]["id"]["count"],
            resources[resource_name]["id"]["where"],
            resources[resource_name]["id"]["bits"],
            item_id=item_id,
        )
        response = handler.get_response()

        return response

    return resource_id


def router_composite_list(pilot, resource_name, composite_name_parts):
    def composite_list(
        request: Request,
        top: int = Query(100, alias="$top"),
        skip: int = Query(0, alias="$skip"),
        item_id: str = Path(alias="id"),
        filter_option: str = Query(None, alias="$filter"),
    ):
        url = f"{get_bare_request_url(request).replace('id', item_id).split('/v1.0/', 1)[0]}/v1.0/{resource_name}"
        handler = resources[resource_name]["handler"](
            pilot,
            url,
            resources[resource_name]["select"],
            resources[resource_name]["_".join(composite_name_parts)]["count"],
            resources[resource_name]["_".join(composite_name_parts)]["where"],
            resources[resource_name]["_".join(composite_name_parts)]["bits"],
            item_id=item_id,
            top=top,
            skip=skip,
            filter_option=filter_option,
        )
        response = handler.get_response()

        return response

    return composite_list


def router_composite_id(pilot, resource_name, composite_name_parts):
    def composite_id(
        request: Request,
        item_id: str = Path(alias="id"),
    ):
        url = f"{get_bare_request_url(request).replace('id', item_id).split('/v1.0/', 1)[0]}/v1.0/{resource_name}"
        handler = resources[resource_name]["handler"](
            pilot,
            url,
            resources[resource_name]["select"],
            resources[resource_name]["_".join(composite_name_parts)]["count"],
            resources[resource_name]["_".join(composite_name_parts)]["where"],
            resources[resource_name]["_".join(composite_name_parts)]["bits"],
            item_id=item_id,
        )
        response = handler.get_response()

        return response

    return composite_id
