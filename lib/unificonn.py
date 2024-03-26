import aiohttp
import logging
import os
from typing import Tuple
from libprobe.asset import Asset
from libprobe.exceptions import CheckException
from lib.connection_cache import ConnectionCache


async def login(asset: Asset, is_unify_os: bool, address: str, port: int,
                ssl: bool, username: str, password: str) -> dict:
    logging.debug(f'login on asset {asset}')

    auth_data = {
        'username': username,
        'password': password,
    }
    try:
        uri = '/api/auth/login' if is_unify_os else '/api/login'
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'https://{address}:{port}{uri}',
                json=auth_data,
                ssl=ssl,
            ) as resp:
                resp.raise_for_status()
                return {
                    'base_url': f'https://{address}:{port}',
                    'cookies': resp.cookies,
                }
    except Exception as e:
        msg = str(e) or type(e).__name__
        raise CheckException(f'login failed: {msg}')


async def detect_if_unify_os(asset: Asset, address: str, port: int,
                             ssl: bool) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(
                    f'https://{address}:{port}',
                    ssl=ssl) as resp:
                if resp.status == 200:
                    logging.debug(f'UniFi OS controller; {asset}')
                    return True
                if resp.status == 302:
                    logging.debug(f'UniFi Standard controller; {asset}')
                    return False
    except Exception:
        pass
    logging.warning(
        f'Unable to determine controller type; '
        f'Using Standard controller; {asset}')
    return False


async def get_session(asset: Asset, asset_config: dict,
                      check_config: dict) -> Tuple[dict, bool]:

    address = check_config.get('address')
    if not address:
        address = asset.name
    port = check_config.get('port', 443)
    ssl = check_config.get('ssl', False)
    username = asset_config.get('username')
    password = asset_config.get('password')
    if None in (username, password):
        raise CheckException('missing credentials')

    # we use everything what identifies a connection for an asset as key
    # of the cached 'connection'
    connection_args = (address, port, ssl, username, password)
    prev = ConnectionCache.get_value(connection_args)
    if prev:
        return prev

    is_unify_os = await detect_if_unify_os(asset, address, port, ssl)

    try:
        session = await login(asset, is_unify_os, *connection_args)
    except ConnectionError:
        raise CheckException('unable to connect')
    except Exception:
        raise
    else:
        # when connection is older than 3600 we request new 'connection'
        max_age = 3600
        ConnectionCache.set_value(
            connection_args,
            (session, is_unify_os),
            max_age)
    return session, is_unify_os
