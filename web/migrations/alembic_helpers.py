# Code based on https://github.com/talkpython/data-driven-web-apps-with-flask
from alembic import op
from sqlalchemy import MetaData
from sqlalchemy import engine_from_config


def load_schema():
    config = op.get_context().config

    engine = engine_from_config(
        config.get_section(config.config_ini_section), prefix="sqlalchemy."
    )
    m = MetaData()
    m.reflect(engine, schema=engine.url.database)
    db_schema = {}
    for m_table in m.tables.values():
        db_schema[m_table.name] = []
        for m_column in m_table.c:
            db_schema[m_table.name].append(m_column.name)
    return db_schema


def table_does_not_exist(table):
    schema = load_schema()
    table_does_not_exist_value = True
    for s_table in schema:
        if s_table == table:
            table_does_not_exist_value = False
    return table_does_not_exist_value


def table_has_column(table, column):
    schema = load_schema()
    has_column = False
    if table not in schema:
        return
    for s_column in schema[table]:
        if column == s_column:
            has_column = True
    return has_column
