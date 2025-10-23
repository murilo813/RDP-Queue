## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](./LICENSE) para detalhes.

# RDPqueue

RDPqueue é um sistema cliente-servidor desenvolvido em Python para gerenciamento de filas de usuários, com painel de informações e registro de atividades.

## Funcionalidades

- Servidor que gerencia a fila em tempo real.
- Cliente que se conecta ao servidor para interagir com a fila.
- Interface gráfica com:
  - Status do servidor em tempo real.
  - Painel de informações do servidor (IP local, IP público, porta).
  - Painel de logs com registros de entradas e saídas.
- Sistema de logs detalhado mostrando usuário, IP, atividade e timestamp.
- Atualização automática da fila a cada segundo.
- Servidor web embutido com Flask para comunicação HTTP.

## Tecnologias utilizadas

- **Python**  
- **Tkinter** para GUI.  
- **Flask** para servidor HTTP leve e comunicação com o cliente.  

## Estrutura do projeto


```text
RDPqueue/
├── server.py          # Servidor principal (RDPqueue-server)
├── client.py          # Cliente de conexão (RDPqueue-client)
├── README.md          # Documentação do projeto
└── requirements.txt   # Dependências Python
```

## Como funciona

### Servidor (`RDPqueue-server`)
1. Inicializa a interface gráfica.
2. Inicia o servidor Flask em uma thread separada.
3. Mantém a fila em memória com atualização periódica.
4. Recebe requisições HTTP do cliente para entrar ou sair da fila.
5. Atualiza logs e status em tempo real na interface.

### Cliente (`RDPqueue-client`)
1. Envia requisições HTTP ao servidor para interagir com a fila.
2. Recebe posição na fila e status de vez.
3. Pode ser configurado para interagir com servidores em redes externas.

### Logs
- Cada ação registrada inclui:
  - Usuário
  - IP
  - Atividade (entrada/saída)
  - Data e hora
- Possibilidade de limpar logs.
