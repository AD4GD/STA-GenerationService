from urllib.error import URLError

from fastapi import HTTPException, status
from rdflib import Graph, Namespace
from rdflib.plugins.stores.sparqlstore import SPARQLStore

from src.settings import settings


class CachedPropertiesHandler:
    def __init__(self, pilot):
        self.pilot = pilot

        if pilot.custom_endpoint:
            store = SPARQLStore(query_endpoint=pilot.custom_endpoint)
        else:
            store = SPARQLStore(query_endpoint=settings.DEFAULT_QUERY_ENDPOINT)
        self.query_graph = Graph(store)
        self.graphs = pilot.graphs

        self._bind_namespaces()

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

    def get_integer_code(self):
        integer_code = 0
        if self.has_observation_collection():
            sosa_properties = ["sosa:phenomenonTime", "sosa:resultTime", "sosa:madeBySensor", "sosa:observedProperty"]
            for bit, sosa_property in enumerate(sosa_properties):
                if self.has_property_on_observation_collection(sosa_property):
                    integer_code += 2**bit
        if self.has_normal_result():
            integer_code += 2**4
        if self.has_wgs_location():
            integer_code += 2**5
        if self.has_property_on_observation_collection("sosa:hasFeatureOfInterest"):
            integer_code += 2**6
        return integer_code

    def has_observation_collection(self):
        for graph in self.graphs:
            query = f"""
            ASK WHERE {{
              GRAPH <{graph}>{{
                ?col rdf:type/rdfs:subClassOf* sosa:ObservationCollection.
              }}
            }}
            """
            try:
                result = self.query_graph.query(query)
                if result:
                    return True
            except Exception as e:
                self.handle_sparql_exception(e)
        return False

    def has_property_on_observation_collection(self, property_name):
        for graph in self.graphs:
            query = f"""
            ASK WHERE {{
              GRAPH <{graph}>{{
                ?col rdf:type/rdfs:subClassOf* sosa:ObservationCollection;
                     {property_name}           ?v.
              }}
            }}
            """
            try:
                result = self.query_graph.query(query)
                if result:
                    return True
            except Exception as e:
                self.handle_sparql_exception(e)
        return False

    def has_normal_result(self):
        for graph in self.graphs:
            query = f"""
            ASK WHERE {{
              GRAPH <{graph}>{{
                ?obs	rdf:type/rdfs:subClassOf*	sosa:Observation;
			            sosa:hasResult              ?result.
              }}
            }}
            """
            try:
                result = self.query_graph.query(query)
                if result:
                    return True
            except Exception as e:
                self.handle_sparql_exception(e)
        return False

    def has_wgs_location(self):
        for graph in self.graphs:
            query = f"""
            ASK WHERE {{
              GRAPH <{graph}>{{
                ?foi    rdf:type/rdfs:subClassOf*   sosa:FeatureOfInterest;
                        wgs84:lat                   ?raw_lat;
                        wgs84:long                  ?raw_long.
              }}
            }}
            """
            try:
                result = self.query_graph.query(query)
                if result:
                    return True
            except Exception as e:
                self.handle_sparql_exception(e)
        return False

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
