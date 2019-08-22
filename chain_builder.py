#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml
import requests
import sys
import urllib.parse
import re
import time

sys.path.append(os.path.dirname(__file__))
import chain_builder_lib

work_dir = os.path.dirname(__file__)
current_dir = os.path.join(work_dir , 'current')
temp_dir = os.path.join(work_dir , 'temp')

def get_chain(l_chain_url):
    try:
        r = requests.get(l_chain_url, verify=False)
    except Exception:
        chain_builder_lib.in_log('Error requests chain file!')
        return False
    if r.status_code == 200:
        try:
            l_chain = yaml.load(r.content.decode("utf-8"))
        except Exception:
            chain_builder_lib.in_log('Error chain format!')
            return False
    else:
        chain_builder_lib.in_log('Error requests chain file!')
        return False
    if l_chain:
        return l_chain
    else:
        chain_builder_lib.in_log('Chain file is empty!')
        return False

def find_current_file(l_current_dir):
    list_current_dir = [f for f in os.listdir(l_current_dir) if f.endswith('.tar')]
    list_current_dir.sort()
    for file_name in list_current_dir[::-1]:
        if re.findall(r'.*-([0-9\.]+-[0-9]+)\.tar$', file_name):
            l_current_file = os.path.join(l_current_dir, file_name)
            return l_current_file
    return None

def get_position(l_current_version, l_chain):
    l_start_pos = -1
    l_stop_pos = -1
    for index in range(len(l_chain)):
        if l_start_pos == -1:
            if l_chain[index]['version'] == l_current_version:
                l_start_pos = index
            continue
        else:
            if l_chain[index]['version'] > l_current_version:
                l_stop_pos = index
            continue
    return l_start_pos, l_stop_pos

def build_chain(l_chain, l_start_pos, l_stop_pos, l_current_file, l_current_dir, l_temp_dir, l_config):
    temp_current_file = l_current_file
    for index in range(l_start_pos+1, l_stop_pos+1):
        if not chain_builder_lib.download_file(urllib.parse.urljoin(l_config['url'], l_chain[index]['delta']), l_temp_dir):
            return False
        delta_file = os.path.join(l_temp_dir, l_chain[index]['delta'])
        l_new_current_file = os.path.join(l_temp_dir, l_chain[index]['file'])
        if chain_builder_lib.md5_file_checksum(delta_file) != l_chain[index]['delta_md5']:
            chain_builder_lib.in_log('Bad delta file checksum!')
            return False
        if not chain_builder_lib.run_cmd('{0} -f -d -s {1} {2} {3}'.format(os.path.join(os.path.dirname(__file__), 'bin', l_config['bin_xdelta3']),
                                                                           temp_current_file, delta_file, l_new_current_file)):
            return False
        if chain_builder_lib.md5_file_checksum(l_new_current_file) == l_chain[index]['file_md5']:
            if index != l_start_pos+1:
                chain_builder_lib.del_file(temp_current_file)
            chain_builder_lib.del_file(delta_file)
            temp_current_file = l_new_current_file
        else:
            chain_builder_lib.in_log('Bad new current file checksum!')
            return False
    if not chain_builder_lib.del_files_on_type(l_current_dir, 'tar'):
        return False
    temp_current_file = chain_builder_lib.move_file(temp_current_file, l_current_dir)
    chain_builder_lib.in_log('New file {0} is downloaded.'.format(os.path.split(temp_current_file)[-1]))
    return temp_current_file

