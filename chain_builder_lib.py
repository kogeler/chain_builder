#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import hashlib
import subprocess
import shutil
import time
import glob
import sys

def in_log(mess):
    now_time = time.strftime('%Y.%m.%d %H:%M:%S', time.localtime())
    mess = '{0}	{1}\n'.format(now_time, mess)
    print(mess)
    try:
        log_file.write(mess)
        log_file.flush()
    except Exception:
        print('Error write in log file!')
        return False
    return True

def download_file(url, dest_dir, user=None, password=None, retries = 3):
    for retry in range(retries):
        try:
            if user and password:
                r = requests.get(url, auth=requests.auth.HTTPBasicAuth(user, password), stream=True, verify=False)
            else:
                r = requests.get(url, stream=True, verify=False)
        except Exception:
            continue
        try:
            with open(os.path.join(dest_dir, url.split('/')[-1]), 'wb+') as fd:
                for chunk in r.iter_content(chunk_size=128):
                    fd.write(chunk)
            return True
        except Exception:
            continue
    time.sleep(10)
    return False

def md5_file_checksum(file):
    if not os.path.exists(file) or not os.path.isfile(file):
        return None
    try:
        with open(file, 'rb') as fh:
            m = hashlib.md5()
            while True:
                data = fh.read(8192)
                if not data:
                    break
                m.update(data)
            return m.hexdigest()
    except Exception:
        return None

def run_cmd(cmd):
    try:
        proces = subprocess.Popen(cmd, shell=True)
        proces.wait()
    except Exception:
        return False
    if proces.returncode:
        return False
    else:
        return True

def del_dir(dir):
    if not dir:
        return False
    if os.path.exists(dir) and os.path.isdir(dir):
        try:
            shutil.rmtree(dir, ignore_errors=True)
        except Exception:
            return False
        return True
    else:
        return False

def del_file(file):
    if not file:
        return False
    if not os.path.exists(file):
        return True
    if os.path.isfile(file):
        try:
            os.remove(file)
        except Exception:
            return False
        return True
    else:
        return False

def del_files_on_type(dir, type):
    if not dir or not type:
        return False
    if os.path.exists(dir) and os.path.isdir(dir):
        for file in glob.glob(os.path.join(dir, '*.' + type)):
            try:
                os.remove(file)
            except Exception:
                return False
        return True
    else:
        return False

def del_dir(dir):
    if not dir:
        return False
    if not os.path.exists(dir):
        return True
    if os.path.isdir(dir):
        try:
            shutil.rmtree(dir)
            return True
        except Exception:
            return False
    else:
        return False

def move_file(src_file, dst_path):
    if not src_file or not dst_path:
        return False
    dst_file = os.path.join(dst_path, os.path.split(src_file)[-1])
    if os.path.exists(src_file) and os.path.isfile(src_file) and os.path.exists(dst_path) \
            and os.path.isdir(dst_path) and not os.path.exists(dst_file):
        try:
            shutil.move(src_file, dst_file)
        except Exception:
            return False
        return dst_file
    else:
        return False

def cp_move_folder(src_path, dst_path, action, full=True):
    if not src_path or not dst_path or not action:
        return False
    if full:
        full_dst_path = dst_path
    else:
        full_dst_path = os.path.join(dst_path, os.path.split(src_path)[-1])
    if os.path.exists(src_path) and os.path.isdir(src_path) and \
            ((not full and os.path.exists(dst_path) and os.path.isdir(dst_path) and not os.path.exists(full_dst_path)) \
             or (full and not os.path.exists(full_dst_path))):
        try:
            if action == 'cp':
                shutil.copytree(src_path, full_dst_path)
            elif action == 'mv':
                shutil.move(src_path, full_dst_path)
            else:
                return False
        except Exception:
            return False
        return full_dst_path
    else:
        return False

def unpack_tar(tar_file, dst_path):
    if not tar_file or not dst_path:
        return False
    if os.path.exists(tar_file) and os.path.isfile(tar_file) and os.path.exists(dst_path) and os.path.isdir(dst_path):
        try:
            shutil.unpack_archive(tar_file, dst_path)
        except Exception:
            return False
        return True
    else:
        return False

try:
    log_file = open(os.path.join(os.path.dirname(__file__), 'log.txt'), 'a')
except Exception:
    print('Error open log file!')
    sys.exit(1)