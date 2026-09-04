import aiohttp
import logging
from libprobe.asset import Asset
from libprobe.check import Check
from lib.unificonn import get_credentials, sanity_check
from urllib.parse import quote
from ..connector import get_connector


MAX_ITEMS = 2000
IGNORE_KEYS = (
    'EVT_WU_Connected',
    'EVT_WU_Disconnected',
    'EVT_WU_Roam',
    'EVT_WU_RoamRadio',
)


class CheckEvent(Check):
    key = 'event'
    unchanged_eol = 14400

    @staticmethod
    async def run(asset: Asset, local_config: dict, config: dict) -> dict:

        site_name = config.get('site', 'default')
        ssl = config.get('ssl', False)
        credentials = await get_credentials(asset, local_config, config)

        base_url = credentials['base_url']
        is_unifi_os = credentials['is_unifi_os']
        cookies = credentials['cookies']
        headers = credentials['headers']

        site_name = quote(site_name, safe="")
        prefix = '/proxy/network' if is_unifi_os else ''

        endpoints = [
            # Primary UniFi OS system log endpoint (Network 8.x / 9.x+)
            {
                'url': (
                    f"{base_url}{prefix}/v2/api/"
                    f"site/{site_name}/system-log/all"),
                'method': 'POST',
                'json': {'_limit': MAX_ITEMS}
            },
            # 2. Alternative GET system log endpoint
            {
                'url': (
                    f"{base_url}{prefix}/v2/api/"
                    f"site/{site_name}/logs?limit={MAX_ITEMS}"),
                'method': 'GET',
                'json': None
            },
            # Legacy GET fallback (for old UniFi Standard Controllers <= 7.x)
            {
                'url': f"{base_url}{prefix}/api/s/{site_name}/stat/event",
                'method': 'GET',
                'json': None
            }
        ]

        data_list = []
        async with aiohttp.ClientSession(cookies=cookies,
                                         connector=get_connector()) as session:
            for ep in endpoints:
                url = ep['url']
                method = ep['method']
                json_payload = ep['json']

                try:
                    async with session.request(method, url,
                                               json=json_payload,
                                               headers=headers,
                                               ssl=ssl) as resp:
                        logging.debug(
                            f"Event fetch attempt: {method} {url} "
                            f"-> {resp.status}")

                        if resp.status == 200:
                            content_type = resp.headers.get('Content-Type', '')
                            if 'application/json' in content_type:
                                res_json = await resp.json()

                                # v2 system log payloads wrap
                                # items in 'data' or 'logs'
                                if isinstance(res_json, dict):
                                    data_list = res_json.get('data') \
                                        or res_json.get('logs') or []
                                elif isinstance(res_json, list):
                                    data_list = res_json

                                if data_list:
                                    logging.debug(
                                        "Successfully fetched "
                                        f"{len(data_list)} events from {url}")
                                    break
                except Exception as err:
                    logging.debug(f"Failed fetching events from {url}: {err}")
                    continue
            else:
                raise Exception(
                    f"Unable to fetch events for site '{site_name}' "
                    f"from {base_url}. "
                    "None of the system log endpoints returned data."
                )

        # Truncate and map fields
        # (handling both legacy and v2 schema field names)
        data_list.sort(key=lambda i: i.get('time') or i.get('timestamp') or 0)
        data_list = data_list[-MAX_ITEMS:]

        event = [{
            'name': d.get('_id') or d.get('id', ''),
            'key': d.get('key') or d.get('event_type', 'unknown'),
            'msg': d.get('msg') or d.get('message', ''),
            'subsystem': d.get('subsystem', ''),
            'time': (
                int((d.get('time') or d.get('timestamp')) / 1000)
                if (d.get('time') or d.get('timestamp')) else None),
        } for d in data_list if d.get('key') not in IGNORE_KEYS]

        return {
            'event': event
        }
