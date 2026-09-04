import aiohttp
from libprobe.asset import Asset
from libprobe.check import Check
from lib.unificonn import get_credentials, sanity_check
from urllib.parse import quote
from ..connector import get_connector


class CheckHealth(Check):
    key = 'health'
    unchanged_eol = 0

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
        url = f"{base_url}{prefix}/api/s/{site_name}/stat/health"

        async with aiohttp.ClientSession(cookies=cookies,
                                         connector=get_connector()) as session:
            async with session.get(url, headers=headers, ssl=ssl) as resp:
                await sanity_check(resp, url)
                data = await resp.json()

        health = [{
            'name': d['subsystem'],
            'num_user': d.get('num_user'),
            'num_guest': d.get('num_guest'),
            'num_iot': d.get('num_iot'),
            'tx_bytes_r': d.get('tx_bytes-r'),
            'rx_bytes_r': d.get('rx_bytes-r'),
            'status': d.get('status'),
            'num_ap': d.get('num_ap'),
            'num_adopted': d.get('num_adopted'),
            'num_disabled': d.get('num_disabled'),
            'num_disconnected': d.get('num_disconnected'),
            'num_pending': d.get('num_pending'),
        } for d in data['data']]

        return {
            'health': health
        }
