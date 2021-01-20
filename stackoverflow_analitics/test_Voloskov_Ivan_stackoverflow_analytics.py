import lxml.etree
import pytest

from task_Voloskov_Ivan_stackoverflow_analytics import get_xml, get_stop_words, build_score_for_interval, top_for_query, print_answer, process_queries

XML_PATH = "test_russian1.xml"
STOP_WORDS_PATH = "stop_russian1.txt"
QUERIES_PATH = "queries_rus.csv"

def test_can_get_xml():
    xml = get_xml(XML_PATH)
    soup = lxml.etree.fromstring(xml[1], parser=lxml.etree.XMLParser())
    assert soup.get('Score') == '5'

def test_can_get_stop_words():
    stop_words = get_stop_words(STOP_WORDS_PATH)
    assert 'да' in stop_words

def test_can_build_score_for_interval():
    xml = get_xml(XML_PATH)
    stop_words = get_stop_words(STOP_WORDS_PATH)
    score = build_score_for_interval(xml, 2019, 2019, stop_words)
    assert score['дед'] == 15

def test_can_return_top():
    xml = get_xml(XML_PATH)
    stop_words = get_stop_words(STOP_WORDS_PATH)
    score = build_score_for_interval(xml, 2019, 2019, stop_words)
    top = top_for_query(score, 2, 2019, 2019)
    assert 'дед' == top[1][0]
    assert 15 == top[1][1]

def test_can_print_answer(capsys):
    xml = get_xml(XML_PATH)
    stop_words = get_stop_words(STOP_WORDS_PATH)
    score = build_score_for_interval(xml, 2019, 2019, stop_words)
    top = top_for_query(score, 2, 2019, 2019)
    print_answer('2019', '2019', top)
    captured = capsys.readouterr()
    assert "баба" in captured.out

def test_can_queries(capsys):
    process_queries(XML_PATH, STOP_WORDS_PATH, QUERIES_PATH)
    captured = capsys.readouterr()
    assert "top" in captured.out
