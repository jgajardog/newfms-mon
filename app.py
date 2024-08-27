import mysql.connector
from os import getenv
import subprocess
import time
import logging
import datetime
logging.basicConfig(encoding='utf-8', level=logging.INFO)
def log(m):
    logging.info(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}; {m}")

db_user = getenv('J_MYSQL_USER')
db_password = getenv('J_MYSQL_PASSWORD')
db_host = getenv('J_MYSQL_IP')
db_name = getenv('J_MYSQL_DB')
buscar = getenv('J_ROLE')
vip = getenv('J_VIP')

keep_CR=f"KEEPALIVE*PENA_P1_KEEPALIVE_{buscar}_NEWFMS|NOC|*KEEPALIVE*Out Of Service*CR*11111111"
keep_NM=f"KEEPALIVE*PENA_P1_KEEPALIVE_{buscar}_NEWFMS|NOC|*KEEPALIVE*In Service Normal*NM*11111111"

config = {
    'user': db_user,
    'password': db_password,
    'host': db_host,
    'database': db_name
}

def enviar_trap(alm, dst):
    command = [
        'snmptrap', '-v', '1', '-c', 'public', dst, '',
        'localhost', '0', '0', '1000', '.1.3.6.1.4.1.11.2.17.2.4', 's', alm
    ]
    try:
        subprocess.run(command, check=True)
        return 0
    except Exception as e:
        log(f"Error al enviar trap: {e}")
        return 1

def get_data(config):
    try:
        conexion = mysql.connector.connect(**config)
        cursor = conexion.cursor()
        consulta = f"SELECT COUNT(*) FROM ALARMA WHERE TECNOLOGIA='KEEPALIVE' AND SEVERIDAD='NM' AND AMO REGEXP 'KEEPALIVE_{buscar}_NEWFMS' AND LASTTIME>=DATE_SUB(NOW(), INTERVAL 15 SECOND)"
        cursor.execute(consulta)
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()
        if int(resultado[0])>0:
            return 0
        else:
            return 1
    except Exception as e:
        log(f"ERR {e}")
        return 1

def check_db(config):
    try:
        conexion = mysql.connector.connect(**config)
        cursor = conexion.cursor()
        consulta = f"SELECT COUNT(*) FROM ALARMA WHERE  LASTTIME>=DATE_SUB(NOW(), INTERVAL 5 MINUTE)"
        cursor.execute(consulta)
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()
        if int(resultado[0])>0:
            return 0
        else:
            return 1
    except Exception as e:
        log(f"ERR check_db {e}")
        return 1


while True:
    checkdb=check_db(config)
    if checkdb==0:
        trap=enviar_trap(keep_NM,db_host)
        time.sleep(1)
        data=get_data(config)
        if((trap==0) and (data==0)):
            log("Todo OK")
        else:
            trap=enviar_trap(keep_CR,vip)
            log("FALLA")
    else:
        trap=enviar_trap(keep_CR,vip)
        log("FALLA DB LOCAL")
    time.sleep(4)