def install_app(l_tar_file, l_config):
    chain_builder_lib.in_log('Start update simclient to: {0}'.format(l_tar_file))
    temp_app = os.path.join(temp_dir, 'app')
    if not chain_builder_lib.del_dir(temp_app):
        chain_builder_lib.in_log('Folder deletion error: {0}'.rormat(temp_app))
        return False
    else:
        os.mkdir(temp_app)
    if not chain_builder_lib.unpack_tar(l_tar_file, temp_app):
        chain_builder_lib.in_log('Error unpack tar file: {0}'.rormat(l_tar_file))
        return False
    for retry in range(3):
        time.sleep(3)
        for folder in l_config['simclient_folders']:
            if not chain_builder_lib.del_dir(os.path.join(l_config['simclient_path'], folder + '.new')):
                chain_builder_lib.in_log('Folder deletion error: {0}'.format(os.path.join(l_config['simclient_path'], folder)))
                break
            if not chain_builder_lib.cp_move_folder(os.path.join(temp_app, folder),
                                                    os.path.join(l_config['simclient_path'], folder + '.new'),
                                                    'cp'):
                chain_builder_lib.in_log('Folder copy error: {0}'.format(os.path.join(temp_app, folder)))
                break
        chain_builder_lib.in_log('Killing simclient!!!')
        chain_builder_lib.run_cmd('taskkill /f /im java.exe /fi "USERNAME eq terminal" /t')
        time.sleep(3)
        for folder in l_config['simclient_folders']:
            if not chain_builder_lib.del_dir(os.path.join(l_config['simclient_path'], folder)):
                chain_builder_lib.in_log('Folder deletion error: {0}'.format(os.path.join(l_config['simclient_path'], folder)))
                break
            try:
                os.rename(os.path.join(l_config['simclient_path'], folder + '.new'), os.path.join(l_config['simclient_path'], folder))
            except Exception:
                chain_builder_lib.in_log('Folder rename error: {0}'.format(os.path.join(l_config['simclient_path'], folder + '.new')))
                break
            if folder == l_config['simclient_folders'][-1]:
                return True
    return False

def lock(l_temp_dir):
    if not l_temp_dir:
        return False
    lock_file = os.path.join(l_temp_dir, 'lock')
    if os.path.exists(lock_file):
        return True
    else:
        try:
            with open(lock_file, 'w+'):
                os.utime(lock_file)
                return True
        except Exception:
            return False

def unlock(l_temp_dir):
    if not l_temp_dir:
        return False
    lock_file = os.path.join(l_temp_dir, 'lock')
    if not os.path.exists(lock_file):
        return True
    else:
        try:
            os.remove(lock_file)
            return True
        except Exception:
            return False

def check_lock(l_temp_dir):
    if not l_temp_dir:
        return False
    lock_file = os.path.join(l_temp_dir, 'lock')
    if os.path.exists(lock_file):
        return True
    else:
        return False

chain_builder_lib.in_log('Start!')

while True:
    try:
        config = yaml.load(open(os.path.join(os.path.dirname(__file__), 'config.yml')))
    except Exception:
        chain_builder_lib.in_log('Error open config file!')
        sys.exit(1)

    time.sleep(config['timeout'])

    new_current_file = ''
    chain_url = urllib.parse.urljoin(config['url'], 'chain.yml')
    chain = get_chain(chain_url)

    if not chain:
        continue

    current_file = find_current_file(current_dir)

    if not current_file:
        chain_builder_lib.in_log('Current file not found! Downloading last build...')
        current_file = os.path.join(current_dir, chain[-1]['file'])
        if not chain_builder_lib.download_file(urllib.parse.urljoin(config['url'], chain[-1]['file']), current_dir) or \
                not chain_builder_lib.md5_file_checksum(current_file) == chain[-1]['file_md5']:
            chain_builder_lib.in_log('Error on downloading last build!')
            chain_builder_lib.del_file(current_file)

    current_version = re.findall(r'.*-([0-9\.]+-[0-9]+)\.tar$', current_file)[0]

    start_pos, stop_pos = get_position(current_version, chain)

    if start_pos == -1 or chain_builder_lib.md5_file_checksum(current_file) != chain[start_pos]['file_md5']:
        chain_builder_lib.in_log('The checksum of the current file is incorrect or the current file is not in the chain. Current file deleted!')
        chain_builder_lib.del_file(current_file)
        continue

    if stop_pos == -1 and os.path.exists(os.path.join(temp_dir, 'app')) and not check_lock(temp_dir):
        continue
    elif stop_pos == -1 and (not os.path.exists(os.path.join(temp_dir, 'app')) or check_lock(temp_dir)):
        new_current_file = current_file
    elif stop_pos != -1:
        new_current_file = build_chain(chain, start_pos, stop_pos, current_file, current_dir, temp_dir, config)

    if new_current_file:
        lock(temp_dir)
        if install_app(new_current_file, config):
            unlock(temp_dir)
            chain_builder_lib.in_log('Successful installed: {0}'.format(new_current_file))
        else:
            chain_builder_lib.in_log('Unsuccessful installation: {0} !!!'.format(new_current_file))
        continue
    else:
        continue