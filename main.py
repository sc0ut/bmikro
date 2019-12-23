#!/usr/bin/python3
import os, os.path
import yaml
import datetime
import time
import paramiko
import difflib
from mailto import send_mail


"""
TODO:
    SEND_MAIL:
        Сделать HTML-вёрстку писем
        Сделать отправку письма о недоступности роутеров с группировкой.
        Если есть изменения в конфигурации, то на каждую группу отправлять отдельное письмо
    TELEGRAM:
        Добавить возможность отправлять сообщения в бота
    CODE:
        Прикрутить логирование
"""

with open(os.path.abspath(os.curdir) + '/setting.yml') as f:
    config = yaml.safe_load(f)
sshdd = paramiko.SSHClient()
getNameRoute = config['command']['getNameRoute']
createConfigFile = config['command']['createConfigFile']
createBackupFile = config['command']['createBackupFile']
getRouteInfo = config['command']['getRouteInfo']
dir_backup = config['setting']['dir_backup']
dir_srv = config['setting']['dir_srv']


def clear_backup():
    for i in os.listdir(dir_srv):
        for ii in os.listdir(dir_srv + i):
            listing_delete = os.listdir(dir_srv + i + '/' + ii)
            while len(listing_delete) > 9:
                listing_delete.sort()
                os.remove(dir_srv + i + '/' + ii + '/' + listing_delete[0])
                listing_delete.pop(0)


def diff_file(i):
    msg = []
    remove_conf = []
    add_conf = []
    for iii in os.listdir(dir_srv + i):
        dir_cursor = dir_srv + i + '/' + iii
        routers = i + ' | ' + iii
        list_file = os.listdir(dir_cursor)
        list_rsc = []
        if list_file:
            for inn in list_file:
                if inn.endswith('.rsc'):
                    list_rsc.append(inn)
            list_rsc.sort()
            if len(list_rsc) > 2:
                t2 = open(dir_cursor + '/' + list_rsc[-1], 'r').readlines()
                t1 = open(dir_cursor + '/' + list_rsc[-2], 'r').readlines()
                for line in difflib.unified_diff(t1, t2, n=0):
                    if line[:3] == '@@ ' or line[:3] == '---' or line[:3] == '+++' or line[:3] == '+# ' or line[:3] == '-# ':
                        pass
                    else:
                        if line[:1] == '+':
                            add_conf.append(line)
                        elif line[:1] == '-':
                            remove_conf.append(line)
            if add_conf is None or remove_conf is None:
                pass
            else:
                if add_conf:
                    msg.insert(1, 'Добавлено: \n')
                    msg.extend(add_conf)
                if remove_conf:
                    msg.append('Удаленные: \n')
                    msg.extend(remove_conf)
                if not msg:
                    pass
                else:
                    msg.insert(0, routers + ' \n')
                    send_mail(2, msg)
                    msg = []
                    remove_conf = []
                    add_conf = []


def download_backup(id_and_ip, user, key_file, new_port, now, i_key):
    for i in id_and_ip:
        home_dir = dir_srv + i_key + '/' + i + '-' + id_and_ip.get(i)
        transport = paramiko.Transport((id_and_ip.get(i), int(new_port)))
        key = paramiko.RSAKey.from_private_key_file(key_file)
        transport.connect(username=user, pkey=key)
        sftp = paramiko.SFTPClient.from_transport(transport)
        listing_del = []
        try:
            listing_all = sftp.listdir(dir_backup)
            listing = []
            if listing_all:
                for ww in listing_all:
                    if ww.endswith('.rsc'):
                        listing.append(ww)
                    if ww.endswith('.backup'):
                        listing.append(ww)
            if not listing:
                print('Нет файлов! Пора бы уже прикрутить логи...')
            else:
                if listing.count(now + '.rsc') >= 1:
                    sftp.get(dir_backup + '/' + now + '.rsc', home_dir + '/' + now + '.rsc')
                    sftp.remove(dir_backup + '/' + now + '.rsc')
                if listing.count(now + '.backup') >= 1:
                    sftp.get(dir_backup + '/' + now + '.backup', home_dir + '/' + now + '.backup')
                    for ee in listing:
                        if ee.endswith('.backup'):
                            listing_del.append(ee)
                    while len(listing_del) > 3:
                        listing_del.sort()
                        sftp.remove(dir_backup + '/' + listing_del[0])
                        listing_del.pop(0)
            sftp.close()
            sshdd.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            sshdd.connect(hostname=str(id_and_ip.get(i)), port=int(new_port), username=str(user), key_filename=str(key_file))
            stdin, stdout, stderr = sshdd.exec_command(getRouteInfo)
            info = stdout.read().decode('utf-8')
            with open(home_dir + '/' + now + '.info', 'w') as f:
                f.write(info)
        except IOError:
            print(IOError)
            print(dir_backup + '/' + listing_del[0])
            sftp.close()


