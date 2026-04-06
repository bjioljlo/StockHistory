"""
ADL (Advance-Decline Line) Updater Module

Responsible for:
- ADL index calculation
- Trading day calendar detection
- ADL persistence to database
- Incremental ADL updates
"""
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text


class ADLUpdater:
    def __init__(self, sql_service, external_factory):
        self._sql_service = sql_service
        self._external_factory = external_factory

    def persist_adl_data(self) -> bool:
        """
        Recalculate full ADL from latest AD_index history and overwrite to MySQL.
        """
        try:
            ad_index_history = self._external_factory.Get_instance().get_full_ad_index()
            if ad_index_history.empty:
                print("No AD_index history available. Skipping ADL persistence.")
                return False

            ad_index_history = ad_index_history.sort_index()
            daily_diff = ad_index_history["up_count"] - ad_index_history["down_count"]
            adl_series = daily_diff.cumsum()
            adl_df = pd.DataFrame({"ADL": adl_series})

            save_ok = self._sql_service.save_adl_data(adl_df)
            if save_ok:
                print(f"Persisted {len(adl_df)} ADL rows to MySQL.")
            else:
                print("Failed to persist ADL data to MySQL.")
            return save_ok
        except Exception as e:
            print(f"Failed to calculate or persist ADL: {e}")
            return False

    def run_update_adl(self, callback=None) -> bool:
        """
        Run full ADL update process for new trading days
        """
        print("Update stocks other Info start!")
        latest_ad_index_date = None
        try:
            with self._sql_service.server_flask.app_context():
                latest_query = text(
                    """
                    SELECT date
                    FROM ad_index
                    ORDER BY date DESC
                    LIMIT 1
                    """
                )
                latest_df = pd.read_sql(latest_query, con=self._sql_service.MySql_server.engine)
                if not latest_df.empty:
                    latest_ad_index_date = pd.to_datetime(latest_df.iloc[0]["date"]).date()
        except Exception as e:
            print(f"Could not read latest AD_index date, fallback to one-year scan: {e}")
        
        end_date = datetime(
            datetime.today().year, datetime.today().month, datetime.today().day
        )  # Set date range

        # Get trading day calendar for last year (using 2330 as reference)
        if latest_ad_index_date:
            start_date_for_calendar = datetime.combine(latest_ad_index_date, datetime.min.time())
            print(f"Fetching trading day calendar from {start_date_for_calendar.strftime('%Y-%m-%d')}...")
        else:
            print("Fetching trading day calendar for the last year...")
            start_date_for_calendar = end_date - timedelta(days=366)
        
        trading_days_df = self._external_factory.Get_instance().get_stock_history(
            "2330", start=start_date_for_calendar
        )
        
        if trading_days_df.empty:
            print("Could not fetch trading day calendar. Aborting ADL update.")
            print("Update stocks other Info end!")
            return False

        # The index is a DatetimeIndex, which is efficient for lookups.
        trading_days = trading_days_df.index

        # Get existing ADL data to avoid duplicate calculations
        existing_dates = {latest_ad_index_date} if latest_ad_index_date else set()

        # Pre-collect dates that need to be processed
        dates_to_process = []
        days_to_scan = max((end_date.date() - latest_ad_index_date).days + 1, 1) if latest_ad_index_date else 366
        
        for i in range(days_to_scan):
            date_to_check = end_date - timedelta(days=i)
            
            # Check if it's a trading day and not already existing
            if date_to_check in trading_days and date_to_check.date() not in existing_dates:
                dates_to_process.append(date_to_check)
            elif date_to_check not in trading_days:
                print(f"Skipping non-trading day: {date_to_check.strftime('%Y-%m-%d')}")
            
            if callback:
                progress = int((i + 1) / max(days_to_scan, 1) * 100)
                callback(progress)

        if not dates_to_process:
            print("No new trading days to process. ADL update completed.")
            return self.persist_adl_data()

        print(f"Found {len(dates_to_process)} trading days to process.")

        # Batch process dates that need calculation
        for i, date_to_check in enumerate(dates_to_process):
            print(f"Updating ADL for {date_to_check.strftime('%Y-%m-%d')} ({i+1}/{len(dates_to_process)})")
            self._external_factory.Get_instance().get_stock_AD_index(date_to_check)
            
            if callback:
                progress = int((i + 1) / len(dates_to_process) * 100)
                callback(progress)

        persist_ok = self.persist_adl_data()
        if not persist_ok:
            print("ADL index update finished, but persisted ADL refresh failed.")
            return False

        print("Update stocks other Info end!")
        return True