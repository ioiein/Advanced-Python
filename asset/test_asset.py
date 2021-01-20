from argparse import Namespace
from unittest.mock import call, patch

from asset import process_cli_arguments, DEFAULT_SMALL_SLEEP_TIME, DEFAULT_BIG_SLEEP_TIME

@patch("asset.load_asset_from_file")
def _test_process_arguments_call_load_once(mock_load_asset_from_file):
    with open("asset_example.txt") as fin:
        arguments = Namespace(
            asset_fin=fin,
            periods=[1,2,5],
        )
        process_cli_arguments(arguments)
        expected_calls = [
            call(fin),
            call().calculate_revenue(1),
            call().calculate_revenue(2),
            call().calculate_revenue(5),
        ]
        mock_load_asset_from_file.assert_has_calls(expected_calls, any_order=True)
        mock_load_asset_from_file.assert_called_once_with(fin)

        assert [call(1), call(2), call(5)] == mock_load_asset_from_file.return_value.calculate_revenue.call_args_list

    #assert 1 == mock_load_asset_from_file.call_count
    mock_load_asset_from_file.assert_called_once()

@patch("asset.sleep")
@patch("time.sleep")
def _test_can_mock_time_sleep(mock_time_sleep, mock_asset_sleep):
    with open("asset_example.txt") as fin:
        arguments = Namespace(
            asset_fin=fin,
            periods=[1,2,5],
        )
        process_cli_arguments(arguments)
        mock_asset_sleep.assert_called_once_with(DEFAULT_BIG_SLEEP_TIME)
        mock_time_sleep.assert_called_once_with(DEFAULT_SMALL_SLEEP_TIME)

@patch("cbr.get_usd_course")
def test_can_mock_external_calls(mock_get_usd_course):
    mock_get_usd_course.side_effect = [76.54, 77,44]
    with open("asset_example.txt") as fin:
        arguments = Namespace(
            asset_fin=fin,
            periods=[1, 1],
        )
        process_cli_arguments(arguments)