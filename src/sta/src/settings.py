import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str = f"postgresql://{os.environ['DATABASE_USER']}:{os.environ['DATABASE_PASS']}@{os.environ['DATABASE_HOST']}:{os.environ['DATABASE_PORT']}/{os.environ['DATABASE_NAME']}"
    API_RESOURCES_NAMES: list = ["Observations", "Datastreams", "FeaturesOfInterest", "HistoricalLocations", "Locations",
                                 "ObservedProperties", "Sensors", "Things"]
    SPATIAL_FUNCTIONS_NAMES: list = ["equals", "disjoint", "touches", "within", "overlaps", "crosses", "intersects",
                                     "contains", "relate"]
    DEBUG: bool = False
    HTTP: str = "http://"
    HTTPS: str = "https://"
    DEFAULT_QUERY_ENDPOINT: str = "https://www.foodie-cloud.org/sparql"


settings = Settings()
