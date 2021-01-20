#!/usr/bin/env python3
from argparse import ArgumentParser, FileType
import sys
import logging
import time
from time import sleep

import cbr

logger = logging.getLogger("asset")

DEFAULT_SMALL_SLEEP_TIME = 3
DEFAULT_BIG_SLEEP_TIME = 4

def do_busy_work(sleep_time=DEFAULT_SMALL_SLEEP_TIME):
    time.sleep(sleep_time)

def do_busy_work_with_full_import(sleep_time=DEFAULT_BIG_SLEEP_TIME):
    sleep(sleep_time)

def do_busy_work_with_nested_calls():
    do_busy_work()
    do_busy_work_with_full_import()


class Asset:
    def __init__(self, name: str, capital: float, interest: float):
        self.name = name
        self.capital = capital
        self.interest = interest

    def calculate_revenue(self, years: int) -> float:
        usd_course = cbr.get_usd_course
        revenue_in_usd = self.capital * ((1.0 + self.interest) ** years - 1.0)
        revenue = revenue_in_usd * usd_course
        return revenue

    @classmethod
    def build_from_str(cls, raw: str):
        logger.debug("building asset object...")
        #do_busy_work()
        #do_busy_work_with_full_import()
        #do_busy_work_with_nested_calls()
        name, capital, interest = raw.strip().split()
        capital = float(capital)
        interest = float(interest)
        asset = cls(name=name, capital=capital, interest=interest)
        return asset

    def __repr__(self):
        repr_ = f"{self.__class__.__name__}({self.name}, {self.capital}, {self.interest})"
        return repr_



def load_asset_from_file(fileio):
    logger.info("reading asset file...")
    raw = fileio.read()
    asset = Asset.build_from_str(raw)
    return asset


def process_cli_arguments(arguments):
    print_asset_revenue(arguments.asset_fin, arguments.periods)


def print_asset_revenue(asset_fin, periods):
    asset = load_asset_from_file(asset_fin)
    for period in periods:
        revenue = asset.calculate_revenue(period)
        logger.debug("asset %s for period %s gives %s", asset, period, revenue)
        print(f"{period:5}: {revenue}")
        # consider nice formatting:
        # print(f"{period:5}: {revenue:10.3f}")


def setup_parser(parser):
    parser.add_argument("-f", "--filepath", dest="asset_fin", default=sys.stdin, type=FileType("r"))
    parser.add_argument("-p", "--periods", nargs="+", type=int, metavar="YEARS", required=True)
    parser.set_defaults(callback=process_cli_arguments)


def main():
    parser = ArgumentParser(
        prog="asset",
        description="tool to forecast asset revenue",
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    arguments.callback(arguments)


if __name__ == "__main__":
    main()
