import paramiko
from django.utils import timezone
import telnetlib
import time
from datetime import datetime


# Função para atualizar o campo UltimoBackup no banco de dados
def atualizar_ultimo_backup(self):
    self.UltimoBackup = timezone.now()  # Use timezone.now() ao invés de datetime.now()
    self.save()
    print(f"Data do último backup atualizada para o equipamento: {self.descricao}")

def acessar_equipamento(id, ip, usuario, senha, porta, comando, nome_equipamento, protocolo="SSH", tempo_maximo=240):
    if protocolo == "SSH":
        return acessar_ssh(id, ip, usuario, senha, porta, comando, nome_equipamento, tempo_maximo)
    elif protocolo == "Telnet":
        return acessar_telnet(id, ip, usuario, senha, porta, comando, nome_equipamento, tempo_maximo)
    else:
        raise ValueError(f"Protocolo inválido: {protocolo}")



def acessar_ssh(id, ip, usuario, senha, porta, comando, nome_equipamento, tempo_maximo=60):
    """
    Função para acessar um equipamento via SSH.
    """
    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Conexão ao equipamento
        cliente.connect(ip, port=porta, username=usuario, password=senha, timeout=60)

        # Criação do canal para envio de comandos
        canal = cliente.invoke_shell()
        canal.settimeout(2)

        # Captura da mensagem inicial
        print("Capturando mensagem inicial via SSH...")
        inicio = time.time()
        while True:
            if canal.recv_ready():
                mensagem_inicial = canal.recv(4096).decode('utf-8')
                print(f"Mensagem inicial recebida:\n{mensagem_inicial}")
                if mensagem_inicial.strip().endswith(">") or mensagem_inicial.strip().endswith("#"):  # Adapte o prompt
                    break
            if time.time() - inicio > 30:
                raise Exception("Tempo limite ao capturar a mensagem inicial.")
            time.sleep(1)

        # Desativando paginação
        print("Desativando paginação via SSH...")
        canal.send("terminal length 0\n")
        time.sleep(2)
        while canal.recv_ready():
            canal.recv(4096)

        # Executando comando principal
        print(f"Executando comando via SSH no equipamento {nome_equipamento}...")
        canal.send(comando + '\n')
        resposta = ""
        inicio = time.time()

        while True:
            if time.time() - inicio > tempo_maximo:
                raise Exception("Tempo limite excedido ao aguardar resposta do equipamento.")

            if canal.recv_ready():
                resposta_parcial = canal.recv(4096).decode('utf-8')
                resposta += resposta_parcial
                print(f"Resposta parcial capturada:\n{resposta_parcial}")

                if resposta.strip().endswith("Fim") or resposta.strip().endswith("#"):
                    print("Comando executado, prompt detectado.")
                    break

            time.sleep(1)

        # Fechamento do canal
        canal.close()
        return resposta

    except Exception as e:
        raise Exception(f"Erro ao acessar o equipamento via SSH: {str(e)}")
    finally:
        cliente.close()


def acessar_telnet(id, ip, usuario, senha, porta, comando, nome_equipamento, tempo_maximo=240):
    """
    Função para acessar um equipamento via Telnet e executar comandos, lidando com paginação (--More--).
    """
    try:
        print(f"Conectando via Telnet ao equipamento {nome_equipamento}...")

        # Inicia a conexão Telnet
        cliente = telnetlib.Telnet(ip, port=porta, timeout=60)

        # Lê até o prompt de login
        prompt_login = cliente.read_until(b"login: ", timeout=10)
        print(f"Prompt de login recebido: {prompt_login.decode('utf-8')}")

        # Envia o nome de usuário
        cliente.write(usuario.encode('ascii') + b"\n")

        # Lê até o prompt de senha
        prompt_password = cliente.read_until(b"Password: ", timeout=10)
        print(f"Prompt de senha recebido: {prompt_password.decode('utf-8')}")

        # Envia a senha
        cliente.write(senha.encode('ascii') + b"\n")

        # Aguarda estabilizar e lê a saída inicial
        time.sleep(2)
        inicial = cliente.read_very_eager().decode('utf-8')
        print(f"Saída inicial após login:\n{inicial}")

        # Desativa a paginação (depende do comando do equipamento, ajuste se necessário)
        cliente.write(b"terminal length 0\n")
        time.sleep(2)
        resposta_pag = cliente.read_very_eager().decode('utf-8')
        print(f"Resposta ao desativar paginação: {resposta_pag}")

        # Envia o comando principal
        print(f"Executando comando via Telnet no equipamento {nome_equipamento}...")
        cliente.write(comando.encode('ascii') + b"\n")
        resposta = ""
        inicio = time.time()

        while True:
            if time.time() - inicio > tempo_maximo:
                raise Exception("Tempo limite excedido ao aguardar resposta do equipamento.")

            resposta_parcial = cliente.read_very_eager().decode('utf-8')
            resposta += resposta_parcial
            print(f"Resposta parcial capturada via Telnet:\n{resposta_parcial}")

            # Detecta o "--More--" e envia espaço para continuar
            if "--More--" in resposta_parcial:
                cliente.write(b" ")  # Envia espaço
                time.sleep(0.5)  # Aguarda o próximo trecho

            # Verifica o fim do comando com um prompt
            elif resposta.strip().endswith(">") or resposta.strip().endswith("#"):
                print("Comando executado, prompt detectado.")
                break

            time.sleep(1)

        # Envia o comando para encerrar a sessão
        cliente.write(b"exit\n")
        cliente.close()

        return resposta

    except Exception as e:
        raise Exception(f"Erro ao acessar o equipamento via Telnet: {str(e)}")


# Função para capturar o prompt inicial
def capturar_prompt(conexao, prompt_fim, tempo_maximo):
    inicio = time.time()
    while True:
        if isinstance(conexao, paramiko.Channel):
            if conexao.recv_ready():
                mensagem_inicial = conexao.recv(4096).decode('utf-8')
                if mensagem_inicial.strip().endswith(tuple(prompt_fim.split("#"))):
                    break
        elif isinstance(conexao, telnetlib.Telnet):
            mensagem_inicial = conexao.read_very_eager().decode('ascii')
            if mensagem_inicial.strip().endswith(tuple(prompt_fim.split("#"))):
                break

        if time.time() - inicio > tempo_maximo:
            raise Exception("Tempo limite ao capturar a mensagem inicial.")
        time.sleep(1)


# Função para capturar a resposta do comando
def capturar_resposta(conexao, prompt_fim, tempo_maximo):
    resposta = ""
    inicio = time.time()
    while True:
        if isinstance(conexao, paramiko.Channel):
            if conexao.recv_ready():
                print("Iniciou via SSH")
                resposta_parcial = conexao.recv(4096).decode('utf-8')
                resposta += resposta_parcial
                if resposta.strip().endswith(tuple(prompt_fim.split("#"))):
                    break
        elif isinstance(conexao, telnetlib.Telnet):
            print("Iniciou via Telnet")
            resposta_parcial = conexao.read_very_eager().decode('ascii')
            resposta += resposta_parcial
            print(f"{resposta}")
            if resposta.strip().endswith(tuple(prompt_fim.split("#"))):
                break

        if time.time() - inicio > tempo_maximo:
            raise Exception("Tempo limite excedido ao aguardar resposta do equipamento.")
        time.sleep(1)

    return resposta
