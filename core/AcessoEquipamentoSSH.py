import paramiko
import telnetlib
import time
from datetime import datetime
from django.utils import timezone

# Função para atualizar o campo UltimoBackup no banco de dados
def atualizar_ultimo_backup(self):
    self.UltimoBackup = timezone.now()
    self.save()
    print(f"Data do último backup atualizada para o equipamento: {self.descricao}")

# Função para acessar equipamentos genéricos
def acessar_equipamento(id, ip, usuario, senha, porta, comando, nome_equipamento, protocolo="SSH", tempo_maximo=240):
    """
    Acessa o equipamento e executa um comando via SSH ou Telnet.
    """
    # Formata comando com variáveis dinâmicas
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    nome_backup = f"{nome_equipamento}_{timestamp}"
    nome_pasta = f"{nome_equipamento}"
    comando = comando.replace("$namebackup", nome_backup)
    comando = comando.replace("$namepasta", nome_pasta)

    if protocolo == "SSH":
        return acessar_ssh(id, ip, usuario, senha, porta, comando, nome_equipamento, tempo_maximo)
    elif protocolo == "Telnet":
        return acessar_telnet(id, ip, usuario, senha, porta, comando, nome_equipamento, tempo_maximo)
    else:
        raise ValueError(f"Protocolo inválido: {protocolo}")

def acessar_ssh(id, ip, usuario, senha, porta, comando, nome_equipamento, tempo_maximo=120):
    """
    Acessa o equipamento via SSH e executa comandos.
    """
    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        cliente.connect(ip, port=porta, username=usuario, password=senha, timeout=60)

        # Criação do canal
        canal = cliente.invoke_shell()
        canal.settimeout(2)

        # Captura da mensagem inicial
        print("Capturando mensagem inicial via SSH...")
        capturar_prompt(canal, [">", "#"], 30)

        # Desativar paginação
        print("Desativando paginação via SSH...")
        #canal.send("terminal length 0\n")
        time.sleep(2)

        # Aguardando estabilização
        print("Aguardando equipamento estabilizar...")
        time.sleep(2)

        # Envia o comando principal
        print(f"Executando comando via SSH no equipamento {nome_equipamento}...")
        canal.send(comando + '\n')

        # Captura da resposta
        resposta = capturar_resposta(canal, [">", "#"], tempo_maximo)
        return resposta

    except Exception as e:
        raise Exception(f"Erro ao acessar o equipamento via SSH: {str(e)}")
    finally:
        cliente.close()

def acessar_telnet(id, ip, usuario, senha, porta, comando, nome_equipamento, tempo_maximo=120):
    """
    Acessa o equipamento via Telnet e executa comandos.
    """
    try:
        print(f"Conectando via Telnet ao equipamento {nome_equipamento}...")
        cliente = telnetlib.Telnet(ip, port=porta, timeout=60)

        # Envia credenciais
        cliente.read_until(b"login: ", timeout=10)
        cliente.write(usuario.encode('ascii') + b"\n")
        cliente.read_until(b"Password: ", timeout=10)
        cliente.write(senha.encode('ascii') + b"\n")

        # Captura da mensagem inicial
        print("Capturando mensagem inicial via Telnet...")
        capturar_prompt(cliente, ">#", tempo_maximo)

        # Desativando paginação
        print("Desativando paginação via Telnet...")
        cliente.write(b"terminal length 0\n")
        time.sleep(2)
        cliente.read_very_eager()  # Limpa o buffer

        # Aguardando estabilização
        print("Aguardando equipamento estabilizar...")
        time.sleep(2)

        # Envia o comando principal
        print(f"Executando comando via Telnet no equipamento {nome_equipamento}...")
        cliente.write(comando.encode('ascii') + b"\n")

        # Captura da resposta
        resposta = capturar_resposta(cliente, [">", "#"], tempo_maximo)
        return resposta

    except Exception as e:
        raise Exception(f"Erro ao acessar o equipamento via Telnet: {str(e)}")

# Função para capturar o prompt inicial
def capturar_prompt(conexao, prompts, tempo_maximo):
    """
    Captura o prompt inicial até encontrar um dos prompts esperados ou estourar o tempo.
    """
    inicio = time.time()
    while True:
        if isinstance(conexao, paramiko.Channel) and conexao.recv_ready():
            mensagem_inicial = conexao.recv(4096).decode('utf-8')
            if any(mensagem_inicial.strip().endswith(p) for p in prompts):
                print("Prompt inicial capturado via SSH.")
                break
        elif isinstance(conexao, telnetlib.Telnet):
            mensagem_inicial = conexao.read_very_eager().decode('ascii')
            if any(mensagem_inicial.strip().endswith(p) for p in prompts):
                print("Prompt inicial capturado via Telnet.")
                break

        if time.time() - inicio > tempo_maximo:
            raise Exception("Tempo limite ao capturar a mensagem inicial.")
        time.sleep(1)

# Função para capturar a resposta do comando
def capturar_resposta(conexao, prompts, tempo_maximo):
    """
    Captura a resposta do comando até encontrar um dos prompts esperados ou estourar o tempo.
    """
    resposta = ""
    inicio = time.time()
    while True:
        if isinstance(conexao, paramiko.Channel) and conexao.recv_ready():
            resposta_parcial = conexao.recv(4096).decode('utf-8')
            resposta += resposta_parcial
            print(f"Resposta parcial capturada via SSH:\n{resposta_parcial}")

            if any(resposta_parcial.strip().endswith(p) for p in prompts):

                print("Comando concluído via SSH.")
                break
        elif isinstance(conexao, telnetlib.Telnet):
            resposta_parcial = conexao.read_very_eager().decode('ascii')
            resposta += resposta_parcial
            print(f"Resposta parcial capturada via Telnet:\n{resposta_parcial}")
            if any(resposta_parcial.strip().endswith(p) for p in prompts):
                print("Comando concluído via Telnet.")
                break

        if time.time() - inicio > tempo_maximo:
            raise Exception("Tempo limite excedido ao aguardar resposta do equipamento.")
        time.sleep(1)

    return resposta
