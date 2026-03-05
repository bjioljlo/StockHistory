from datetime import datetime, timedelta
import logging

import pandas as pd
import twstock

from src.Common import InfomationType as info
from src.Common import Tools
from src.ExternalService.ExternalDataFactory import ExternalDataFactory
from src.FilterService.StockHistory import OriginalStockByYahoo
from src.FilterService.GetStockData import All_Stock_Filters_fuc
from src.FilterService import GetStockData
from src.Model.Model import TModel
from src.Common.Parameter import RecordPickParameter


class Model_pick(TModel):
    def __init__(self, external_data_factory: ExternalDataFactory):
        super().__init__()
        self._external_data_factory = external_data_factory
        self._Groups: list[str] = None
        self._setGroups()
        self._reportService = GetStockData.ReportServices(self._external_data_factory)
        self._logger = logging.getLogger(__name__)

    @property
    def Groups(self) -> list[str]:
        if self._Groups is None:
            raise ValueError("Groups尚未初始化")
        return self._Groups

    def _setGroups(self):
        """初始化股票分類群組"""
        self._Groups = []
        for key, value in twstock.codes.items():
            if (value.group != "") and (value.group not in self._Groups):
                self._Groups.append(value.group)

    def _validate_parameters(self, params: RecordPickParameter) -> dict:
        """驗證並提取參數"""
        try:
            return {
                'GPM': float(params.GPM),
                'OPR': float(params.OPR),
                'EPS': float(params.EPS),
                'RPS': float(params.RPS),
                'monthRP_smoothAVG': int(params.monthRP_smoothAVG),  # 轉換為整數
                'monthRP_UpMpnth': int(params.monthRP_UpMpnth),      # 轉換為整數
                'PBR_low': float(params.PBR_low),
                'PBR_high': float(params.PBR_high),
                'PER_low': float(params.PER_low),
                'PER_high': float(params.PER_high),
                'ROE_low': float(params.ROE_low),
                'ROE_high': float(params.ROE_high),
                'yiled_high': float(params.yiled_high),
                'yiled_low': float(params.yiled_low),
                'OMGR': float(params.OMGR),
                'price_high': float(params.price_high),
                'price_low': float(params.price_low),
                'flash_Day': int(params.flash_Day),
                'record_Day': int(params.record_Day),
                'volum': float(params.volum),
                'PEG_low': float(params.PEG_low),
                'PEG_high': float(params.PEG_high),
                'FCF': float(params.FCF),
                'ROE_up': float(params.ROE),
                'EPS_up': float(params.EPS_up),
                'SRGR': float(params.SRGR),
                'MRGR': float(params.MRGR),
                'BerMA': float(params.BetterMA),
                'Kind': int(params.Kind),
                'avg_vol_multiple': float(params.avg_vol_multiple)
            }
        except (ValueError, AttributeError, TypeError) as e:
            self._logger.error(f"參數驗證失敗: {e}")
            raise ValueError(f"參數格式錯誤: {e}")

    def _get_valid_date(self, end_date: datetime) -> datetime:
        """取得有效的交易日期"""
        date = end_date
        max_attempts = 30  # 最多嘗試30天
        attempts = 0
        
        while attempts < max_attempts:
            try:
                stock_data = OriginalStockByYahoo(self._external_data_factory, 2330)
                price = stock_data.get_PriceByDateAndType(date, info.Price_type.Close)
                if price is not None:
                    self._logger.info(f"找到有效交易日期: {date.strftime('%Y-%m-%d')}")
                    return date
            except Exception as e:
                self._logger.warning(f"檢查日期 {date.strftime('%Y-%m-%d')} 時發生錯誤: {e}")
            
            date = date + timedelta(days=-1)
            attempts += 1
        
        raise ValueError(f"在 {max_attempts} 天內找不到有效的交易日期")

    def _merge_filter_data(self, base_data: pd.DataFrame, filter_data: pd.DataFrame, 
                          filter_name: str) -> pd.DataFrame:
        """安全地合併篩選資料"""
        if filter_data.empty:
            self._logger.warning(f"{filter_name} 篩選結果為空")
            return pd.DataFrame()  # 返回空DataFrame而不是base_data
        
        try:
            # 檢查是否有重複的列名
            base_columns = set(base_data.columns) if not base_data.empty else set()
            filter_columns = set(filter_data.columns)
            duplicate_columns = base_columns & filter_columns
            
            if duplicate_columns:
                self._logger.warning(f"{filter_name} 篩選資料有重複列名: {duplicate_columns}")
                # 為重複的列名添加後綴以避免衝突
                suffix = f"_{filter_name.replace(' ', '_')}"
                new_column_names = {}
                for col in duplicate_columns:
                    new_name = f"{col}{suffix}"
                    counter = 1
                    while new_name in base_columns or new_name in filter_columns:
                        new_name = f"{col}{suffix}_{counter}"
                        counter += 1
                    new_column_names[col] = new_name
                
                # 重命名 filter_data 中的重複列
                filter_data = filter_data.rename(columns=new_column_names)
                self._logger.info(f"重命名重複列: {new_column_names}")
            
            merged_data = pd.merge(
                base_data, filter_data, 
                left_index=True, right_index=True, how="inner",
                suffixes=('_base', '_filter')
            )
            if merged_data.empty:
                self._logger.warning(f"{filter_name} 篩選後無符合條件的股票")
            return merged_data
        except Exception as e:
            self._logger.error(f"合併 {filter_name} 篩選資料時發生錯誤: {e}")
            return base_data

    def _apply_financial_filters(self, date: datetime, params: dict) -> pd.DataFrame:
        """應用財務指標篩選"""
        # 取得財務報表資料
        financial_data = self.get_financial_statement(
            date, 
            params['GPM'], params['OPR'], params['EPS'], params['RPS']
        )
        
        if financial_data.empty:
            self._logger.warning("財務報表篩選結果為空")
            return financial_data

        # 初始化主篩選器
        mainfun = GetStockData.All_fuc(date, self._reportService.Month_index)
        mainStockfun = All_Stock_Filters_fuc(date, financial_data, OriginalStockByYahoo(self._external_data_factory))

        # 應用各項財務指標篩選
        filters_to_apply = [
            ('PBR', lambda: self._apply_report_filter(mainfun, self._reportService.PBR_index, params['PBR_high'], params['PBR_low'])),
            ('PER', lambda: self._apply_report_filter(mainfun, self._reportService.PER_index, params['PER_high'], params['PER_low'])),
            ('ROE', lambda: self._apply_report_filter(mainfun, self._reportService.ROE_index, params['ROE_high'], params['ROE_low'])),
            ('ROE成長', lambda: mainfun.get_Up_Auto(params['ROE_up'])),
            ('殖利率', lambda: self._apply_report_filter(mainfun, self._reportService.Yield_index, params['yiled_high'], params['yiled_low'])),
            ('營收成長', lambda: mainfun.get_Up_Auto(params['OMGR'])),
            ('PEG', lambda: self._apply_report_filter(mainfun, self._reportService.PEG_index, params['PEG_high'], params['PEG_low'])),
            ('自由現金流', lambda: mainfun.get_Up_Auto(params['FCF'])),
            ('EPS成長', lambda: mainfun.get_Up_Auto(params['EPS_up'])),
            ('營收年增', lambda: mainfun.get_Up_Auto(params['SRGR'])),
            ('營收月增', lambda: mainfun.get_Up_Auto(params['MRGR']))
        ]
        
        # 只有當月營收平滑和升高參數都不為0時才應用月報表平滑篩選
        if params['monthRP_smoothAVG'] > 0 and params['monthRP_UpMpnth'] > 0:
            filters_to_apply.insert(0, ('月報表平滑', lambda: mainfun.get_Smooth_Up_Auto(params['monthRP_smoothAVG'], params['monthRP_UpMpnth'])))

        result_data = financial_data
        for filter_name, filter_func in filters_to_apply:
            try:
                filter_result = filter_func()
                if not filter_result.empty:
                    result_data = self._merge_filter_data(result_data, filter_result, filter_name)
            except Exception as e:
                self._logger.error(f"應用 {filter_name} 篩選時發生錯誤: {e}")

        return result_data

    def _apply_technical_filters(self, base_data: pd.DataFrame, date: datetime, params: dict) -> pd.DataFrame:
        """應用技術指標篩選"""
        if base_data.empty:
            return base_data

        mainStockfun = All_Stock_Filters_fuc(date, base_data, OriginalStockByYahoo(self._external_data_factory))
        result_data = base_data

        # 價格篩選
        if params['price_high'] > 0 or params['price_low'] > 0:
            try:
                price_data = mainStockfun.get_Filter(
                    "price", params['price_high'], params['price_low'], info.Price_type.Close
                )
                result_data = self._merge_filter_data(result_data, price_data, "價格")
            except Exception as e:
                self._logger.error(f"價格篩選失敗: {e}")

        # 歷史高點篩選
        if params['flash_Day'] > 0 or params['record_Day'] > 0:
            try:
                record_data = mainStockfun.get_Filter_RecordHigh(
                    params['flash_Day'], params['record_Day'], info.Price_type.High
                )
                result_data = self._merge_filter_data(result_data, record_data, "歷史高點")
            except Exception as e:
                self._logger.error(f"歷史高點篩選失敗: {e}")

        # 移動平均線篩選
        if params['BerMA'] > 0:
            try:
                berma_data = mainStockfun.get_Filter_BetterMA(params['BerMA'], info.Price_type.Close)
                result_data = self._merge_filter_data(result_data, berma_data, "移動平均線")
            except Exception as e:
                self._logger.error(f"移動平均線篩選失敗: {e}")

        # 成交量篩選
        if params['avg_vol_multiple'] > 0:
            try:
                avg_vol_data = mainStockfun.get_Filter_AvgVol_Multiple(params['avg_vol_multiple'], 10)
                result_data = self._merge_filter_data(result_data, avg_vol_data, "成交量倍數")
            except Exception as e:
                self._logger.error(f"成交量倍數篩選失敗: {e}")

        if params['volum'] > 0:
            try:
                volume_data = mainStockfun.get_Filter_SMA(
                    "volume", params['volum'] * 100000000, params['volum'] * 10000, 5, info.Price_type.Volume
                )
                result_data = self._merge_filter_data(result_data, volume_data, "成交量SMA")
            except Exception as e:
                self._logger.error(f"成交量SMA篩選失敗: {e}")

        # 產業分類篩選
        if params['Kind'] > 0 and params['Kind'] <= len(self.Groups):
            try:
                group_data = mainStockfun.get_FilterInfo(self.Groups[params['Kind'] - 1])
                result_data = self._merge_filter_data(result_data, group_data, f"產業分類({self.Groups[params['Kind'] - 1]})")
            except Exception as e:
                self._logger.error(f"產業分類篩選失敗: {e}")

        return result_data

    def _apply_report_filter(self, mainfun, report_index, high_value: float, low_value: float) -> pd.DataFrame:
        """應用報表指標篩選的輔助方法"""
        mainfun.report = report_index
        return mainfun.get_Filter_Auto(high_value, low_value)

    # 全部篩選
    def RunFilte(self, params: RecordPickParameter, end_date: datetime) -> pd.DataFrame:
        """執行完整的股票篩選流程"""
        try:
            # 驗證參數
            validated_params = self._validate_parameters(params)
            self._logger.info("參數驗證完成")
            
            # 取得有效日期
            valid_date = self._get_valid_date(end_date)
            self._logger.info(f"使用日期: {valid_date.strftime('%Y-%m-%d')}")
            
            # 應用財務指標篩選
            financial_result = self._apply_financial_filters(valid_date, validated_params)
            self._logger.info(f"財務篩選完成，剩餘 {len(financial_result)} 隻股票")
            
            # 應用技術指標篩選
            final_result = self._apply_technical_filters(financial_result, valid_date, validated_params)
            self._logger.info(f"技術篩選完成，最終剩餘 {len(final_result)} 隻股票")
            
            print(f"總挑選數量: {len(final_result)}")
            return final_result
            
        except Exception as e:
            self._logger.error(f"執行篩選時發生錯誤: {e}")
            print(f"篩選失敗: {e}")
            return pd.DataFrame()

    # 取得各種財報數字篩選
    def get_financial_statement(
        self, date: datetime, GPM: float = 0, OPR: float = 0, EPS: float = 0, RPS: float = 0
    ) -> pd.DataFrame:
        """取得財務報表篩選結果"""
        try:
            # 取得最近的財務報告日期
            report_date = Tools.get_latest_season_report_date(date, date)
            self._logger.info(f"使用財務報告日期: {report_date.strftime('%Y-%m-%d')}")
            
            # 篩選綜合損益表
            pl_report = self._reportService.PLA_RP.get_ALL_Report(report_date, base_today=report_date)
            if pl_report.empty:
                self._logger.warning("綜合損益表資料為空")
                return pd.DataFrame()
            
            # 確保數據類型正確
            pl_report = pl_report.copy()
            if "毛利率(%)" in pl_report.columns:
                pl_report["毛利率(%)"] = pd.to_numeric(pl_report["毛利率(%)"], errors='coerce')
            if "營業利益率(%)" in pl_report.columns:
                pl_report["營業利益率(%)"] = pd.to_numeric(pl_report["營業利益率(%)"], errors='coerce')
            
            gpm_filter = pl_report["毛利率(%)"] > GPM
            opr_filter = pl_report["營業利益率(%)"] > OPR
            result_pl = pl_report[gpm_filter & opr_filter]
            self._logger.info(f"綜合損益表篩選完成: {len(result_pl)} 隻股票")
            
            # 篩選資產負債表
            bs_report = self._reportService.BS_RP.get_ALL_Report(report_date, base_today=report_date)
            if bs_report.empty:
                self._logger.warning("資產負債表資料為空")
                return pd.DataFrame()
            
            # 確保數據類型正確
            bs_report = bs_report.copy()
            if "每股參考淨值" in bs_report.columns:
                bs_report["每股參考淨值"] = pd.to_numeric(bs_report["每股參考淨值"], errors='coerce')
            
            rps_filter = bs_report["每股參考淨值"] > RPS
            result_bs = bs_report[rps_filter]
            self._logger.info(f"資產負債表篩選完成: {len(result_bs)} 隻股票")
            
            # 篩選現金流量表
            cpl_report = self._reportService.CPL_RP.get_ALL_Report(report_date, base_today=report_date)
            if cpl_report.empty:
                self._logger.warning("現金流量表資料為空")
                return pd.DataFrame()
            
            # 確保數據類型正確
            cpl_report = cpl_report.copy()
            if "基本每股盈餘（元）" in cpl_report.columns:
                cpl_report["基本每股盈餘（元）"] = pd.to_numeric(cpl_report["基本每股盈餘（元）"], errors='coerce')
            
            eps_filter = cpl_report["基本每股盈餘（元）"] > EPS
            result_cpl = cpl_report[eps_filter]
            self._logger.info(f"現金流量表篩選完成: {len(result_cpl)} 隻股票")
            
            # 合併結果
            if result_pl.empty or result_bs.empty or result_cpl.empty:
                self._logger.warning("部分財務報表篩選結果為空，無法合併")
                return pd.DataFrame()
            
            # 使用改進的MixDataFrames方法
            try:
                # 檢查DataFrame的索引類型
                pl_index = result_pl.index.name if result_pl.index.name else "index"
                bs_index = result_bs.index.name if result_bs.index.name else "index"
                cpl_index = result_cpl.index.name if result_cpl.index.name else "index"
                
                # 使用最常見的索引名稱
                common_index = "code"  # 預設使用 code
                
                # 如果索引名稱不一致，嘗試使用第一個DataFrame的索引名稱
                if pl_index and bs_index and pl_index == bs_index:
                    common_index = pl_index
                elif pl_index:
                    common_index = pl_index
                
                self._logger.info(f"使用索引 '{common_index}' 進行合併")
                
                result_temp = Tools.MixDataFrames({
                    "result_pl": result_pl, 
                    "result_bs": result_bs
                }, index=common_index)
                
                final_result = Tools.MixDataFrames({
                    "result_temp": result_temp, 
                    "result_cpl": result_cpl
                }, index=common_index)
                
                self._logger.info(f"財務報表合併完成: {len(final_result)} 隻股票")
                return final_result
                
            except Exception as e:
                self._logger.error(f"合併財務報表時發生錯誤: {e}")
                # 回退到使用pandas merge
                try:
                    # 使用索引進行合併
                    temp = pd.merge(result_pl, result_bs, left_index=True, right_index=True, how="inner")
                    final_result = pd.merge(temp, result_cpl, left_index=True, right_index=True, how="inner")
                    self._logger.info("使用pandas merge成功合併財務報表")
                    return final_result
                except Exception as merge_error:
                    self._logger.error(f"使用pandas merge也失敗: {merge_error}")
                    return pd.DataFrame()
                    
        except Exception as e:
            self._logger.error(f"取得財務報表時發生錯誤: {e}")
            return pd.DataFrame()
