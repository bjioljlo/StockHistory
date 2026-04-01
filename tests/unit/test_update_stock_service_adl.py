import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd

from src.FilterService.StockReportHistory import ADL_Indicator, ADL_Report
from src.UpdateStockService import UpdateStockService


class DummyDataValidationService:
    def __init__(self, config):
        self.config = config

    def validate_stock_data(self, stock_name, df_result, source="yahoo"):
        return True, [], df_result


class UpdateStockServiceADLTests(unittest.TestCase):
    def setUp(self):
        self.sql_service = MagicMock()
        self.mongo_service = MagicMock()
        self.read_load_system = MagicMock()
        self.config = {
            "app": {
                "data_validation": False,
                "auto_adl_update": True,
            },
            "external_apis": {
                "yahoo_finance": {
                    "retry_attempts": 1,
                }
            },
        }

    def _create_service(self):
        with patch("src.UpdateStockService.DataValidationService", DummyDataValidationService):
            service = UpdateStockService(
                sql_service=self.sql_service,
                mongo_service=self.mongo_service,
                read_load_system=self.read_load_system,
                config=self.config,
            )
        external = MagicMock()
        service._getExternalFactory = MagicMock()
        service._getExternalFactory.Get_instance.return_value = external
        return service, external

    def test_persist_adl_data_saves_cumulative_history(self):
        service, external = self._create_service()
        ad_index_history = pd.DataFrame(
            {
                "up_count": [10, 12, 8],
                "down_count": [5, 7, 9],
            },
            index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
        )
        external.get_full_ad_index.return_value = ad_index_history
        self.sql_service.save_adl_data.return_value = True

        result = service._persist_adl_data()

        self.assertTrue(result)
        self.sql_service.save_adl_data.assert_called_once()
        saved_df = self.sql_service.save_adl_data.call_args.args[0]
        expected_df = pd.DataFrame(
            {"ADL": [5, 10, 9]},
            index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
        )
        pd.testing.assert_frame_equal(saved_df, expected_df)

    def test_update_flow_triggers_adl_refresh_after_db_save_completion(self):
        service, _ = self._create_service()
        user_info = SimpleNamespace(TW_UpdateDate="2024-01-01")

        def fake_save(data_queue, update_adl_flag):
            item = data_queue.get()
            self.assertIsNone(item)
            data_queue.task_done()
            update_adl_flag["should_update"] = True

        with patch.object(service, "_save_stock_data_to_db", side_effect=fake_save):
            with patch.object(service, "_UpdateStockService__RunUpDateADL", return_value=True) as refresh_mock:
                service._UpdateStockService__update_stocks_common(
                    mainUserInfoDatas=user_info,
                    stock_list=[],
                    update_date_attr="TW_UpdateDate",
                    initial_date=datetime(2009, 1, 1),
                )

        refresh_mock.assert_called_once_with()
        self.assertEqual(user_info.TW_UpdateDate, str(datetime.today())[0:10])

    def test_update_flow_keeps_stock_update_committed_when_adl_refresh_fails(self):
        service, _ = self._create_service()
        user_info = SimpleNamespace(TW_UpdateDate="2024-01-01")

        def fake_save(data_queue, update_adl_flag):
            item = data_queue.get()
            self.assertIsNone(item)
            data_queue.task_done()
            update_adl_flag["should_update"] = True

        with patch.object(service, "_save_stock_data_to_db", side_effect=fake_save):
            with patch.object(service, "_UpdateStockService__RunUpDateADL", return_value=False) as refresh_mock:
                service._UpdateStockService__update_stocks_common(
                    mainUserInfoDatas=user_info,
                    stock_list=[],
                    update_date_attr="TW_UpdateDate",
                    initial_date=datetime(2009, 1, 1),
                )

        refresh_mock.assert_called_once_with()
        self.assertEqual(user_info.TW_UpdateDate, str(datetime.today())[0:10])


class ADLIndicatorPersistenceTests(unittest.TestCase):
    def test_adl_indicator_prefers_persisted_adl_history(self):
        external = MagicMock()
        persisted_adl = pd.DataFrame(
            {"ADL": [3, 8]},
            index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
        )
        external.get_full_adl.return_value = persisted_adl
        external.get_full_ad_index.return_value = pd.DataFrame()
        # Mock stock history for trading calendar - return same dates as ADL data
        stock_history = pd.DataFrame(
            {"Close": [100, 100]},
            index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
        )
        stock_history.index.name = "Date"
        external.get_stock_history.return_value = stock_history

        report = ADL_Report("adl_report", 1, external)
        indicator = ADL_Indicator("ADL", report)

        result = indicator.get_ALL_Report(pd.Timestamp("2024-01-03"))

        pd.testing.assert_frame_equal(
            result,
            pd.DataFrame({"ADL": [8]}, index=pd.to_datetime(["2024-01-03"])),
        )
        external.get_full_adl.assert_called_once()
        external.get_full_ad_index.assert_not_called()

    def test_adl_indicator_forward_fills_missing_trading_dates(self):
        external = MagicMock()
        # ADL data has only 2 dates
        persisted_adl = pd.DataFrame(
            {"ADL": [5, 10]},
            index=pd.to_datetime(["2024-01-02", "2024-01-05"]),
        )
        external.get_full_adl.return_value = persisted_adl
        # But stock history has 3 trading dates (Jan 2, 3, 5 - Jan 4 is missing because weekend/holiday)
        stock_history = pd.DataFrame(
            {"Close": [100, 101, 102]},
            index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-05"]),
        )
        stock_history.index.name = "Date"
        external.get_stock_history.return_value = stock_history

        report = ADL_Report("adl_report", 1, external)
        indicator = ADL_Indicator("ADL", report)

        # Request data for the missing date (2024-01-03)
        result = indicator.get_ALL_Report(pd.Timestamp("2024-01-03"))

        # Should return forward-filled value (5, since no new data on Jan 3)
        expected = pd.DataFrame({"ADL": [5]}, index=pd.to_datetime(["2024-01-03"]))
        pd.testing.assert_frame_equal(result, expected)


if __name__ == "__main__":
    unittest.main()
