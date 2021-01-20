from textwrap import dedent

import pytest
import ast
import logging

from task_Voloskov_Ivan_inverted_index import StoragePolicy, InvertedIndex, build_inverted_index, load_documents,\
    process_queries_file, process_build, process_queries_words

DATASET_SMALL_FPATH = "small_wikipedia.sample"
DATASET_TINY_FPATH = "tiny_wikipedia.sample"

SMALL_INVERTED_INDEX_PATH = "small.index"
TINY_INVERTED_INDEX_PATH = "tiny.index"

def test_can_load_documents():
    documents = load_documents(DATASET_TINY_FPATH)
    etalon_documents = {
        "123": "some words A_word and nothing",
        "2": "some word B_word in this dataset",
        "5": "famous_phrases to be or not to be",
        "37": "all words such as A_word and B_word are here",
    }
    assert etalon_documents == documents, ("load_documents incorrectly loaded dataset")

@pytest.mark.parametrize(
    "query, etalon_answer",
    [
        pytest.param(["A_word"], ["123", "37"]),
        pytest.param(["B_word"], ["2", "37"], id = "B_word"),
        pytest.param(["A_word", "B_word"], ["37"], id = "both_words"),
        pytest.param(["word does not exist"], [], id = "word does not exist"),
    ],
)
def test_query_inverted_index_intersect_result(query, etalon_answer):
    documents = load_documents(DATASET_TINY_FPATH)
    tiny_inverted_index = build_inverted_index(documents)
    answer = tiny_inverted_index.query(query)
    assert sorted(answer) == sorted(etalon_answer), (
        f"Expected answer is {etalon_answer}, but you got {answer}"
    )

@pytest.fixture()
def small_wikipedia_documents():
    documents = load_documents(DATASET_SMALL_FPATH)
    return documents

def test_can_build_and_query_inverted_index(small_wikipedia_documents):
    wikipedia_inverted_index = build_inverted_index(small_wikipedia_documents)
    doc_ids = wikipedia_inverted_index.query(["one"])
    assert isinstance(doc_ids, list), (
        "inverted index query should return list"
    )

@pytest.fixture()
def tiny_wikipedia_documents():
    documents = load_documents(DATASET_TINY_FPATH)
    return documents

@pytest.fixture()
def tiny_wikipedia_inverted_index(tiny_wikipedia_documents):
    tiny_wikipedia_inverted_index = build_inverted_index(tiny_wikipedia_documents)
    return tiny_wikipedia_inverted_index

def test_can_dump_and_load_tiny_inverted_index(tmpdir, tiny_wikipedia_inverted_index):
    index_fio = tmpdir.join("index.dump")
    tiny_wikipedia_inverted_index.dump(index_fio)
    loaded_inverted_index = InvertedIndex.load(index_fio)
    assert tiny_wikipedia_inverted_index == loaded_inverted_index, (
        "load should return the same inverted index"
    )

@pytest.fixture()
def small_wikipedia_inverted_index(small_wikipedia_documents):
    wikipedia_inverted_index = build_inverted_index(small_wikipedia_documents)
    return wikipedia_inverted_index

def test_can_dump_and_load_inverted_index(tmpdir, small_wikipedia_inverted_index):
    index_fio = tmpdir.join("index.dump")
    small_wikipedia_inverted_index.dump(index_fio)
    loaded_inverted_index = InvertedIndex.load(index_fio)
    assert small_wikipedia_inverted_index == loaded_inverted_index, (
        "load should return the same inverted index"
    )

@pytest.mark.parametrize(
    ("filepath",),
    [
        pytest.param(DATASET_TINY_FPATH, id = "tiny dataset"),
        pytest.param(DATASET_SMALL_FPATH, id = "small dataset"),
    ]
)
def test_can_dump_and_load_inverted_index_with_array_police_parametrized(filepath, tmpdir):
    index_fio = tmpdir.join("index.dump")

    documents = load_documents(filepath)
    etalon_inverted_index = build_inverted_index(documents)
    etalon_inverted_index.dump(index_fio, storage_policy = StoragePolicy)
    loaded_inverted_index = InvertedIndex.load(index_fio, storage_policy = StoragePolicy)
    assert etalon_inverted_index == loaded_inverted_index, (
        "load should return the same inverted index"
    )

def test_process_build_can_build():
    process_build(DATASET_SMALL_FPATH, SMALL_INVERTED_INDEX_PATH)

def test_process_query_can_process_all_queries(capsys, caplog):
    caplog.set_level("DEBUG")
    with open("queries.txt") as fin:
        process_queries_file(
            input=SMALL_INVERTED_INDEX_PATH,
            query_file=fin,
        )
        captured = capsys.readouterr()
        assert any("load inverted index" in message for message in caplog.messages),(
            "there is no 'load inverted index' message in logs"
        )
        assert all(record.levelno <= logging.WARNING for record in caplog.records), (
            "application is unstable, there are WARNING+ level messages in logs"
        )
        assert len(captured.out.split()) == 3

def test_process_query_can_process_all_queries_cp1251(capsys):
    with open("queries_cp1251.txt", encoding="cp1251") as fin:
        process_queries_file(
            input=SMALL_INVERTED_INDEX_PATH,
            query_file=fin,
        )
        captured = capsys.readouterr()

def test_process_query_can_process_all_queries_utf8(capsys):
    with open("queries_utf8.txt", encoding="utf-8") as fin:
        process_queries_file(
            input=SMALL_INVERTED_INDEX_PATH,
            query_file=fin,
        )
        captured = capsys.readouterr()

def test_process_query_words_can_solve_community_case(capsys):
    query = [['some', 'two']]
    process_queries_words(SMALL_INVERTED_INDEX_PATH,query)
    captured = capsys.readouterr()
    assert len(ast.literal_eval(captured.out)) == 3
