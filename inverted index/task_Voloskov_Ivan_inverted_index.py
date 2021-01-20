#!/usr/bin/env python3
import struct
import sys
from io import TextIOWrapper
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType, ArgumentTypeError
import logging
import yaml
import logging.config

APPLICATION_NAME = "inverted_index"
DEFAULT_DATASET_PATH="small_wikipedia.sample"
DEFAULT_INVERTED_INDEX_STORE_PATH = "inverted.index"
DEFAULT_LOGGING_CONFIG_FILEPATH = "logging.conf.yml"

logger = logging.getLogger(APPLICATION_NAME)

class EncodedFileType(FileType):
    """overload of FileType from argparse
    """
    def __call__(self, string):
        if string == '-':
            if 'r' in self._mode:
                stdin = TextIOWrapper(sys.stdin.buffer, encoding=self._encoding)
                return stdin
            elif 'w' in self._mode:
                stdout = TextIOWrapper(sys.stdout.buffer, encoding=self._encoding)
                return stdout
            else:
                msg = 'argument "-" with mode %r' % self._mode
                raise ValueError(msg)

        try:
            return open(string, self._mode, self._bufsize, self._encoding, self._errors)
        except OSError as e:
            message = "can't open '%s': %s"
            raise ArgumentTypeError(message % (message, e)) from e

def is_utf8(s):
    """
    check for string in utf-8
    """
    for c in s:
        if ord(c) > 256:
            return 0
    return 1

class StoragePolicy:
    """Policy for storage inverted index
    """
    @staticmethod
    def dump(word_to_docs_mapping, filepath: str):
        """algorithm to store inverted index

        :param word_to_docs_mapping: inverted_index
        :param filepath: path to save inverted index
        :return: nothing
        """
        with open(filepath, "wb") as write_file:
            d = struct.pack('>I', len(word_to_docs_mapping.index))
            write_file.write(d)
            for key in word_to_docs_mapping.index:
                if (is_utf8(key) == 1):
                    write_file.write(struct.pack('>B', 1))
                    len_key = len(key.encode('utf-8'))
                    write_file.write(struct.pack('>H', len_key))
                    word = struct.pack('>{}s'.format(len_key), key.encode('utf-8'))
                    write_file.write(word)
                else:
                    write_file.write(struct.pack('>B', 0))
                    len_key = len(key.encode('utf-16'))
                    write_file.write(struct.pack('>H', len_key))
                    word = struct.pack('>{}s'.format(len_key), key.encode('utf-16'))
                    write_file.write(word)
                d = struct.pack('>H', len(word_to_docs_mapping.index[key]))
                write_file.write(d)
                for item in word_to_docs_mapping.index[key]:
                    d = struct.pack('>H', int(item))
                    write_file.write(d)

    @staticmethod
    def load(filepath: str):
        """algorithm to load inverted index

        :param filepath: path to saved inverted index
        :return: class InvertedIndex
        """
        cls = InvertedIndex()
        with open(filepath, "rb") as read_file:
            count = struct.unpack('>I', read_file.read(4))
            for i in range(int(count[0])):
                flag = struct.unpack('>B', read_file.read(1))
                l = struct.unpack('>H', read_file.read(2))
                d = read_file.read(l[0])
                code = struct.unpack('>{}s'.format(l[0]), d)
                if flag[0] == 1:
                    key = code[0].decode('utf-8')
                else:
                    key = code[0].decode('utf-16')
                cls.index[key] = set()
                c = struct.unpack('>H', read_file.read(2))
                for j in range(int(c[0])):
                    number = struct.unpack('>H', read_file.read(2))
                    cls.index[key].add(f'{number[0]}')
        return cls

class InvertedIndex:
    """
    class inverted index
    """
    def __init__(self):
        self.index = {}

    def __eq__(self, other):
        return self.index == other.index

    def query(self, words: list) -> list:
        """
        function answer for queries
        :param words: words of query
        :return: list of answer
        """
        assert isinstance(words, list), (
            "query should be provided with list of words, but user provided: "
            f"{repr(words)}"
        )
        logger.debug("query inverted index with request %s", repr(words))
        answer = None
        for word in words:
            if (answer == None):
                answer = self.index.get(word)
            else:
                answer.intersection_update(self.index.get(word))
        if answer == None:
            answer = []
        else:
            answer = list(answer)
        return answer


    def dump(self, filepath: str, storage_policy = StoragePolicy):
        storage_policy.dump(self, filepath)


    @classmethod
    def load(cls, filepath: str, storage_policy = StoragePolicy):
        logger.info("load inverted index from filepath %s", filepath)
        return storage_policy.load(filepath)


