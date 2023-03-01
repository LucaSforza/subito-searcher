# stdlib
import pickle
import json
from typing import Union

# third party
from subitokit import subito_query,load_query

DB_FILE = "searches.tracked"
TELEGRAM_API_FILE = "telegram.credentials"

def save_queries(queries: list[subito_query]) -> None:
    queries_dict = list(map(lambda x:x.to_json(),queries))
    with open(DB_FILE,'wb') as file:
        pickle.dump(queries_dict,file)
        

def load_queries() -> list[subito_query]:
    try:
        with open(DB_FILE,'rb') as file:
            queries_str: list[str] = pickle.load(file)
    except FileNotFoundError:
        return []
    queries = list()
    for query_str in queries_str:
        queries.append(load_query(json.loads(query_str)))
    return queries

def save_api_credentials(token: str ,chat_id: str ,bot_on: bool) -> None:
    api_credential = {
        'token':token,
        'chat_id':chat_id,
        'state': bot_on
    }
    with open(TELEGRAM_API_FILE,'wb') as file:
        pickle.dump(api_credential,file)

def load_api_credential() -> dict[str,Union[str,bool]]:
    try:
        with open(TELEGRAM_API_FILE,'rb') as file:
            return pickle.load(file)
    except FileNotFoundError:
        return dict()