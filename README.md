# Bmikro
### Бэкап и отслеживание изменений в конфигурации роутеров *Mikrotik*
Скрипт предназначен для отслеживания изменения конфигурации роутеров *Mikrotik*. Только для запуска на Linux OS, для автоматизации запуска используется `Crontab`. 
> https://crontab.guru/ - Удобный генератор времени запуска.

В начале проверяется доступность роутеров для подключения, список не доступных для подключения роутеров отправляется на 
почту администратора. Далее идёт создание и скачивание файлов конфигурации и бэкапа роутера на сервер, после запускается 
проверка конфигурации роутера библиотекой Python 3 - `difflib` - Результаты отправляются на почту администратора.
Создаётся за один раз 3 файла - `.rsc`, `.backup`, `.info`

### Настройка и запуск скрипта
* Минимальная версия Python 3.6, так же требуются библиотеки [PyYaml](https://pypi.org/project/PyYAML/) и [Paramiko](http://www.paramiko.org/installing.html)
* На роутере создаём отдельного пользователя, генерируем ключи на сервере и устанавливаем их для этого пользователя. 
Вносим в группу роутеров данные: Название группы, имя пользователя, путь к ключу, IP - роутеров. Запускаем первый раз скрипт вручную
`python3 main.py` - будут созданы каталоги и созданые первые снимки системы.
> Генерация ключей на сервере командой *nix: `ssh-keygen -t rsa` Путь к ключам по умолчанию (`home/*user*/.ssh/`) `id_rsa` остаётся на сервере бэкапа, `id_rsa.pub` на "Mikrotik"
Добавление ключа к пользователю "Mikrotik" - на ротуер закинуть ключ и выполнить команду:
`/user ssh-keys import user=USERNAME public-key-file=id_rsa.pub`
Посмотреть ключи `/user ssh-keys print`
* После успешной отладки добавляем его в автозапуск Cron'a
> `crontab -e` - Откроет для редактирования файл Cron'a текущего пользователя (`-u` выбрать другого пользователя).
`0 6 */1 * * /usr/bin/python3 /home/*user*/main.py` - Запуска скрипта каждый день в 6 утра, путь к интерпретатору Python3, путь к скрипту.
* Файлы создаются по маске `%d%m%Y-%H%M%S`.

### Описание файлов настроек 
* Настройки и список роутеров содержит файл `setting.yml`
* Авторизация происходит по ключам, каждой группе роутеров можно присвоить свои ключи. 
* Хранилищем групп и списков роутеров является директория `routing_list` 
  * `all_router` - группа роутеров (Может быть любым именем, но не содержать символы пробела)
    * `user` - имя пользователя роутеров к кому привязан ключ *RSA*
    * `key_file` - путь к ключу на сервере
    * `port` - порт группы (не рекомендуется использовать по умолчанию)
    * `list_ip` - список IP роутеров
      * `192.168.0.1` - IP роутера
* Директория `command` содержит команды терминала роутера
  * getNameRoute - `/system identity print` Получение идентификационного имени роутера
  * createConfigFile - `/export terse file=/backup/` Экспорт файла с конфигурацией роутера
    * `terse`(По умолчанию) - Не переносит строки, не рекомендуется изменять
    * `verbose` - создаёт полный конфиг включая настройки роутера по умолчанию 
    * `compact` - только отличия от конфигурации по умолчанию (По умолчанию RouterOS 6)
  * createBackupFile - `/system backup save name=/backup/` Снятие бинарного бэкапа роутера. Можно восстановить только на этот же роутер
  * getRouteInfo - `/system resource print` Получение снимка состояния железа и etc. на момент создание бэкапа.
* `setting` - дополнительные настройки
  * `dir_backup` - директория на роутере где хранятся бэкапы
  * `dir_srv` - директория на сервере где будут хранится конфигурационные файлы и бэкапы