def load_documents(filepath: str):
    """
    loading documents from drive
    :param filepath: path to saved document
    :return: dict of documents
    """
    d = {}
    f = open(filepath)
    line = f.readline()
    while line:
        d[line.split('\t', 1)[0]] = line.split('\t', 1)[1].rstrip()
        line = f.readline()
    f.close()
    return d


def build_inverted_index(documents):
    """
    building inverted index
    :param documents: dict of documents
    :return: class InvertedIndex
    """
    logger.info("build inverted index for provided documents")
    inverted_index = InvertedIndex()
    for key in documents:
        for word in documents[key].split():
            if inverted_index.index.get(word) == None:
                inverted_index.index[word] = set()
            inverted_index.index.get(word).add(key)
    return inverted_index

def callback_build(arguments):
    """
    callback for command build
    :param arguments: args from argparse
    :return: nothing
    """
    return process_build(arguments.dataset_path, arguments.output)

def process_build(dataset_path, output):
    """
    building inverted index for callback_build
    :param dataset_path: path to saved documents
    :param output: path to save inverted index
    :return: nothing
    """
    logger.debug("call build subcommand with arguments: %s and %s", dataset_path, output)
    documents = load_documents(dataset_path)
    inverted_index = build_inverted_index(documents)
    inverted_index.dump(output)

def callback_query(arguments):
    """
    callback for command query
    :param arguments: args from argparse
    :return: nothing
    """
    if arguments.query:
        return process_queries_words(arguments.input, arguments.query)
    else:
        return process_queries_file(arguments.input, arguments.query_file)

def process_queries_words(input, queries):
    """
    query for command --query
    :param input: path to saved inverted index
    :param query: words to query
    :return: print answer
    """
    logger.info("read queries %s", queries)
    for query in queries:
        inverted_index = InvertedIndex.load(input)
        answers = inverted_index.query(query)
        logger.debug("use the following query to run against InvertedIndex: %s", query)
        print(*answers, sep=',')

def process_queries_file(input, query_file):
    """
    query for command --query_file_*
    :param input: path to saved inverted index
    :param query_file: file of queries
    :return: print answers
    """
    logger.info("read queries from %s", query_file)
    inverted_index = InvertedIndex.load(input)
    for query in query_file:
        query = query.strip()
        answers = inverted_index.query(query.split())
        logger.debug("use the following query to run against InvertedIndex: %s", query)
        print(*answers, sep=',')

def setup_parser(parser):
    subparser = parser.add_subparsers(help="choose command")

    build_parser = subparser.add_parser(
        "build", help="build inverted index and save into hard drive",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    build_parser.add_argument(
        "-o", "--output", default=DEFAULT_INVERTED_INDEX_STORE_PATH,
        help="path to store inverted index"
    )
    build_parser.add_argument(
        "-d", "--dataset", dest="dataset_path",
        default=DEFAULT_DATASET_PATH, required=False,
        help="path to dataset to load",
    )
    build_parser.set_defaults(callback=callback_build)

    query_parser = subparser.add_parser(
        "query", help="query inverted index",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    query_file_group = query_parser.add_mutually_exclusive_group(required=False)
    query_file_group.add_argument(
        "--query-file-utf8", dest = "query_file", type=EncodedFileType("r", encoding="utf-8"),
        default=TextIOWrapper(sys.stdin.buffer, encoding="utf-8"),
        help="query file to get queries for inverted index",
    )
    query_file_group.add_argument(
        "--query-file-cp1251", dest= "query_file", type=EncodedFileType("r", encoding="cp1251"),
        default=TextIOWrapper(sys.stdin.buffer, encoding="cp1251"),
        help="query file to get queries for inverted index",
    )
    query_parser.add_argument(
        "-i", "--index", dest="input",
        default=DEFAULT_INVERTED_INDEX_STORE_PATH,
        help="path to read inverted index"
    )
    query_parser.add_argument(
        "-q", "--query", nargs="+", action='append',
        help="query word to get queries for inverted index",
    )
    query_parser.set_defaults(callback=callback_query)

def setup_logging():
    with open(DEFAULT_LOGGING_CONFIG_FILEPATH) as config_fin:
        logging.config.dictConfig(yaml.safe_load(config_fin))

def main():
    """
    just main))
    :return:
    """
    setup_logging()
    parser = ArgumentParser(
        description="tool to build, query, dump and load inverted index",
        prog="inverted-index",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    logger.debug(arguments)
    arguments.callback(arguments)

if __name__ == "__main__":
    main()
