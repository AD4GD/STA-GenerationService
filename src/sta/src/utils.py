import logging
import os
from contextlib import contextmanager
from urllib.parse import urlparse

from src.database import SessionLocal
from src.settings import settings


def setup_logger():
    console_logger = logging.getLogger()
    if settings.DEBUG:
        console_logger.setLevel(logging.DEBUG)
    else:
        console_logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    console_logger.addHandler(console_handler)

    return console_logger


logger = setup_logger()


def get_label(url):
    if "#" in url:
        parts = url.rsplit("#", 1)
        label = parts[-1]
    elif "/" in url:
        parts = url.rsplit("/", 1)
        label = parts[-1]
    else:
        label = url

    return label


def get_path_after_domain(url):
    parsed_url = urlparse(url)
    subpath = parsed_url.path

    return subpath


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_manager():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def read_queries_from_files(resource_name, operation):
    count_queries = []
    where_queries = []
    bits_text = None

    for file_name in sorted(os.listdir(f"resources/{resource_name}/{operation}")):
        with open(f"resources/{resource_name}/{operation}/{file_name}") as file:
            if file_name.startswith("bits.txt"):
                bits_text = file.read()
            elif file_name.startswith("count"):
                count_queries.append(file.read())
            else:
                where_queries.append(file.read())

    return {"count": count_queries, "where": where_queries, "bits": bits_text}


def read_select_from_file(resource_name, file_name="select.rq"):
    with open(f"resources/{resource_name}/{file_name}") as file:
        select = file.read()

    return select


def get_bare_request_url(request):
    if settings.DEBUG:
        return str(request.url).split("?")[0]
    else:
        return str(request.url).split("?")[0].replace(settings.HTTP, settings.HTTPS)
