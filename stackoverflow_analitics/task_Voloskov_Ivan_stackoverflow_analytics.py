#!/usr/bin/env python3
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import logging
import yaml
import logging.config
import lxml
import lxml.etree
import re
import json

DEFAULT_LOGGING_CONFIG_FILEPATH = "logging.conf.yml"
APPLICATION_NAME = "stackoverflow_analytics"

logger = logging.getLogger(APPLICATION_NAME)

def get_xml(path_to_xml):
    """
    return xml list from file
    :param path_to_xml: path to xml file
    :return: xml list
    """
    xml = []
    with open(path_to_xml) as fin:
        for i in fin:
            xml.append(i)
    return xml

def get_stop_words(path_to_stop_words):
    """
    return list of stopword from file
    :param path_to_stop_words: path to file
    :return: list of words
    """
    stop_words = []
    with open(path_to_stop_words, encoding='koi8-r') as fin:
        for word in fin:
            stop_words.append(word.rstrip())
    return stop_words

def build_score_for_interval(xml, start_year, end_year, stop_words):
    """
    build score for words in titles
    :param xml: xml list
    :param start_year: begin year
    :param end_year: end year
    :param stop_words: list of stop words
    :return: dict of score
    """
    words_score = {}
    for x in xml:
        soup = lxml.etree.fromstring(x, parser=lxml.etree.XMLParser())
        type_id = soup.get('PostTypeId')
        year = int(soup.get('CreationDate')[:4])
        if (type_id == '1' and start_year <= year <= end_year):
            score = int(soup.get('Score'))
            title = set(re.findall("\w+", soup.get('Title').lower()))
            for word in title:
                if word not in stop_words:
                    if words_score.get(word) == None:
                        words_score[word] = score
                    else:
                        words_score[word] += score
    return words_score

def top_for_query(score, N, start, end):
    """
    return top N words
    :param score: dict word with score
    :param N: top count
    :param start: begin year
    :param end: end year
    :return: list of top words
    """
    score_list = []
    for key in score:
        score_list.append([key, score[key]])
    sorted_score_list = sorted(score_list, key=lambda score_list: score_list[0])
    sorted_score_list = sorted(sorted_score_list,
                               key=lambda sorted_score_list: sorted_score_list[1], reverse=True)
    if len(score_list) >= N:
        return sorted_score_list[:N]
    else:
        logger.warning("not enough data to answer, found %s words out of %s for period \"%s,%s\"",
                       len(score_list), N, start, end)
        return sorted_score_list

def print_answer(start, end, top):
    """print answer"""
    jsonline = json.dumps({"start": int(start), "end": int(end), "top": top}, ensure_ascii=False)
    print(jsonline)

def callback_queries(arguments):
    """callback for argparse"""
    return process_queries(arguments.questions, arguments.stop_words, arguments.queries)

def process_queries(path_questions, path_stop_words, path_queries):
    """
    answer for queries from file
    :param path_questions: path to xml stackoverflow
    :param path_stop_words: path to file with stopwords
    :param path_queries: path to file with queries
    :return: nothing
    """
    xml = get_xml(path_questions)
    logger.info("process XML dataset, ready to serve queries")
    stop_words = get_stop_words(path_stop_words)
    with open(path_queries) as fin:
        for query in fin:
            logger.debug("got query \"%s\"", query.strip())
            start_year, end_year, top_N = query.split(',')
            score = build_score_for_interval(xml, int(start_year), int(end_year), stop_words)
            top = top_for_query(score, int(top_N), int(start_year), int(end_year))
            print_answer(start_year, end_year, top)
        logger.info("finish processing queries")

def setup_parser(parser):
    parser.add_argument(
        "--questions", required=True,
        help="path to stackoverflow questions .xml"
    )
    parser.add_argument(
        "--stop-words",
        help="path to stop words .txt"
    )
    parser.add_argument(
        "--queries",
        help="path to queries .csv"
    )
    parser.set_defaults(callback=callback_queries)

def setup_logging():
    """
    setup logger from file yml
    :return:
    """
    with open(DEFAULT_LOGGING_CONFIG_FILEPATH) as config_fin:
        logging.config.dictConfig(yaml.safe_load(config_fin))

def main():
    """
    just main))
    :return:
    """
    setup_logging()
    parser = ArgumentParser(
        description="tool to provide stackoverflow analytics",
        prog="stackoverflow-analytics",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    arguments.callback(arguments)

if __name__ == "__main__":
    main()