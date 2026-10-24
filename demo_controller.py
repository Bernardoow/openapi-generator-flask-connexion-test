"""Return generated models directly so Connexion performs JSON serialization."""

from datetime import date, datetime, timezone
from decimal import Decimal
from importlib.metadata import version
from uuid import UUID

from openapi_server import encoder
from openapi_server.models.demo_child import DemoChild
from openapi_server.models.demo_item import DemoItem
from openapi_server.models.nulls_example import NullsExample
from openapi_server.models.runtime_info import RuntimeInfo


def get_runtime():
    adapter = encoder.JSONProvider if hasattr(encoder, 'JSONProvider') else encoder.JSONEncoder
    return RuntimeInfo(
        connexion_version=version('connexion'),
        flask_version=version('flask'),
        adapter=adapter.__name__,
        include_nulls=adapter.include_nulls,
    )


def get_model():
    return DemoItem(
        id=101,
        display_name='Modelo gerado',
        note=None,
        child=DemoChild(code='child-1', comment=None),
        children=[DemoChild(code='list-1', comment='na lista')],
        lookup={'first': DemoChild(code='map-1', comment=None)},
        created_at=datetime(2024, 4, 5, 6, 7, 8, tzinfo=timezone.utc),
        birthday=date(2024, 4, 5),
        amount=Decimal('12.50'),
        token=UUID('12345678-1234-5678-1234-567812345678'),
    )


def get_list():
    return [get_model()]


def get_map():
    return {'primary': get_model()}


def get_nulls():
    return NullsExample(
        optional_label=None,
        enabled=False,
        count=0,
        label='',
        child=DemoChild(code='child-null', comment=None),
    )
