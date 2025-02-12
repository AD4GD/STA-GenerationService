import os

from fastapi import FastAPI
from sqlalchemy import event
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from src import models
from src.routers.general_router import router_composite_id, router_composite_list, router_id, router_list
from src.routers.pilots import router as pilots_router
from src.routers.root import router_root
from src.settings import settings
from src.utils import get_db_manager, logger

app = FastAPI(title="OGC SensorThings API", version="1.0.0", docs_url="/")


def generate_pilot_apps():
    app.routes.clear()
    app.setup()
    app.include_router(pilots_router)

    with get_db_manager() as db:
        db: Session
        try:
            pilots = db.query(models.Pilot).all()
        except ProgrammingError:
            pilots = []
            logger.error("You need to migrate the database!")

    for pilot in pilots:
        pilot_app = FastAPI(title="OGC SensorThings API", version="1.0.0")
        pilot_app.add_api_route("/", router_root(), methods=["GET"], tags=["Base"])

        for resource_name in settings.API_RESOURCES_NAMES:
            pilot_app.add_api_route(
                f"/{resource_name}", router_list(pilot, resource_name), methods=["GET"], tags=[f"{resource_name}"]
            )
            pilot_app.add_api_route(
                f"/{resource_name}({{id}})",
                router_id(pilot, resource_name),
                methods=["GET"],
                tags=[f"{resource_name}"],
            )

        for resource_name in settings.API_RESOURCES_NAMES:
            for composite_name in os.listdir(f"resources/{resource_name}/"):
                if (
                    composite_name != "id"
                    and composite_name != "list"
                    and composite_name not in ["select.rq", "select_simple_result.rq", "select_normal_result.rq"]
                ):
                    composite_name_parts = composite_name.split("_")
                    if composite_name.endswith("_list"):
                        pilot_app.add_api_route(
                            f"/{composite_name_parts[0]}({{id}})/{composite_name_parts[1]}",
                            router_composite_list(pilot, resource_name, composite_name_parts),
                            methods=["GET"],
                            tags=[f"{composite_name_parts[0]}"],
                        )
                    else:
                        pilot_app.add_api_route(
                            f"/{composite_name_parts[0]}({{id}})/{composite_name_parts[1]}",
                            router_composite_id(pilot, resource_name, composite_name_parts),
                            methods=["GET"],
                            tags=[f"{composite_name_parts[0]}"],
                        )

        app.mount(f"/{pilot.name}/api/v1.0", pilot_app)


@event.listens_for(Session, "after_commit")
def update_apps_on_pilots_changes(session: Session):
    logger.info("Reloading API after pilots changes")
    generate_pilot_apps()


generate_pilot_apps()
