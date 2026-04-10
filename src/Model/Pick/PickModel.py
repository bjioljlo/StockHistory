"""
Stock Pick Model - Refactored Implementation

This class contains the main business logic for stock screening functionality.
All logic migrated from legacy Model_pick.py facade.
"""
import logging
from datetime import datetime
import pandas as pd

from src.Model.Model import TModel
from src.Model.ModelValidation import ModelValidator, validate_parameters, ModelValidationError
from src.ExternalService.ExternalDataFactory import ExternalDataFactory
from src.FilterService.StockHistory import StockFilter, OriginalStockByYahoo
from src.FilterService.StockReportHistory import SeasonReportFactory
from src.Common.Parameter import RecordPickParameter
from src.Common import Tools

from .ParameterValidator import PickParameterValidator
from .StockGroupService import StockGroupService
from .DateValidatorService import DateValidatorService
from .FilterDataMerger import FilterDataMerger


class PickModel(TModel):
    """
    Main model class for stock screening functionality.
    Contains business logic migrated from legacy Model_pick.py.
    """
    def __init__(self, external_data_factory: ExternalDataFactory):
        super().__init__()
        self._external_data_factory = external_data_factory
        self._Groups = None
        self._reportService = ReportServices(self._external_data_factory)
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

    def _apply_financial_filters(self, date: datetime, params: dict) -> pd.DataFrame:
        """Apply financial indicator filters"""
        # Get financial statement data
        financial_data = self.get_financial_statement(
            date, 
            params['GPM'], params['OPR'], params['EPS'], params['RPS']
        )
        
        if financial_data.empty:
            self._logger.warning("Financial statement filter result is empty")
            return financial_data

        # Initialize main filter
        mainfun = StockFilter(date, self._reportService.Month_index)

        # Apply financial filters - only apply when parameter > 0
        filters_to_apply = []
        
        # PBR filter
        if params['PBR_high'] > 0 or params['PBR_low'] > 0:
            filters_to_apply.append(
                ('PBR', lambda: self._apply_report_filter(mainfun, self._reportService.PBR_index, params['PBR_high'], params['PBR_low']))
            )
        
        # PER filter
        if params['PER_high'] > 0 or params['PER_low'] > 0:
            filters_to_apply.append(
                ('PER', lambda: self._apply_report_filter(mainfun, self._reportService.PER_index, params['PER_high'], params['PER_low']))
            )
        
        # ROE filter
        if params['ROE_high'] > 0 or params['ROE_low'] > 0:
            filters_to_apply.append(
                ('ROE', lambda: self._apply_report_filter(mainfun, self._reportService.ROE_index, params['ROE_high'], params['ROE_low']))
            )
        
        # ROE growth filter
        if params['ROE_up'] > 0:
            filters_to_apply.append(('ROE Growth', lambda: mainfun.get_Up_Auto(params['ROE_up'])))
        
        # Dividend yield filter
        if params['yiled_high'] > 0 or params['yiled_low'] > 0:
            filters_to_apply.append(
                ('Dividend Yield', lambda: self._apply_report_filter(mainfun, self._reportService.Yield_index, params['yiled_high'], params['yiled_low']))
            )
        
        # Revenue growth filter
        if params['OMGR'] > 0:
            filters_to_apply.append(('Revenue Growth', lambda: mainfun.get_Up_Auto(params['OMGR'])))
        
        # PEG filter
        if params['PEG_high'] > 0 or params['PEG_low'] > 0:
            filters_to_apply.append(
                ('PEG', lambda: self._apply_report_filter(mainfun, self._reportService.PEG_index, params['PEG_high'], params['PEG_low']))
            )
        
        # Free Cash Flow filter
        if params['FCF'] > 0:
            filters_to_apply.append(('Free Cash Flow', lambda: mainfun.get_Up_Auto(params['FCF'])))
        
        # EPS growth filter
        if params['EPS_up'] > 0:
            filters_to_apply.append(('EPS Growth', lambda: mainfun.get_Up_Auto(params['EPS_up'])))
        
        # Annual Revenue growth filter
        if params['SRGR'] > 0:
            filters_to_apply.append(('Annual Revenue Growth', lambda: mainfun.get_Up_Auto(params['SRGR'])))
        
        # Monthly Revenue growth filter
        if params['MRGR'] > 0:
            filters_to_apply.append(('Monthly Revenue Growth', lambda: mainfun.get_Up_Auto(params['MRGR'])))
        
        # Monthly report smooth filter - only apply when both parameters are non-zero
        if params['monthRP_smoothAVG'] > 0 and params['monthRP_UpMpnth'] > 0:
            filters_to_apply.insert(0, ('Monthly Report Smooth', lambda: mainfun.get_Smooth_Up_Auto(params['monthRP_smoothAVG'], params['monthRP_UpMpnth'])))

        self._logger.info(f"Preparing to apply {len(filters_to_apply)} financial filter conditions")
        
        result_data = financial_data
        for filter_name, filter_func in filters_to_apply:
            try:
                filter_result = filter_func()
                if not filter_result.empty:
                    result_data = self._merge_filter_data(result_data, filter_result, filter_name)
                else:
                    self._logger.warning(f"{filter_name} filter result is empty, stopping filter")
                    return pd.DataFrame()
            except Exception as e:
                self._logger.error(f"Error applying {filter_name} filter: {e}")

        return result_data

    def _apply_technical_filters(self, base_data: pd.DataFrame, date: datetime, params: dict) -> pd.DataFrame:
        """Apply technical indicator filters"""
        if base_data.empty:
            self._logger.warning("Base data for technical filter is empty")
            return base_data

        mainStockfun = StockFilter(date, base_data, OriginalStockByYahoo(self._external_data_factory))
        result_data = base_data
        filters_applied = 0

        # Price filter
        if params['price_high'] > 0 or params['price_low'] > 0:
            try:
                price_data = mainStockfun.get_Filter(
                    "price", params['price_high'], params['price_low'], info.Price_type.Close
                )
                if not price_data.empty:
                    result_data = self._merge_filter_data(result_data, price_data, "Price")
                    filters_applied += 1
                else:
                    self._logger.warning("Price filter result is empty")
                    return pd.DataFrame()
            except Exception as e:
                self._logger.error(f"Price filter failed: {e}")

        # Historical high filter
        if params['flash_Day'] > 0 or params['record_Day'] > 0:
            try:
                record_data = mainStockfun.get_Filter_RecordHigh(
                    params['flash_Day'], params['record_Day'], info.Price_type.High
                )
                if not record_data.empty:
                    result_data = self._merge_filter_data(result_data, record_data, "Historical High")
                    filters_applied += 1
                else:
                    self._logger.warning("Historical high filter result is empty")
                    return pd.DataFrame()
            except Exception as e:
                self._logger.error(f"Historical high filter failed: {e}")

        # Moving Average filter
        if params['BerMA'] > 0:
            try:
                berma_data = mainStockfun.get_Filter_BetterMA(params['BerMA'], info.Price_type.Close)
                if not berma_data.empty:
                    result_data = self._merge_filter_data(result_data, berma_data, "Moving Average")
                    filters_applied += 1
                else:
                    self._logger.warning("Moving average filter result is empty")
                    return pd.DataFrame()
            except Exception as e:
                self._logger.error(f"Moving average filter failed: {e}")

        # Volume multiple filter
        if params['avg_vol_multiple'] > 0:
            try:
                avg_vol_data = mainStockfun.get_Filter_AvgVol_Multiple(params['avg_vol_multiple'], 10)
                if not avg_vol_data.empty:
                    result_data = self._merge_filter_data(result_data, avg_vol_data, "Volume Multiple")
                    filters_applied += 1
                else:
                    self._logger.warning("Volume multiple filter result is empty")
                    return pd.DataFrame()
            except Exception as e:
                self._logger.error(f"Volume multiple filter failed: {e}")

        # Volume SMA filter
        if params['volum'] > 0:
            try:
                volume_data = mainStockfun.get_Filter_SMA(
                    "volume", params['volum'] * 100000000, params['volum'] * 10000, 5, info.Price_type.Volume
                )
                if not volume_data.empty:
                    result_data = self._merge_filter_data(result_data, volume_data, "Volume SMA")
                    filters_applied += 1
                else:
                    self._logger.warning("Volume SMA filter result is empty")
                    return pd.DataFrame()
            except Exception as e:
                self._logger.error(f"Volume SMA filter failed: {e}")

        # Industry classification filter
        if params['Kind'] > 0 and params['Kind'] <= len(self.Groups):
            try:
                group_data = mainStockfun.get_FilterInfo(self.Groups[params['Kind'] - 1])
                if not group_data.empty:
                    result_data = self._merge_filter_data(result_data, group_data, f"Industry({self.Groups[params['Kind'] - 1]})")
                    filters_applied += 1
                else:
                    self._logger.warning(f"Industry({self.Groups[params['Kind'] - 1]}) filter result is empty")
                    return pd.DataFrame()
            except Exception as e:
                self._logger.error(f"Industry classification filter failed: {e}")

        self._logger.info(f"Applied {filters_applied} technical filter conditions")
        return result_data

    def _apply_report_filter(self, mainfun, report_index, high_value: float, low_value: float) -> pd.DataFrame:
        """Helper method to apply report indicator filter"""
        mainfun.report = report_index
        return mainfun.get_Filter_Auto(high_value, low_value)

    def RunFilte(self, params: RecordPickParameter, end_date: datetime) -> pd.DataFrame:
        """Execute complete stock screening process"""
        try:
            # Validate parameters
            validated_params = self._validate_parameters(params)
            self._logger.info("Parameter validation completed")
            
            # Get valid date
            valid_date = self._get_valid_date(end_date)
            self._logger.info(f"Using date: {valid_date.strftime('%Y-%m-%d')}")
            
            # Apply financial filters
            financial_result = self._apply_financial_filters(valid_date, validated_params)
            self._logger.info(f"Financial filter completed, {len(financial_result)} stocks remaining")
            
            # Apply technical filters
            final_result = self._apply_technical_filters(financial_result, valid_date, validated_params)
            self._logger.info(f"Technical filter completed, {len(final_result)} stocks remaining")
            
            print(f"Total selected: {len(final_result)}")
            return final_result
            
        except Exception as e:
            self._logger.error(f"Error executing filter: {e}")
            print(f"Filter failed: {e}")
            return pd.DataFrame()

    def get_financial_statement(
        self, date: datetime, GPM: float = 0, OPR: float = 0, EPS: float = 0, RPS: float = 0
    ) -> pd.DataFrame:
        """Get financial statement filter results"""
        try:
            # Get latest financial report date
            report_date = Tools.get_latest_season_report_date(date, date)
            self._logger.info(f"Using financial report date: {report_date.strftime('%Y-%m-%d')}")
            
            # Filter Profit & Loss statement
            pl_report = self._reportService.PLA_RP.get_ALL_Report(report_date, base_today=report_date)
            if pl_report.empty:
                self._logger.warning("Profit & Loss statement data is empty")
                return pd.DataFrame()
            
            # Ensure correct data types
            pl_report = pl_report.copy()
            
            # Gross Profit Margin (%)
            gpm_columns = ["毛利率(%)", "毛利率", "gross_margin", "GPM"]
            gpm_col = next((col for col in gpm_columns if col in pl_report.columns), None)
            if gpm_col:
                pl_report[gpm_col] = pd.to_numeric(pl_report[gpm_col], errors='coerce')
                gpm_filter = pl_report[gpm_col] > GPM
            else:
                self._logger.warning("GPM column not found, skipping GPM filter")
                gpm_filter = pd.Series([True] * len(pl_report), index=pl_report.index)
            
            # Operating Profit Margin (%)
            opr_columns = ["營業利益率(%)", "營業利益率", "operating_margin", "OPM"]
            opr_col = next((col for col in opr_columns if col in pl_report.columns), None)
            if opr_col:
                pl_report[opr_col] = pd.to_numeric(pl_report[opr_col], errors='coerce')
                opr_filter = pl_report[opr_col] > OPR
            else:
                self._logger.warning("OPM column not found, skipping OPR filter")
                opr_filter = pd.Series([True] * len(pl_report), index=pl_report.index)
            
            result_pl = pl_report[gpm_filter & opr_filter]
            self._logger.info(f"Profit & Loss statement filter completed: {len(result_pl)} stocks")
            
            # Filter Balance Sheet
            bs_report = self._reportService.BS_RP.get_ALL_Report(report_date, base_today=report_date)
            if bs_report.empty:
                self._logger.warning("Balance Sheet data is empty")
                return pd.DataFrame()
            
            # Ensure correct data types
            bs_report = bs_report.copy()
            
            # Book Value Per Share
            rps_columns = ["每股參考淨值", "每股淨值", "book_value_per_share", "BVPS"]
            rps_col = next((col for col in rps_columns if col in bs_report.columns), None)
            if rps_col:
                bs_report[rps_col] = pd.to_numeric(bs_report[rps_col], errors='coerce')
                rps_filter = bs_report[rps_col] > RPS
            else:
                self._logger.warning("BVPS column not found, skipping RPS filter")
                rps_filter = pd.Series([True] * len(bs_report), index=bs_report.index)
            
            result_bs = bs_report[rps_filter]
            self._logger.info(f"Balance Sheet filter completed: {len(result_bs)} stocks")
            
            # Filter Cash Flow statement
            cpl_report = self._reportService.CPL_RP.get_ALL_Report(report_date, base_today=report_date)
            if cpl_report.empty:
                self._logger.warning("Cash Flow statement data is empty")
                return pd.DataFrame()
            
            # Ensure correct data types
            cpl_report = cpl_report.copy()
            
            # Earnings Per Share
            eps_columns = ["基本每股盈餘（元）", "基本每股盈餘", "EPS", "每股盈餘", "consolidated_eps"]
            eps_col = next((col for col in eps_columns if col in cpl_report.columns), None)
            if eps_col:
                cpl_report[eps_col] = pd.to_numeric(cpl_report[eps_col], errors='coerce')
                eps_filter = cpl_report[eps_col] > EPS
            else:
                self._logger.warning("EPS column not found, skipping EPS filter")
                eps_filter = pd.Series([True] * len(cpl_report), index=cpl_report.index)
            
            result_cpl = cpl_report[eps_filter]
            self._logger.info(f"Cash Flow statement filter completed: {len(result_cpl)} stocks")
            
            # Merge results
            if result_pl.empty or result_bs.empty or result_cpl.empty:
                self._logger.warning("Some financial statement filter results are empty, cannot merge")
                return pd.DataFrame()
            
            # Use improved MixDataFrames method
            try:
                pl_index = result_pl.index.name if result_pl.index.name else "index"
                bs_index = result_bs.index.name if result_bs.index.name else "index"
                cpl_index = result_cpl.index.name if result_cpl.index.name else "index"
                
                # Use most common index name
                common_index = "code"  # Default using code
                
                # If index names are consistent, use first DataFrame's index name
                if pl_index and bs_index and pl_index == bs_index:
                    common_index = pl_index
                elif pl_index:
                    common_index = pl_index
                
                self._logger.info(f"Using index '{common_index}' for merging")
                
                result_temp = Tools.MixDataFrames({
                    "result_pl": result_pl, 
                    "result_bs": result_bs
                }, index=common_index)
                
                final_result = Tools.MixDataFrames({
                    "result_temp": result_temp, 
                    "result_cpl": result_cpl
                }, index=common_index)
                
                self._logger.info(f"Financial statements merged successfully: {len(final_result)} stocks")
                return final_result
                
            except Exception as e:
                self._logger.error(f"Error merging financial statements: {e}")
                # Fallback to pandas merge
                try:
                    # Merge using index
                    temp = pd.merge(result_pl, result_bs, left_index=True, right_index=True, how="inner")
                    final_result = pd.merge(temp, result_cpl, left_index=True, right_index=True, how="inner")
                    self._logger.info("Successfully merged financial statements using pandas merge")
                    return final_result
                except Exception as merge_error:
                    self._logger.error(f"pandas merge also failed: {merge_error}")
                    return pd.DataFrame()
                    
        except Exception as e:
            self._logger.error(f"Error getting financial statements: {e}")
            return pd.DataFrame()
