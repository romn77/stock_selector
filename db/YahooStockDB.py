import sys
import sqlite3
import retry
import yfinance as yf
import pandas as pd
from tqdm import tqdm
from .StockDB import StockDB

class YahooStockDB(StockDB):
    def __init__(self):
        super().__init__()

    def read_csv(self, filepath):
        df_a = pd.read_csv(filepath, dtype=str, engine="python")
        stock_codes = df_a['Symbol']
        return stock_codes
    
        # 失败重试3次
    @retry.retry(exceptions=Exception, tries=3, delay=1)
    def yf_download(self, code, start_date, end_date):
        self.df = yf.download(code, interval="1d", start=start_date, end=end_date)
        return self.df
    
    def download_stock(self, code, start_date, end_date):
        conn = sqlite3.connect('db/stock.db')
        cursor = conn.cursor()
        df = self.yf_download(code, start_date, end_date)
        data_list = []
        # 插入数据的 SQL 语句
        insert_data_sql = '''
            INSERT OR IGNORE INTO stock_daily (code, date, open, high, low, close)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        # 将 DataFrame 中的数据写入数据库
        for index, row in df.iterrows():
            data_list.append((code, row['Date'], row['Open'], row['High'], row['Low'], row['Close']))
            
        # 执行批量插入操作
        cursor.executemany(insert_data_sql, data_list)
        conn.commit()

    def get_stock_daily(self, code, start_date, end_date):
        return self.query(code, start_date, end_date)
    
    def query(self, code, start_date, end_date):
        # 执行查询语句并返回DataFrame
        query_sql = '''
            SELECT * FROM stock_daily
            WHERE code = ? AND date >= ? AND date <= ?
            ORDER BY date ASC
        '''
        # 执行查询语句
        self.cursor.execute(query_sql, (code, start_date, end_date))

        # 获取查询结果
        results = self.cursor.fetchall()
        df = pd.DataFrame(results, columns=[column[0] for column in self.cursor.description])
        self.conn.commit()
        return df
