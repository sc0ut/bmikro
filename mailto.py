import smtplib


def send_mail(event, msg):
    mess = []
    if event == 1:
        title = 'Список недоступных роутеров'
        mess = f'\n {title} : \n \n' + f' \n'.join(msg)
    elif event == 2:
        title = 'Изменения в конфигурации '
        mess = f"\n{title}: \n" + f"Роутер: " + msg[0] + "\n\n" + f' \n'.join(msg[1:])
    smtpObj = smtplib.SMTP('adr_srv', 25)
    smtpObj.login('from@mail.com', 'password')
    smtpObj.sendmail("from@mail.com", "to@mail.com", mess.encode('utf-8'))
    smtpObj.quit()
    print('mail send')


if __name__ == '__main__':
    send_mail()