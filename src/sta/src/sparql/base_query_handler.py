import copy
import re
from functools import partial
from urllib.error import URLError

from fastapi import HTTPException, status
from rdflib import Graph, Namespace
from rdflib.plugins.stores.sparqlstore import SPARQLStore
from rdflib.term import Variable

from src.settings import settings


class BaseQueryHandler:
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
        self.pilot = pilot
        self.url = url
        self.select = select
        self.top = top
        self.skip = skip
        self.item_id = item_id
        self.filter_option = filter_option
        if self.filter_option is not None:
            self.count_queries = copy.deepcopy(where_queries)
        else:
            self.count_queries = copy.deepcopy(count_queries)
        self.where_queries = copy.deepcopy(where_queries)
        self.integer_codes = []
        self._extract_and_remove_codes()
        if bits_text is not None:
            self.important_bits = [int(x) for x in bits_text.split(",")]
        else:
            self.important_bits = None

        if pilot.custom_endpoint:
            store = SPARQLStore(query_endpoint=pilot.custom_endpoint)
        else:
            store = SPARQLStore(query_endpoint=settings.DEFAULT_QUERY_ENDPOINT)
        self.query_graph = Graph(store)
        self.graphs = pilot.graphs

        self._bind_namespaces()

    def _extract_and_remove_codes(self):
        pattern = r"\$CODE_(\d+)\$"

        for i in range(len(self.where_queries)):
            matches = re.findall(pattern, self.where_queries[i])
            for match in matches:
                number = int(match)
                self.integer_codes.append(number)
                self.where_queries[i] = re.sub(pattern, "", self.where_queries[i])

    def _bind_namespaces(self):
        sosa = Namespace("http://www.w3.org/ns/sosa/")
        qudt = Namespace("http://qudt.org/schema/qudt/")
        om2 = Namespace("http://www.ontology-of-units-of-measure.org/resource/om-2/")
        ogc = Namespace("http://www.opengis.net/def/observationType/OGC-OM/2.0/")
        wgs84 = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
        geo = Namespace("http://www.opengis.net/ont/geosparql#")
        dct = Namespace("http://purl.org/dc/terms/")

        self.query_graph.bind("sosa", sosa)
        self.query_graph.bind("qudt", qudt)
        self.query_graph.bind("om2", om2)
        self.query_graph.bind("ogc", ogc)
        self.query_graph.bind("wgs84", wgs84)
        self.query_graph.bind("geo", geo)
        self.query_graph.bind("dct", dct)

    def get_response(self):
        try:
            if (
                len(self.integer_codes) > 0
                and self.pilot.cached_properties is not None
                and self.item_id is not None
                and not self._is_limited()
            ):
                for code in self.integer_codes:
                    bits_same = True

                    for pos in self.important_bits:
                        mask = 1 << pos
                        bit1 = (code & mask) >> pos
                        bit2 = (self.pilot.cached_properties & mask) >> pos
                        if bit1 != bit2:
                            bits_same = False
                            break

                    if bits_same:
                        where = self.where_queries[self.integer_codes.index(code)].replace(
                            "{bare_request_url}", self.url
                        )
                        where = where.replace("{bare_request_url}", self.url)
                        where = where.replace("{pilot.name}", self.pilot.name)
                        where = where.replace("{id}", self.item_id)
                        results = self._get_query_results(where)
                        response = self.transform_binding(results.bindings[0])
                        return response
            elif len(self.integer_codes) > 0 and self.pilot.cached_properties is not None:
                for code in self.integer_codes:
                    bits_same = True
                    for pos in self.important_bits:
                        mask = 1 << pos
                        bit1 = (code & mask) >> pos
                        bit2 = (self.pilot.cached_properties & mask) >> pos
                        if bit1 != bit2:
                            bits_same = False
                            break

                    if bits_same:
                        where = self.where_queries[self.integer_codes.index(code)].replace(
                            "{bare_request_url}", self.url
                        )
                        where = where.replace("{pilot.name}", self.pilot.name)
                        if len(self.where_queries) > len(self.count_queries):
                            count = self.count_queries[0]
                        else:
                            count = self.count_queries[self.integer_codes.index(code)]

                        if self.item_id is not None:
                            where = where.replace("{id}", self.item_id)
                            count = count.replace("{id}", self.item_id)

                        if self.filter_option is not None:
                            count, where = self._add_user_filters_to_query(count, where)
                        else:
                            count = count
                        results = self._get_query_results(where)
                        total_count = self._get_total_count(count)
                        response = self._handle_results_properties(total_count)
                        for binding in results.bindings:
                            data_dict = self.transform_binding(binding)
                            response["value"].append(data_dict)

                        return response
        except HTTPException:
            pass

        if self.item_id is not None and not self._is_limited():
            for where in self.where_queries:
                where = where.replace("{bare_request_url}", self.url)
                where = where.replace("{pilot.name}", self.pilot.name)
                where = where.replace("{id}", self.item_id)

                try:
                    results = self._get_query_results(where)
                    response = self.transform_binding(results.bindings[0])

                    return response
                except Exception:
                    pass
        elif len(self.where_queries) > len(self.count_queries):
            default_count = self.count_queries[0]
            for where in self.where_queries:
                where = where.replace("{bare_request_url}", self.url)
                where = where.replace("{pilot.name}", self.pilot.name)

                try:
                    if self.filter_option is not None:
                        count, where = self._add_user_filters_to_query(default_count, where)
                    else:
                        count = default_count
                    results = self._get_query_results(where)
                    total_count = self._get_total_count(count)
                    response = self._handle_results_properties(total_count)
                    for binding in results.bindings:
                        data_dict = self.transform_binding(binding)
                        response["value"].append(data_dict)

                    return response
                except Exception:
                    pass
        else:
            for count, where in zip(self.count_queries, self.where_queries):
                where = where.replace("{bare_request_url}", self.url)
                where = where.replace("{pilot.name}", self.pilot.name)
                if self.item_id is not None:
                    where = where.replace("{id}", self.item_id)
                    count = count.replace("{id}", self.item_id)

                if self.filter_option is not None:
                    count, where = self._add_user_filters_to_query(count, where)

                total_count = self._get_total_count(count)
                if total_count > 0:
                    results = self._get_query_results(where)
                    response = self._handle_results_properties(total_count)
                    for binding in results.bindings:
                        data_dict = self.transform_binding(binding)
                        response["value"].append(data_dict)

                    return response

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    def _is_limited(self):
        return self.top is not None and self.skip is not None

    def _add_user_filters_to_query(self, count, where):
        if self.filter_option.startswith(("(", "st", "geo", "not")):
            filter_line = self._get_filter_line(self.filter_option, where)
            count, where = self._add_filter_line_to_query(count, where, filter_line)
        else:
            split_filter = self.filter_option.split()
            filter_property = split_filter[0]
            filter_operator = split_filter[1]
            filter_value = split_filter[2]
            if filter_operator == "eq":
                filter_line = f"FILTER(?{filter_property} = '{filter_value}')"
                count, where = self._add_filter_line_to_query(count, where, filter_line)

        return count, where

    def _get_filter_line(self, filter_option, where):
        filter_line = "FILTER("
        pattern = re.compile(r"(geo\.\w+|st_\w+)\((location, geography'.+?')\)")
        filter_line += pattern.sub(partial(self._replace_filter_option_with_sparql, where=where), filter_option)
        filter_line = filter_line.replace("and", "&&").replace("or", "||").replace("not", "!")
        filter_line += ")"

        return filter_line

    def _replace_filter_option_with_sparql(self, match, where):
        spatial_function_name = match.group(1)[3:]
        if spatial_function_name not in settings.SPATIAL_FUNCTIONS_NAMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Spatial relationship function: {spatial_function_name} doesn't exist",
            )
        return f'geo:sf{match.group(1).replace(".", "")[3:].replace("_", "").capitalize()}({self._transform_location_to_sparql(match.group(2), where)})'

    @staticmethod
    def _transform_location_to_sparql(function_content, where):
        geometry = function_content.replace("location, geography'", "")
        if "wgs84" in where:
            function_content = f"bif:st_geomFromText(?point_text), '{geometry}^^geo:wktLiteral"
        else:
            function_content = f"?wkt, '{geometry}^^geo:wktLiteral"

        return function_content

    @staticmethod
    def _add_filter_line_to_query(count, where, filter_line):
        last_index = count.rfind("}")
        count = f"{count[:last_index]}{filter_line}\n}}"
        last_index = where.rfind("}")
        where = f"{where[:last_index]}{filter_line}\n}}"
        return count, where

    def _get_total_count(self, where):
        try:
            query = "SELECT (COUNT(DISTINCT ?id) AS ?count)\n"
            query += self._add_graphs_to_query()
            query += where
            total_count = int(self.query_graph.query(query).bindings[0][Variable("count")])
        except ValueError:
            query = "SELECT (COUNT(DISTINCT *) AS ?count)\n"
            query += self._add_graphs_to_query()
            query += where
            try:
                total_count = int(self.query_graph.query(query).bindings[0][Variable("count")])
            except Exception as e:
                self.handle_sparql_exception(e)

        return total_count

    def _get_query_results(self, where):
        query = self.select
        query += "\n"
        query += self._add_graphs_to_query()
        query += where
        query = query.replace("$GRAPHS_LIST$", self._add_graphs_to_query())
        if self._is_limited():
            if "$LIMIT_OFFSET$" in query:
                query = query.replace("$LIMIT_OFFSET$", f"LIMIT {self.top} OFFSET {self.skip}")
            else:
                query += f"LIMIT {self.top} OFFSET {self.skip}"

        try:
            results = self.query_graph.query(query)
        except Exception as e:
            self.handle_sparql_exception(e)

        if len(results) == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return results

    def _add_graphs_to_query(self):
        query = ""
        for graph in self.graphs:
            query += f"FROM <{graph}>\n"

        return query

    def _handle_results_properties(self, total_count):
        if self.skip + self.top >= total_count:
            prepared_response = {"@iot.count": total_count, "value": []}
        else:
            prepared_response = {
                "@iot.count": total_count,
                "@iot.nextLink": f"{self.url}?$top={self.top}&$skip={self.skip + self.top}",
                "value": [],
            }

        return prepared_response

    @staticmethod
    def handle_sparql_exception(error):
        if type(error.__context__) is URLError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="SPARQL endpoint is unavailable"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="There was an error processing the query. Check assigned graphs",
            )

    def transform_binding(self, binding):
        pass

    @staticmethod
    def make_id_and_self_link(data_dict):
        data_dict["@iot.id"] = data_dict.pop("id")
        data_dict["@iot.selfLink"] = data_dict.pop("self_link")
        return data_dict
