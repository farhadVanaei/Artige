import codecs
import datetime
import json
import logging
import os.path

# import argparse
try:
    raise ImportError()
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)
except ImportError:
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), '../instagram_private_api'))
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


def onlogin_callback(api, new_settings_file):
    cache_settings = api.settings
    with open(new_settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
        print('SAVED: {0!s}'.format(new_settings_file))


def login(args):
    logging.basicConfig()
    _logger = logging.getLogger('instagram_private_api')
    if args.debug:
        _logger.setLevel(logging.DEBUG)
    else:
        _logger.setLevel(logging.WARNING)
    # s_handler = logging.StreamHandler()
    # _logger.addHandler(s_handler)
    if args.log_file_path:
        _logger.addHandler(logging.FileHandler(args.log_file_path))

    # Example command:
    # python examples/savesettings_logincallback.py -u "yyy" -p "zzz" -settings "test_credentials.json"
    # parser = argparse.ArgumentParser(description='login callback and save settings demo')
    # parser.add_argument('-settings', '--settings', dest='settings_file_path', type=str, required=True)
    # parser.add_argument('-u', '--username', dest='username', type=str, required=True)
    # parser.add_argument('-p', '--password', dest='password', type=str, required=True)
    # parser.add_argument('-debug', '--debug', action='store_true')

    print('Client version: {0!s}'.format(client_version))

    device_id = None
    try:

        settings_file = args.settings_file_path
        if not os.path.isfile(settings_file):
            # settings file does not exist
            print('Unable to find file: {0!s}'.format(settings_file))

            # login new
            api = Client(
                args.username, args.password,
                on_login=lambda x: onlogin_callback(x, args.settings_file_path))
        else:
            with open(settings_file) as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            print('Reusing settings: {0!s}'.format(settings_file))

            device_id = cached_settings.get('device_id')
            # reuse auth settings
            api = Client(
                args.username, args.password,
                settings=cached_settings)

    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))

        # Login expired
        # Do relogin but use default ua, keys and such
        api = Client(
            args.username, args.password,
            device_id=device_id,
            on_login=lambda x: onlogin_callback(x, args.settings_file_path))

    except ClientLoginError as e:
        print('ClientLoginError {0!s}'.format(e))
        exit(9)
    except ClientError as e:
        print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
        exit(9)
    except Exception as e:
        print('Unexpected Exception: {0!s}'.format(e))
        exit(99)

    # Show when login expires
    cookie_expiry = api.cookie_jar.auth_expires
    print('Cookie Expiry: {0!s}'.format(datetime.datetime.fromtimestamp(cookie_expiry).strftime('%Y-%m-%dT%H:%M:%SZ')))

    return api


if __name__ == '__main__':
    from private import Config as args
    api = login(args)

    # Call the api:
    rank_token = api.generate_uuid()
    results = api.tag_search('cats', rank_token)
    assert len(results.get('results', [])) > 0
    import ipdb; ipdb.trace()
    print('All ok\n results:\t', results)

    # ---------- Pagination with max_id ----------
    user_id = '2958144170'
    followers = []
    results = api.user_followers(user_id, rank_token)
    followers.extend(results.get('users', []))

    next_max_id = results.get('next_max_id')
    while next_max_id:
        results = api.user_followers(user_id, rank_token, max_id=next_max_id)
        followers.extend(results.get('users', []))
        if len(followers) >= 600:  # get only first 600 or so
            break
        next_max_id = results.get('next_max_id')

    followers.sort(key=lambda x: x['pk'])
    # print list of user IDs
    print(json.dumps([u['pk'] for u in followers], indent=2))

    # ---------- Pagination with rank_token and exclusion list ----------
    rank_token = Client.generate_uuid()
    has_more = True
    tag_results = []
    while has_more and rank_token and len(tag_results) < 60:
        results = api.tag_search(
            'cats', rank_token, exclude_list=[t['id'] for t in tag_results])
        tag_results.extend(results.get('results', []))
        has_more = results.get('has_more')
        rank_token = results.get('rank_token')
    print(json.dumps([t['name'] for t in tag_results], indent=2))
