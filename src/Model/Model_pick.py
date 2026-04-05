"""
Stock Pick Model - Facade Class (Backward Compatible)

This class maintains backward compatibility while delegating functionality
to the new refactored components in Model/Pick/ directory.
"""
import logging
import pandas as pd
from src.Model.Model import TModel
from src.Model.ModelValidation import ModelValidator, validate_parameters, ModelValidationError
from src.ExternalService.ExternalDataFactory import ExternalDataFactory
from src.FilterService import GetStockData
from src.Model.Pick import (
    PickParameterValidator,
    StockGroupService,
    DateValidatorService,
    FilterDataMerger
)


class Model_pick(TModel):
    """
    Facade class for backward compatibility.
    All actual implementation is delegated to specialized components.
    """
    def __init__(self, external_data_factory: ExternalDataFactory):
        super().__init__()
        self._external_data_factory = external_data_factory
        self._Groups = None
        self._reportService = GetStockData.ReportServices(self._external_data_factory)
        self._logger = logging.getLogger(__name__)
        
        # Initialize refactored services
        self._date_validator = DateValidatorService(external_data_factory)

    @property
    def Groups(self) -> list[str]:
        if self._Groups is None:
            self._Groups = StockGroupService.get_all_groups()
        return self._Groups

    def _validate_parameters(self, params):
        """Delegate to PickParameterValidator"""
        return PickParameterValidator.validate(params)

    def _get_valid_date(self, end_date):
        """Delegate to DateValidatorService"""
        return self._date_validator.get_valid_trading_date(end_date)

    def _merge_filter_data(self, base_data: pd.DataFrame, filter_data: pd.DataFrame, 
                          filter_name: str) -> pd.DataFrame:
        """Delegate to FilterDataMerger"""
        return FilterDataMerger.merge_filter_data(base_data, filter_data, filter_name)
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
            
            # 使用動態後綴避免衝突
            suffixes = (f'_{filter_name.replace(" ", "_")}_base', f'_{filter_name.replace(" ", "_")}_filter')
            
            merged_data = pd.merge(
                base_data, filter_data, 
                left_index=True, right_index=True, how="inner",
                suffixes=suffixes
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

        # 應用各項財務指標篩選 - 只有當參數大於0時才應用篩選
        filters_to_apply = []
        
        # PBR 篩選：只有當 high 或 low 大於 0 時才應用
        if params['PBR_high'] > 0 or params['PBR_low'] > 0:
            filters_to_apply.append(
                ('PBR', lambda: self._apply_report_filter(mainfun, self._reportService.PBR_index, params['PBR_high'], params['PBR_low']))
            )
        
        # PER 篩選
        if params['PER_high'] > 0 or params['PER_low'] > 0:
            filters_to_apply.append(
                ('PER', lambda: self._apply_report_filter(mainfun, self._reportService.PER_index, params['PER_high'], params['PER_low']))
            )
        
        # ROE 篩選
        if params['ROE_high'] > 0 or params['ROE_low'] > 0:
            filters_to_apply.append(
                ('ROE', lambda: self._apply_report_filter(mainfun, self._reportService.ROE_index, params['ROE_high'], params['ROE_low']))
            )
        
        # ROE成長 篩選
        if params['ROE_up'] > 0:
            filters_to_apply.append(('ROE成長', lambda: mainfun.get_Up_Auto(params['ROE_up'])))
        
        # 殖利率 篩選
        if params['yiled_high'] > 0 or params['yiled_low'] > 0:
            filters_to_apply.append(
                ('殖利率', lambda: self._apply_report_filter(mainfun, self._reportService.Yield_index, params['yiled_high'], params['yiled_low']))
            )
        
        # 營收成長 篩選
        if params['OMGR'] > 0:
            filters_to_apply.append(('營收成長', lambda: mainfun.get_Up_Auto(params['OMGR'])))
        
        # PEG 篩選
        if params['PEG_high'] > 0 or params['PEG_low'] > 0:
            filters_to_apply.append(
                ('PEG', lambda: self._apply_report_filter(mainfun, self._reportService.PEG_index, params['PEG_high'], params['PEG_low']))
            )
        
        # 自由現金流 篩選
        if params['FCF'] > 0:
            filters_to_apply.append(('自由現金流', lambda: mainfun.get_Up_Auto(params['FCF'])))
        
        # EPS成長 篩選
        if params['EPS_up'] > 0:
            filters_to_apply.append(('EPS成長', lambda: mainfun.get_Up_Auto(params['EPS_up'])))
        
        # 營收年增 篩選
        if params['SRGR'] > 0:
            filters_to_apply.append(('營收年增', lambda: mainfun.get_Up_Auto(params['SRGR'])))
        
        # 營收月增 篩選
        if params['MRGR'] > 0:
            filters_to_apply.append(('營收月增', lambda: mainfun.get_Up_Auto(params['MRGR'])))
        
        # 月報表平滑篩選：只有當兩個參數都不為0時才應用
        if params['monthRP_smoothAVG'] > 0 and params['monthRP_UpMpnth'] > 0:
            filters_to_apply.insert(0, ('月報表平滑', lambda: mainfun.get_Smooth_Up_Auto(params['monthRP_smoothAVG'], params['monthRP_UpMpnth'])))

        self._logger.info(f"準備應用 {len(filters_to_apply)} 個財務篩選條件")
        
        result_data = financial_data
        for filter_name, filter_func in filters_to_apply:
            try:
                filter_result = filter_func()
                if not filter_result.empty:
                    result_data = self._merge_filter_data(result_data, filter_result, filter_name)
                else:
                    self._logger.warning(f"{filter_name} 篩選結果為空，停止篩選")
                    return pd.DataFrame()  # 如果任何篩選結果為空，直接返回空
            except Exception as e:
                self._logger.error(f"應用 {filter_name} 篩選時發生錯誤: {e}")

        return result_data

    def _apply_technical_filters(self, base_data: pd.DataFrame, date: datetime, params: dict) -> pd.DataFrame:
        """應用技術指標篩選"""
        if base_data.empty:
            self._logger.warning("技術篩選的基礎數據為空")
            return base_data

        mainStockfun = All_Stock_Filters_fuc(date, base_data, OriginalStockByYahoo(self._external_data_factory))
        result_data = base_data
        filters_applied = 0

        # 價格篩選
        if params['price_high'] > 0 or params['price_low'] > 0:
            try:
                price_data = mainStockfun.get_Filter(
                    "price", params['price_high'], params['price_low'], info.Price_type.Close
                )
                if not price_data.empty:
                    result_data = self._merge_filter_data(result_data, price_data, "價格")
                    filters_applied += 1
                else:
                    self._logger.warning("價格篩選結果為空")
                    return pd.DataFrame()
            except Exception as e:
                self._logger.error(f"價格篩選失敗: {e}")

        # 歷史高點篩選
        if params['flash_Day'] > 0 or params['record_Day'] > 0:
            try:
                record_data = mainStockfun.get_Filter_RecordHigh(
                    params['flash_Day'], params['record_Day'], info.Price_type.High
                )
                if not record_data.empty:
                    result_data = self._merge_filter_data(result_data, record_data, "歷史高點")
                    filters_applied += 1
                else:
                    self._logger.warning("歷史高點篩選結果為空")
                    return pd.DataFrame()
            except Exception as e:
                self._logger.error(f"歷史高點篩選失敗: {e}")

        # 移動平均線篩選
        if params['BerMA'] > 0:
            try:
                berma_data = mainStockfun.get_Filter_BetterMA(params['BerMA'], info.Price_type.Close)
                if not berma_data.empty:
                    result_data = self._merge_filter_data(result_data, berma_data, "移動平均線")
                    filters_applied += 1
                else:
                    self._logger.warning("移動平均線篩選結果為空")
                    return pd.DataFrame()
            except Exception as e:
                self._logger.error(f"移動平均線篩選失敗: {e}")

        # 成交量倍數篩選
        if params['avg_vol_multiple'] > 0:
            try:
                avg_vol_data = mainStockfun.get_Filter_AvgVol_Multiple(params['avg_vol_multiple'], 10)
                if not avg_vol_data.empty:
                    result_data = self._merge_filter_data(result_data, avg_vol_data, "成交量倍數")
                    filters_applied += 1
                else:
                    self._logger.warning("成交量倍數篩選結果為空")
                    return pd.DataFrame()
            except Exception as e:
                self._logger.error(f"成交量倍數篩選失敗: {e}")

        # 成交量SMA篩選
        if params['volum'] > 0:
            try:
                volume_data = mainStockfun.get_Filter_SMA(
                    "volume", params['volum'] * 100000000, params['volum'] * 10000, 5, info.Price_type.Volume
                )
                if not volume_data.empty:
                    result_data = self._merge_filter_data(result_data, volume_data, "成交量SMA")
                    filters_applied += 1
                else:
                    self._logger.warning("成交量SMA篩選結果為空")
                    return pd.DataFrame()
            except Exception as e:
                self._logger.error(f"成交量SMA篩選失敗: {e}")

        # 產業分類篩選
        if params['Kind'] > 0 and params['Kind'] <= len(self.Groups):
            try:
                group_data = mainStockfun.get_FilterInfo(self.Groups[params['Kind'] - 1])
                if not group_data.empty:
                    result_data = self._merge_filter_data(result_data, group_data, f"產業分類({self.Groups[params['Kind'] - 1]})")
                    filters_applied += 1
                else:
                    self._logger.warning(f"產業分類({self.Groups[params['Kind'] - 1]})篩選結果為空")
                    return pd.DataFrame()
            except Exception as e:
                self._logger.error(f"產業分類篩選失敗: {e}")

        self._logger.info(f"技術篩選應用了 {filters_applied} 個篩選條件")
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
            
            # 確保數據類型正確 - 改進：使用更靈活的欄位名稱檢查
            pl_report = pl_report.copy()
            
            # 毛利率(%) - 嘗試多種可能的欄位名稱
            gpm_columns = ["毛利率(%)", "毛利率", "gross_margin", "GPM"]
            gpm_col = next((col for col in gpm_columns if col in pl_report.columns), None)
            if gpm_col:
                pl_report[gpm_col] = pd.to_numeric(pl_report[gpm_col], errors='coerce')
                gpm_filter = pl_report[gpm_col] > GPM
            else:
                self._logger.warning("未找到毛利率相關欄位，跳過GPM篩選")
                gpm_filter = pd.Series([True] * len(pl_report), index=pl_report.index)
            
            # 營業利益率(%) - 嘗試多種可能的欄位名稱
            opr_columns = ["營業利益率(%)", "營業利益率", "operating_margin", "OPM"]
            opr_col = next((col for col in opr_columns if col in pl_report.columns), None)
            if opr_col:
                pl_report[opr_col] = pd.to_numeric(pl_report[opr_col], errors='coerce')
                opr_filter = pl_report[opr_col] > OPR
            else:
                self._logger.warning("未找到營業利益率相關欄位，跳過OPR篩選")
                opr_filter = pd.Series([True] * len(pl_report), index=pl_report.index)
            
            result_pl = pl_report[gpm_filter & opr_filter]
            self._logger.info(f"綜合損益表篩選完成: {len(result_pl)} 隻股票")
            
            # 篩選資產負債表
            bs_report = self._reportService.BS_RP.get_ALL_Report(report_date, base_today=report_date)
            if bs_report.empty:
                self._logger.warning("資產負債表資料為空")
                return pd.DataFrame()
            
            # 確保數據類型正確
            bs_report = bs_report.copy()
            
            # 每股參考淨值 - 嘗試多種可能的欄位名稱
            rps_columns = ["每股參考淨值", "每股淨值", "book_value_per_share", "BVPS"]
            rps_col = next((col for col in rps_columns if col in bs_report.columns), None)
            if rps_col:
                bs_report[rps_col] = pd.to_numeric(bs_report[rps_col], errors='coerce')
                rps_filter = bs_report[rps_col] > RPS
            else:
                self._logger.warning("未找到每股參考淨值相關欄位，跳過RPS篩選")
                rps_filter = pd.Series([True] * len(bs_report), index=bs_report.index)
            
            result_bs = bs_report[rps_filter]
            self._logger.info(f"資產負債表篩選完成: {len(result_bs)} 隻股票")
            
            # 篩選現金流量表
            cpl_report = self._reportService.CPL_RP.get_ALL_Report(report_date, base_today=report_date)
            if cpl_report.empty:
                self._logger.warning("現金流量表資料為空")
                return pd.DataFrame()
            
            # 確保數據類型正確
            cpl_report = cpl_report.copy()
            
            # 基本每股盈餘（元）- 嘗試多種可能的欄位名稱
            eps_columns = ["基本每股盈餘（元）", "基本每股盈餘", "EPS", "每股盈餘", "consolidated_eps"]
            eps_col = next((col for col in eps_columns if col in cpl_report.columns), None)
            if eps_col:
                cpl_report[eps_col] = pd.to_numeric(cpl_report[eps_col], errors='coerce')
                eps_filter = cpl_report[eps_col] > EPS
            else:
                self._logger.warning("未找到基本每股盈餘相關欄位，跳過EPS篩選")
                eps_filter = pd.Series([True] * len(cpl_report), index=cpl_report.index)
            
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
