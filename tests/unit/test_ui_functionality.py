"""
UI 功能測試
測試重構後的 Controller 與 View 層功能
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.Controller.Controller_main import Controller_main
from src.View.View_main import Main_Window
from src.Model.Model_main import Model_main


class UIControllerTests(unittest.TestCase):
    """
    測試 UI Controller 重構後功能
    """

    def setUp(self):
        """
        測試初始化
        """
        self.mock_draw_figur = MagicMock()
        self.mock_report_services = MagicMock()
        self.mock_view = MagicMock(spec=Main_Window)
        self.mock_model = MagicMock(spec=Model_main)

        # 模擬 UI 表單
        self.mock_form = MagicMock()
        self.mock_view.GetFormUI.return_value = self.mock_form

        # 模擬使用者資訊
        self.mock_model.main_user_info_data = MagicMock()
        self.mock_model.main_user_info_data.UpdateDate = "2024-01-01"

    def test_controller_main_initialization(self):
        """
        測試 Controller_main 初始化
        """
        controller = Controller_main(
            draw_figur_service=self.mock_draw_figur,
            report_services=self.mock_report_services,
            _view=self.mock_view,
            _model=self.mock_model
        )

        self.assertIsNotNone(controller)
        self.assertEqual(controller.View, self.mock_view)
        self.assertEqual(controller.Model, self.mock_model)
        self.assertIsNotNone(controller._draw_figur_service)
        self.assertIsNotNone(controller._ReportFactory)

    def test_controller_event_binding(self):
        """
        測試 UI 事件綁定功能
        """
        controller = Controller_main(
            draw_figur_service=self.mock_draw_figur,
            report_services=self.mock_report_services,
            _view=self.mock_view,
            _model=self.mock_model
        )

        # 測試 Init_Window 方法
        controller.Init_Window()

        # 驗證按鈕事件已綁定
        self.assertTrue(self.mock_form.button_addStock.clicked.connect.called)
        self.assertTrue(self.mock_form.button_deletStock.clicked.connect.called)
        self.assertTrue(self.mock_form.button_getStockHistory.clicked.connect.called)
        self.assertTrue(self.mock_form.button_runSchedule.clicked.connect.called)

    def test_controller_message_handling(self):
        """
        測試 Controller 訊息處理功能
        """
        controller = Controller_main(
            draw_figur_service=self.mock_draw_figur,
            report_services=self.mock_report_services,
            _view=self.mock_view,
            _model=self.mock_model
        )

        # 測試 handle_message 方法
        test_message = {
            "type": "update_progress",
            "progress": 50
        }

        try:
            controller.handle_message(test_message)
            # 預設實作不應該擲出例外
            success = True
        except Exception as e:
            success = False
            print(f"handle_message 失敗: {e}")

        self.assertTrue(success, "Controller 應該能夠處理訊息")

    def test_controller_view_utils_integration(self):
        """
        測試 ViewUtils 整合
        """
        from src.View.ViewUtils import creat_treeView_model

        # 測試 creat_treeView_model 函式存在
        self.assertTrue(callable(creat_treeView_model), "creat_treeView_model 應該可呼叫")

        # 測試從 Controller 匯入
        from src.Controller.Controller import creat_treeView_model as controller_import
        self.assertEqual(creat_treeView_model, controller_import, "Controller 應該匯入 ViewUtils 函式")


class ViewUtilsTests(unittest.TestCase):
    """
    測試 ViewUtils 模組功能
    """

    def test_view_utils_imports(self):
        """
        測試 ViewUtils 模組匯入
        """
        try:
            from src.View import ViewUtils
            success = True
        except ImportError as e:
            success = False
            print(f"ViewUtils 匯入失敗: {e}")

        self.assertTrue(success, "ViewUtils 模組應該可以正常匯入")

    def test_view_utils_exports(self):
        """
        測試 ViewUtils 匯出函式
        """
        from src.View import ViewUtils

        # 驗證函式存在
        self.assertTrue(hasattr(ViewUtils, 'creat_treeView_model'))
        self.assertTrue(hasattr(ViewUtils, 'set_treeView'))
        self.assertTrue(hasattr(ViewUtils, 'set_treeView2'))
        self.assertTrue(hasattr(ViewUtils, 'add_stock_List'))

        # 驗證常數存在
        self.assertTrue(hasattr(ViewUtils, 'MAIN_TITALLIST'))
        self.assertTrue(hasattr(ViewUtils, 'PICK__TITALLIST'))


if __name__ == "__main__":
    unittest.main()