import os
import requests
import tempfile
import re
from urllib.error import HTTPError
import unicodedata

from bs4 import BeautifulSoup
import pandas as pd


VAX_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


def read_xlsx_from_url(url: str, as_series: bool = False, **kwargs) -> pd.DataFrame:
    """Download and load xls file from URL.

    Args:
        url (str): File url.
        as_series (bol): Set to True to return a pandas.Series object. Source file must be of shape 1xN (1 row, N
                            columns). Defaults to False.
        kwargs: Arguments for pandas.read_excel.

    Returns:
        pandas.DataFrame: Data loaded.
    """
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux i686)"}
    response = requests.get(url, headers=headers)
    with tempfile.NamedTemporaryFile() as tmp:
        with open(tmp.name, 'wb') as f:
            f.write(response.content)
        df = pd.read_excel(tmp.name, **kwargs)
    if as_series:
        return df.T.squeeze()
    return df


def download_file_from_url(url, save_path, chunk_size=128):
    r = requests.get(url, stream=True)
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)


def get_headers() -> dict:
    """Get generic header for requests.

    Returns:
        dict: Header.
    """
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.16; rv:86.0) Gecko/20100101 Firefox/86.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "*",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }


def get_soup(source: str, headers: dict = None, verify: bool = True, from_encoding: str = None,
             timeout=20) -> BeautifulSoup:
    """Get soup from website.

    Args:
        source (str): Website url.
        headers (dict, optional): Headers to be used for request. Defaults to general one.
        verify (bool, optional): Verify source URL. Defaults to True.
        from_encoding (str, optional): Encoding to use. Defaults to None.
        timeout (int, optional): If no response is received after `timeout` seconds, exception is raied. 
                                 Defaults to 20.
    Returns:
        BeautifulSoup: Website soup.
    """
    if headers is None:
        headers = get_headers()
    try:
        response = requests.get(source, headers=headers, verify=verify, timeout=timeout)
    except Exception as err:
        raise err
    if not response.ok:
        raise HTTPError("Web {} not found! {response.content}")
    content = response.content
    return BeautifulSoup(
        content,
        "html.parser",
        from_encoding=from_encoding
    )


def url_request_broken(url):
    url_base, url_params = url.split('query?')
    x = filter(lambda x: x[0] != 'where', [p.split('=') for p in url_params.split('&')])
    params = dict(x)
    return f"{url_base}/query", params


def clean_count(count):
    count = re.sub(r"[^0-9]", "", count)
    count = int(count)
    return count


def clean_string(text_raw):
    """Clean column name."""
    text_new = unicodedata.normalize('NFKC', text_raw).strip()
    return text_new


def clean_column_name(colname):
    """Clean column name."""
    colname_new = clean_string(colname)
    if "Unnamed:" in colname_new:
        colname_new = ""
    return colname_new


def clean_df_columns_multiindex(df):
    columns_new = []
    for col in df.columns:
        columns_new.append([clean_column_name(c) for c in col])
    df.columns = pd.MultiIndex.from_tuples(columns_new)
    return df