def make_backup(id_and_ip, user, key_file, new_port, now):
    for i in id_and_ip:
        sshdd.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sshdd.connect(hostname=str(id_and_ip.get(i)), port=int(new_port), username=str(user), key_filename=str(key_file))
        time.sleep(0.5)
        sshdd.exec_command(createConfigFile + now)
        time.sleep(0.5)
        sshdd.exec_command(createBackupFile + now)
        time.sleep(1.5)
    sshdd.close()


def look_dir(id_and_ip, i_key):
    if os.path.isdir(dir_srv + i_key):
        for i in id_and_ip:
            end = i + '-' + id_and_ip.get(i)
            if os.path.isdir(dir_srv + i_key + '/' + end):
                continue
            else:
                os.mkdir(dir_srv + i_key + '/' + end)
    else:
        os.mkdir(dir_srv + i_key)
        for i in id_and_ip:
            end = i + '-' + id_and_ip.get(i)
            if os.path.isdir(dir_srv + i_key + '/' + end):
                continue
            else:
                os.mkdir(dir_srv + i_key + '/' + end)
    return True


def ping_routing(user, key_file, list_ip, new_port):
    true_ip = []
    id_and_ip = {}
    if type(list_ip) is list:
        for ip in list_ip:
            try:
                sshdd.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                sshdd.connect(hostname=str(ip), port=int(new_port), username=str(user), key_filename=str(key_file), timeout=3)
                true_ip.append(ip)
            except paramiko.ssh_exception.BadHostKeyException:
                print('BadHostKeyException: ' + ip)
            except paramiko.ssh_exception.AuthenticationException:
                print('AuthenticationException: ' + ip)
            except IOError:
                print('IOError: Timeout in ' + ip)
            except paramiko.ssh_exception.SSHException:
                print('SSHException:' + ip)
            sshdd.close()
        if true_ip is None:
            pass
        else:
            for ip in true_ip:
                sshdd.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                sshdd.connect(hostname=str(ip), port=int(new_port), username=str(user), key_filename=str(key_file))
                stdin, stdout, stderr = sshdd.exec_command(getNameRoute)
                res = stdout.read().decode('utf-8')
                sftp = sshdd.open_sftp()
                try:
                    sftp.listdir(dir_backup)
                except:
                    sftp.mkdir(dir_backup)
                sftp.close()
                sshdd.close()
                a = res.find(':')
                b = res[a + 1:].strip(' \n\r')
                id_and_ip[b] = ip
        all_ip = list(set(true_ip) ^ set(list_ip))
        if not all_ip:
            all_ip2 = False
            return id_and_ip, all_ip2
        else:
            return id_and_ip, all_ip
    else:
        print('Да, да прошли выходные а логирования нет :(')


def get_user_and_key(key):
    if os.path.isdir(dir_srv):
        pass
    else:
        os.mkdir(dir_srv)
    user = config['routing_list'][key]['user']
    key_file = config['routing_list'][key]['key_file']
    list_ip = config['routing_list'][key]['list_ip']
    new_port = config['routing_list'][key]['port']
    return user, key_file, list_ip, new_port


def get_current_date_time():
    now = datetime.datetime.today().strftime('%d%m%Y-%H%M%S')
    return now


def main():
    msg_container = []
    if config:
        now = get_current_date_time()
        for i in config['routing_list']:
            user, key_file, list_ip, new_port = get_user_and_key(i)
            id_and_ip, all_ip = ping_routing(user, key_file, list_ip, new_port)
            if all_ip is False:
                pass
            else:
                msg_container.extend(id_and_ip)
            if look_dir(id_and_ip, i) is True:
                make_backup(id_and_ip, user, key_file, new_port, now)
                download_backup(id_and_ip, user, key_file, new_port, now, i)
                diff_file(i)
            else:
                pass
        if not msg_container:
            pass
        else:
            send_mail(1, msg_container)
    clear_backup()


if __name__ == '__main__':
    main()
