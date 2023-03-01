# stdlib
import requests
import time
from typing import Optional
import os

# third party
from subitokit import subito_query,run_query
import typer

# first party
from src._version import __version__
from src.persistence import (
    save_queries,
    load_queries,
    save_api_credentials,
    load_api_credential
)

app = typer.Typer()

queries: list[subito_query] = list()

api_credentials = dict()
bot_on: bool

def exit(string: str = None):
    save_queries(queries)
    if string:
        raise typer.Exit(string)
    raise typer.Exit()

def version_callback(called: bool) -> None:
    if called:
        exit(f'subito-searcher version: {__version__}')

def is_telegram_active():
    return (api_credentials.get("chat_id") and api_credentials.get("token")) and api_credentials.get("state",False)

def send_telegram_messages(message):
    request_url = f"https://api.telegram.org/bot{api_credentials['token']}/sendMessage?chat_id={api_credentials['chatid']}&text={message}"
    requests.get(request_url)

URL = typer.Option(
    '' ,"--url" ,help="url for your new tracking's search query"
)
MIN_PRICE = typer.Option(
    None ,"--minPrice" ,"--min" ,help="minimum price for the query"
)
MAX_PRICE = typer.Option(
    None ,"--maxPrice" ,"--max" ,help="maximum price for the query"
)
DAEMON = typer.Option(
    False ,"--daemon" ,"-d" ,help="keep refreshing search results forever (default delay 120 seconds)"
)
DELAY = typer.Option(
    120 ,"--delay" , help="delay for the daemon option (in seconds)"
)
LONG_LIST = typer.Option(
    False ,"--long","-l" , help="print a more compact list"
)
ADD_TOKEN_ID = typer.Option(
    None ,"--token" ,"-t" ,help="telegram setup: add bot API token"
)
ADD_CHAT_ID = typer.Option(
    None ,"--chat-id" ,"-c" ,help="telegram setup: add bot chat id"
)
SET_BOT_OFF = typer.Option(
    False,'--off',help='set off the telegram bot'
)
SET_BOT_ON = typer.Option(
    False,'--on',help='set on the telegram bot'
)
VERSION = typer.Option(
    None ,"--version" ,"-v" ,help="shows installed version of subito-searcher",callback=version_callback,is_eager=True
)

@app.callback()
def common(ctx: typer.Context ,version: Optional[bool] = VERSION):
    ctx.obj = ctx.params
    ...

@app.command()
def add(
    name: str,
    url: str = URL,
    min_price: Optional[int] = MIN_PRICE,
    max_price: Optional[int] = MAX_PRICE
):
    global queries
    if not min_price:
        min_price = 'null'
    if not max_price:
        max_price = 'null'
    if name in map(lambda q:q.name,queries):
        exit(f'"{name}" already exists in the query list')
    typer.echo(f'running query "{name}" ...')
    query = run_query(name,min_price,max_price,url)
    queries.append(query)
    typer.echo(query)
    exit('done')

@app.command()
def delete(name: str):
    global queries
    for query in queries:
        if name == query.name:
            queries.remove(query)
            exit(f'deleted query "{name}"')
    typer.echo(f'not found the query "{name}"')

@app.command()
def refresh(daemon: bool = DAEMON,delay : int  = DELAY):
    global queries
    try:
        while True:
            for query in queries:
                new_prods = query.refresh()
                if is_telegram_active():
                    for prod in new_prods:
                        send_telegram_messages(
                            f"""New product discovered
                            search name:{query.name}
                            product name:{prod.title}
                            location:{prod.location}
                            price:{prod.price}
                            link:{prod.link}"""
                        )
            if daemon:
                time.sleep(delay)
            else:
                exit('done the refresh of all queries')
    except KeyboardInterrupt:
        exit('\nend of refreshing')

@app.command('list')
def list_queries(long: bool = LONG_LIST):
    for i,query in enumerate(queries,start=1):
        typer.echo(f'\n{i}) {query}' if long else f'\n{i}) search: {query.name}\nquery url:{query.url}')

@app.command('telegram')
def add_telegram_bot(
    token: Optional[str] = ADD_TOKEN_ID,
    chat_id: Optional[str] = ADD_CHAT_ID,
    set_on: bool = SET_BOT_ON,
    set_off: bool= SET_BOT_OFF

):
    if set_off and set_on:
        raise typer.Exit("You can't set on and of at the same time" )
    if set_off:
        api_credentials['state'] = False
    elif set_on:
        api_credentials['state'] = True
    if token and chat_id:
        api_credentials['token'] = token
        api_credentials['chat_id'] = chat_id
        save_api_credentials(token,chat_id,set_on)
        raise typer.Exit()
    typer.echo("you must select 'token' and 'chat_id options'")

@app.command('show-telegram-api')
def show_api_tokens():
    for key,item in api_credentials.items():
        typer.echo(f"{key}: {item}")
@app.command()
def pwd():
    typer.echo(os.getcwd())

def main():
    global queries,api_credentials
    queries = load_queries()
    api_credentials = load_api_credential()
    app()