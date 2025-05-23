import aiohttp
from libprobe.asset import Asset
from lib.unificonn import get_session
from urllib.parse import quote
from ..connector import get_connector


MAX_ITEMS = 2000
IGNORE_KEYS = (
    'EVT_WU_Connected',
    'EVT_WU_Disconnected',
    'EVT_WU_Roam',
    'EVT_WU_RoamRadio',
)


async def check_event(
    asset: Asset,
    asset_config: dict,
    check_config: dict
) -> dict:
    site_name = check_config.get('site', 'default')
    ssl = check_config.get('ssl', False)
    session, is_unifi_os = await get_session(asset, asset_config, check_config)
    uri = '/proxy/network/api/s/' if is_unifi_os else '/api/s/'
    url = f'{uri}{quote(site_name, safe="")}/stat/event'
    async with aiohttp.ClientSession(
            connector=get_connector(),
            **session) as session:
        async with session.get(url, ssl=ssl) as resp:
            resp.raise_for_status()
            data = await resp.json()

    # Each event is translated to an item. InfraSonar does not support more
    # than 2000 items per type, therefore we need to truncate the result
    # and only return the newest events. This only happens on relatively
    # large sites with many events.
    data = list(data['data'])
    data.sort(key=lambda i: i.get('time') or 0)
    data = data[-MAX_ITEMS:]

    event = [{
        'name': d['_id'],
        'key': d['key'],
        'msg': d.get('msg'),
        'subsystem': d.get('subsystem'),
        'time': int(d['time'] / 1000) if d.get('time') else None,
    } for d in data if d['key'] not in IGNORE_KEYS]
    return {
        'event': event
    }
