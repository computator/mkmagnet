#!/usr/bin/env python
from __future__ import print_function, unicode_literals

import argparse
import re
import sys
import yaml
try:
    from urllib.parse import quote as quote_uriparam
except ImportError:
    from urllib import quote as quote_uriparam


class MagnetLink:
    @staticmethod
    def validate_hash(btih):
        if len(btih) != 40 or not re.match('[a-zA-Z0-9]{40}', btih):
            return False
        return True

    @staticmethod
    def validate_tracker_uri(uri):
        if not re.match('(https?|udp)://(([^:/@]+:)?[^:/@]+@)?(\w+\.)*\w+(:\d+)?(/|$)', uri):
            return False
        return True

    def __init__(self, btih):
        if not isinstance(btih, str):
            raise TypeError("Hash must be of type 'str'")
        self.btih = btih.lower()
        if not self.validate_hash(self.btih):
            raise ValueError("Invalid hash value")
        self.trackers = []

    def set_title(self, title):
        if not isinstance(title, str):
            raise TypeError("Title must be of type 'str'")
        self.title = title

    def add_tracker(self, uri):
        if not isinstance(uri, str):
            raise TypeError("URI must be of type 'str'")
        if not self.validate_tracker_uri(uri):
            raise ValueError("Invalid tracker URI")
        if uri not in self.trackers:
            self.trackers.append(uri)

    def __str__(self):
        params = []
        if hasattr(self, 'title'):
            params.append(('dn', self.title))
        params += [('tr', uri) for uri in self.trackers]
        return "magnet:?" + '&'.join(['xt=urn:btih:{}'.format(self.btih)] + ['='.join([k, quote_uriparam(v, safe='')]) for k, v in params])


def torrent_hash(btih):
    btih = btih.lower()
    if not MagnetLink.validate_hash(btih):
        raise argparse.ArgumentTypeError("'{}' is not a valid torrent hash".format(btih))
    return btih

def tracker_uri(uri):
    if not MagnetLink.validate_tracker_uri(uri):
        raise argparse.ArgumentTypeError("'{}' is not a valid tracker URI".format(uri))
    return uri

parser = argparse.ArgumentParser(add_help=False, prog="mkmagnet", description="Creates a magnet link from the given parameters")

srcparser = parser.add_argument_group("torrent").add_mutually_exclusive_group(required=True)
srcparser.add_argument('-h', '--hash', type=torrent_hash, help="torrent hash")
srcparser.add_argument('-f', '--file', type=argparse.FileType(), help="read parameters from YAML/JSON file (or '-' for stdin)")

detparser = parser.add_argument_group("details")
detparser.add_argument('-n', metavar='TITLE', help="torrent title")
detparser.add_argument('-t', type=tracker_uri, action='append', default=[], metavar='URI', help="tracker URI")

parser.add_argument_group("optional arguments").add_argument('--help', action='help', help="show this help message and exit")

args = parser.parse_args()

if args.hash:
    magnet = MagnetLink(args.hash)
if args.file:
    try:
        fileargs = yaml.safe_load(args.file)
    except yaml.YAMLError as e:
        sys.exit(e)
    if not fileargs:
        sys.exit("error: input file missing valid torrent data")
    btih, fileargs = fileargs.popitem()
    try:
        magnet = MagnetLink(btih)
    except TypeError:
        sys.exit("error: torrent hash must be a string".format(btih))
    except ValueError:
        sys.exit("error: '{}' is not a valid torrent hash".format(btih))

    if fileargs:
        if not isinstance(fileargs, dict):
            sys.exit("error: link options must be a dictionary")
        if 'title' in fileargs:
            magnet.set_title(fileargs['title'])
        if 'trackers' in fileargs:
            if not isinstance(fileargs['trackers'], list):
                sys.exit("error: 'trackers' must be a list")
            for tracker in fileargs['trackers']:
                try:
                    magnet.add_tracker(tracker)
                except TypeError:
                    sys.exit("error: tracker URI must be a string".format(tracker))
                except ValueError:
                    sys.exit("error: '{}' is not a valid tracker URI".format(tracker))

if args.n:
    magnet.set_title(args.n)
for tracker in args.t:
    magnet.add_tracker(tracker)

print(magnet)