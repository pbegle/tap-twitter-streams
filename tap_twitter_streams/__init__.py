#!/usr/bin/env python3
import json
import os

import singer
from singer import metadata, utils
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema

from tap_twitter_streams.api import stream_tweets

REQUIRED_CONFIG_KEYS = ["rules", "bearer_token"]
KEY_PROPERTIES = {"twitter_stream": ["tweet_id"]}
LOGGER = singer.get_logger()


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_schemas():
    """ Load schemas from schemas folder """
    schemas = {}
    for filename in os.listdir(get_abs_path('schemas')):
        path = get_abs_path('schemas') + '/' + filename
        file_raw = filename.replace('.json', '')
        with open(path) as file:
            schemas[file_raw] = Schema.from_dict(json.load(file))
    return schemas


def discover():
    raw_schemas = load_schemas()
    streams = []
    for stream_id, schema in raw_schemas.items():
        key_properties = KEY_PROPERTIES.get(stream_id) or []
        stream_metadata = metadata.get_standard_metadata(
            schema=schema.to_dict(),
            key_properties=key_properties
        )
        streams.append(
            CatalogEntry(
                tap_stream_id=stream_id,
                stream=stream_id,
                schema=schema,
                key_properties=key_properties,
                metadata=stream_metadata,
                replication_key=None,
                is_view=None,
                database=None,
                table=None,
                row_count=None,
                stream_alias=None,
                replication_method=None,
            )
        )
    return Catalog(streams)


def sync(config, state, catalog):
    """ Sync data from tap source """
    # Loop over selected streams in catalog
    for stream in catalog.get_selected_streams(state):
        LOGGER.info("Syncing stream:" + stream.tap_stream_id)

        stream_tweets(
            stream.tap_stream_id,
            stream.schema.to_dict(),
            stream.key_properties,
            config)

    return


@utils.handle_top_exception(LOGGER)
def main():
    # Parse command line arguments
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)
    # LOGGER.info(f"args.config: {args.config['rules']}")

    # If discover flag was passed, run discovery mode and dump output to stdout
    if args.discover:
        catalog = discover()
        catalog.dump()
    # Otherwise run in sync mode
    else:
        if args.catalog:
            catalog = args.catalog
        else:
            catalog = discover()
        sync(args.config, args.state, catalog)


if __name__ == "__main__":
    main()
