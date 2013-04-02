# -*- coding: utf-8 -*-

import logging
import requests
import os
import ConfigParser


# default ETL configuration values
_etl_defaults = {
    "log_file": None,
    "log_level": "debug",
    "workspace_path": "./data"
}


class ExtendedLogger(logging.Logger):
    """Extended logger"""
    def __init__(self, filename=None, level=None):

        levels = {  "info": logging.INFO,
                    "debug": logging.DEBUG,
                    "warn":logging.WARN,
                    "error": logging.ERROR}

        if level:
            level = level.lower()

        logging.Logger.__init__(self, "vvo", levels.get(level, logging.DEBUG))

        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        if filename and filename != '-':
            handler = logging.FileHandler(filename)
        else:
            handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.addHandler(handler)


class Context(dict):
    def __init__(self, *args, **kwargs):
        """Context for ETL configuration. You can share variables here within
        single ETL run."""

        super(Context, self).__init__(*args, **kwargs)

    def __getattr__(self, attribute):
        return self[attribute]

    def __setattr__(self, attribute, value):
        self[attribute] = value


def create_context(config_filename):
    """Create context for ETL"""
    ctx = Context()

    # load configuration
    try:
        config = ConfigParser.ConfigParser()
        config.read(config_filename or "config.ini")
    except Exception as e:
        raise Exception("Unable to load configuration: %s" % e)    

    # create logger
    ctx.logger = ExtendedLogger(
                    config.get("etl", "log_file", vars=_etl_defaults),
                    config.get("etl", "log_level", vars=_etl_defaults))

    # get root url
    try:
        ctx.root_url = config.get("sources", "root_url")
    except ConfigParser.Error:
        raise Exception("No root url specified")

    # get workspace path
    try:
        ctx.workspace_path = config.get("etl", "workspace_path")
    except ConfigParser.Error:
        workspace_path = _etl_defaults["workspace_path"]
        ctx.logger.info("Using default workspace path %s") % (workspace_path)
        ctx.workspace_path = workspace_path

    # if workspace directory does not exist, create one
    if not os.path.exists(ctx.workspace_path):
        os.makedirs(ctx.workspace_path)

    # set bulletin catalog file
    ctx.bulletin_catalog = os.path.join(ctx.workspace_path, "bulletins.json")

    # create connection session
    ctx.session = requests.Session()

    return ctx