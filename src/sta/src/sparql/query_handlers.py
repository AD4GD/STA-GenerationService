from fastapi import HTTPException, status
from rdflib.term import Variable

from src.sparql.base_query_handler import BaseQueryHandler
from src.utils import get_label


class ObservationsHandler(BaseQueryHandler):
    def _get_total_count(self, where):
        query = "SELECT (COUNT(DISTINCT ?obs) AS ?count)\n"
        query += self._add_graphs_to_query()
        query += where
        try:
            total_count = int(self.query_graph.query(query).bindings[0][Variable("count")])
        except Exception as e:
            self.handle_sparql_exception(e)
        return total_count

    def _get_query_results(self, where):
        if "sosa:hasSimpleResult" in where:
            query = self.select["simple"]
        else:
            query = self.select["normal"]

        query += "\n"
        query += self._add_graphs_to_query()
        query += where
        query = query.replace("$GRAPHS_LIST$", self._add_graphs_to_query())
        if self._is_limited():
            query = query.replace("$LIMIT_OFFSET$", f"LIMIT {self.top} OFFSET {self.skip}")

        try:
            results = self.query_graph.query(query)
        except Exception as e:
            self.handle_sparql_exception(e)

        if len(results) == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return results

    def transform_binding(self, binding):
        if binding.get(Variable("result")):
            simple_result = True
        else:
            simple_result = False

        if simple_result:
            data_dict = {}
            for key, value in binding.items():
                data_dict[str(key)] = value.toPython()
        else:
            data_dict = {"result": {}}
            for key, value in binding.items():
                if key not in [Variable("p_values"), Variable("v_values")]:
                    data_dict[str(key)] = value.toPython()

            try:
                p_values = binding[Variable("p_values")].split("|")
                v_values = binding[Variable("v_values")].split("|")
                for key, value in zip(p_values, v_values):
                    key = get_label(key)
                    data_dict["result"][key] = value
            except KeyError:
                data_dict["result"] = None
        data_dict = self.make_id_and_self_link(data_dict)
        data_dict["Datastream@iot.navigationLink"] = data_dict.pop("datastream_link")
        data_dict["FeatureOfInterest@iot.navigationLink"] = data_dict.pop("feature_link")

        return data_dict


class DatastreamsHandler(BaseQueryHandler):
    def __init__(
        self,
        pilot,
        url,
        select,
        count_queries,
        where_queries,
        bits_text,
        top=None,
        skip=None,
        item_id=None,
        filter_option=None,
    ):
        super().__init__(
            pilot,
            url,
            select,
            count_queries,
            where_queries,
            bits_text,
            top=top,
            skip=skip,
            item_id=item_id,
            filter_option=filter_option,
        )
        self.graphs += ["http://qudt.org/2.1/vocab/unit", "http://www.ontology-of-units-of-measure.org/resource/om-2"]

    def transform_binding(self, binding):
        data_dict = {"unitOfMeasurement": {}}
        for key, value in binding.items():
            if key in [Variable("u_symbol"), Variable("u_name"), Variable("u_definition")]:
                data_dict["unitOfMeasurement"][str(key)[2:]] = value.toPython()
            else:
                data_dict[str(key)] = value.toPython()

        data_dict = self.make_id_and_self_link(data_dict)
        data_dict["Observations@iot.navigationLink"] = data_dict.pop("observations_link")
        data_dict["ObservedProperty@iot.navigationLink"] = data_dict.pop("observed_property_link")
        data_dict["Sensor@iot.navigationLink"] = data_dict.pop("sensor_link")
        data_dict["Thing@iot.navigationLink"] = data_dict.pop("thing_link")

        return data_dict

    def _get_total_count(self, where):
        query = "SELECT COUNT DISTINCT ?sensor ?obs_property\n"
        query += self._add_graphs_to_query()
        query += where
        try:
            total_count = int(self.query_graph.query(query).bindings[0][Variable("callret-0")])
        except Exception as e:
            self.handle_sparql_exception(e)
        return total_count


class LocationsHandler(BaseQueryHandler):
    def transform_binding(self, binding):
        data_dict = {"location": {"coordinates": [0.0, 0.0], "type": "Point"}}
        for key, value in binding.items():
            if key == Variable("lat"):
                data_dict["location"]["coordinates"][0] = float(value.toPython())
            elif key == Variable("long"):
                data_dict["location"]["coordinates"][1] = float(value.toPython())
            else:
                data_dict[str(key)] = value.toPython()

        data_dict = self.make_id_and_self_link(data_dict)
        data_dict["Things@iot.navigationLink"] = data_dict.pop("things_link")
        data_dict["HistoricalLocations@iot.navigationLink"] = data_dict.pop("historical_locations_link")

        return data_dict

    def _get_total_count(self, where):
        query = "SELECT (COUNT(DISTINCT ?foi) AS ?count)\n"
        query += self._add_graphs_to_query()
        query += where
        try:
            total_count = int(self.query_graph.query(query).bindings[0][Variable("count")])
        except Exception as e:
            self.handle_sparql_exception(e)
        return total_count


class SensorsHandler(BaseQueryHandler):
    def transform_binding(self, binding):
        data_dict = {"metadata": {}}
        for key, value in binding.items():
            if key == Variable("name"):
                data_dict[str(key)] = get_label(value.toPython())
            elif key == Variable("type"):
                data_dict["metadata"]["type"] = get_label(value.toPython())
            else:
                data_dict[str(key)] = value.toPython()

        data_dict = self.make_id_and_self_link(data_dict)
        data_dict["Datastreams@iot.navigationLink"] = data_dict.pop("datastreams_link")

        return data_dict

    def _get_total_count(self, where):
        query = "SELECT (COUNT(DISTINCT ?sensor) AS ?count)\n"
        query += self._add_graphs_to_query()
        query += where
        try:
            total_count = int(self.query_graph.query(query).bindings[0][Variable("count")])
        except Exception as e:
            self.handle_sparql_exception(e)
        return total_count


class FeaturesOfInterestHandler(BaseQueryHandler):
    def transform_binding(self, binding):
        data_dict = {"feature": {"coordinates": [0.0, 0.0], "type": "Point"}}
        for key, value in binding.items():
            if key == Variable("lat"):
                data_dict["feature"]["coordinates"][0] = float(value.toPython())
            elif key == Variable("long"):
                data_dict["feature"]["coordinates"][1] = float(value.toPython())
            else:
                data_dict[str(key)] = value.toPython()

        data_dict = self.make_id_and_self_link(data_dict)
        data_dict["Observations@iot.navigationLink"] = data_dict.pop("observations_link")

        return data_dict

    def _get_total_count(self, where):
        query = "SELECT (COUNT(DISTINCT ?foi) AS ?count)\n"
        query += self._add_graphs_to_query()
        query += where
        try:
            total_count = int(self.query_graph.query(query).bindings[0][Variable("count")])
        except Exception as e:
            self.handle_sparql_exception(e)
        return total_count


class ThingsHandler(BaseQueryHandler):
    def transform_binding(self, binding):
        data_dict = {"properties": {}}
        for key, value in binding.items():
            if key not in [Variable("p_values"), Variable("v_values"), Variable("type")]:
                data_dict[str(key)] = value.toPython()

        p_values = binding[Variable("p_values")].split("|")
        v_values = binding[Variable("v_values")].split("|")
        for key, value in zip(p_values, v_values):
            if "type" in key:
                continue
            key = get_label(key)
            data_dict["properties"][key] = value
        data_dict["properties"]["type"] = binding[Variable("type")]
        data_dict = self.make_id_and_self_link(data_dict)
        data_dict["Datastreams@iot.navigationLink"] = data_dict.pop("datastreams_link")
        data_dict["HistoricalLocations@iot.navigationLink"] = data_dict.pop("historical_locations_link")
        data_dict["Locations@iot.navigationLink"] = data_dict.pop("locations_link")

        return data_dict

    def _get_total_count(self, where):
        query = "SELECT (COUNT(DISTINCT ?sensor) AS ?count)\n"
        query += self._add_graphs_to_query()
        query += where
        try:
            total_count = int(self.query_graph.query(query).bindings[0][Variable("count")])
        except Exception as e:
            self.handle_sparql_exception(e)
        return total_count


class ObservedPropertiesHandler(BaseQueryHandler):
    def transform_binding(self, binding):
        data_dict = {}
        for key, value in binding.items():
            data_dict[str(key)] = value.toPython()

        data_dict = self.make_id_and_self_link(data_dict)
        data_dict["Datastreams@iot.navigationLink"] = data_dict.pop("datastreams_link")

        return data_dict

    def _get_total_count(self, where):
        query = "SELECT (COUNT(DISTINCT ?obs_property) AS ?count)\n"
        query += self._add_graphs_to_query()
        query += where
        try:
            total_count = int(self.query_graph.query(query).bindings[0][Variable("count")])
        except Exception as e:
            self.handle_sparql_exception(e)
        return total_count


class HistoricalLocationsHandler(BaseQueryHandler):
    def transform_binding(self, binding):
        data_dict = {}
        for key, value in binding.items():
            data_dict[str(key)] = value.toPython()

        data_dict = self.make_id_and_self_link(data_dict)
        data_dict["Locations@iot.navigationLink"] = data_dict.pop("locations_link")
        data_dict["Thing@iot.navigationLink"] = data_dict.pop("thing_link")

        return data_dict

    def _get_total_count(self, where):
        query = "SELECT (COUNT(DISTINCT ?obs) AS ?count)\n"
        query += self._add_graphs_to_query()
        query += where
        try:
            total_count = int(self.query_graph.query(query).bindings[0][Variable("count")])
        except Exception as e:
            self.handle_sparql_exception(e)
        return total_count
