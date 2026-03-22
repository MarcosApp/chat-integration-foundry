# Workshop Agent

Template web para integrar um agente do Azure AI Foundry a uma interface de chat em Flask.

O projeto foi organizado para servir como base de demonstração e também como ponto de partida para integrações reais. A aplicação abre uma conversa, envia mensagens para um workflow/agente no Foundry, filtra respostas técnicas ou de agentes auxiliares quando necessário e renderiza as respostas em bolhas separadas no chat.

## Visão Geral

- Backend em `Flask`
- Integração com Azure AI Foundry via `azure-ai-projects`
- Frontend simples com HTML, CSS e JavaScript puro
- Configuração centralizada em `.env`
- Filtro opcional de mensagens por agente e por padrões de texto
- Logging opcional do JSON bruto retornado pela API `responses`

## Estrutura

- [app.py](/e:/ProjetosPython/Conviva-Bot/azuredev-5b47/app.py): rotas HTTP, sessão da conversa e renderização da interface
- [agent_service.py](/e:/ProjetosPython/Conviva-Bot/azuredev-5b47/agent_service.py): comunicação com Azure AI Foundry e tratamento das respostas
- [config.py](/e:/ProjetosPython/Conviva-Bot/azuredev-5b47/config.py): leitura e normalização das variáveis de ambiente
- [templates/index.html](/e:/ProjetosPython/Conviva-Bot/azuredev-5b47/templates/index.html): estrutura da interface
- [static/styles.css](/e:/ProjetosPython/Conviva-Bot/azuredev-5b47/static/styles.css): identidade visual do template
- [static/app.js](/e:/ProjetosPython/Conviva-Bot/azuredev-5b47/static/app.js): envio de mensagens, reset do chat e renderização das bolhas
- [run_agent.py](/e:/ProjetosPython/Conviva-Bot/azuredev-5b47/run_agent.py): teste simples no terminal

## Fluxo Da Aplicação

1. O usuário abre a página `/`.
2. O backend reseta a conversa anterior da sessão para evitar contexto residual.
3. Ao enviar uma mensagem, o frontend faz `POST /api/chat`.
4. O backend cria a conversa se ainda não existir para a sessão atual.
5. O serviço chama `openai_client.responses.create(...)` com a referência do workflow.
6. O retorno JSON da API é analisado em `output[]`.
7. Apenas mensagens `assistant` relevantes são mantidas.
8. Mensagens de agentes ocultos por configuração são removidas.
9. Cada mensagem final volta para o frontend em `replies`.
10. O frontend cria uma bolha para cada item recebido.

## Backend

### `app.py`

Responsável por três pontos principais:

- renderizar a página inicial
- receber mensagens do chat
- resetar a conversa atual

Rotas:

- `GET /`: limpa a conversa da sessão e entrega a interface
- `POST /api/chat`: envia a mensagem para o agente e retorna `reply` e `replies`
- `POST /api/reset`: remove a conversa atual

### `agent_service.py`

Centraliza a integração com o Azure AI Foundry.

Principais responsabilidades:

- criar cliente com `AIProjectClient`
- criar e apagar conversas
- enviar mensagens ao workflow configurado
- registrar o JSON bruto da resposta quando habilitado
- extrair mensagens úteis do campo `output`
- filtrar mensagens por agente
- limpar prefixos como `TRUE` e `FALSE`

#### Extração das respostas

O projeto não depende apenas de `response.output_text`, porque workflows com múltiplos agentes podem devolver mensagens em `output[]` com vários itens intermediários. Por isso, o código percorre `output[]`, seleciona apenas itens:

- `type == "message"`
- `role == "assistant"`

Depois, cada texto é normalizado e devolvido como uma lista.

#### Filtro por agente

Se um agente auxiliar aparecer no JSON e você não quiser exibir sua mensagem no chat, basta usar:

```env
AGENT_HIDE_OUTPUT_AGENTS="Seguranca"
```

Para ocultar vários:

```env
AGENT_HIDE_OUTPUT_AGENTS="Seguranca,Classificador"
```

### `config.py`

Concentra a leitura do `.env` e evita espalhar `os.getenv(...)` pelo projeto.

Também resolve:

- fallback entre `AZURE_EXISTING_AGENT_ID` e `AZURE_WORKFLOW_NAME` + `AZURE_WORKFLOW_VERSION`
- leitura de booleanos
- leitura de listas separadas por vírgula
- configuração específica por workflow para filtros do agente

## Frontend

### `templates/index.html`

Define a estrutura da página:

- painel lateral introdutório
- cabeçalho do chat
- lista de mensagens
- composer com textarea e botão de envio

Também injeta `window.chatConfig` com os rótulos e mensagens usados pelo JavaScript.

### `static/app.js`

Responsável por:

- enviar mensagens ao backend
- adicionar bolha do usuário
- mostrar estado temporário de processamento
- substituir esse estado pelas respostas finais
- renderizar várias bolhas quando `replies` contém mais de uma mensagem
- resetar visualmente o chat

### `static/styles.css`

Implementa o visual do template:

- fundo com gradientes e glow
- painéis translúcidos
- tipografia forte para hero e cabeçalho
- animações suaves de entrada
- responsividade para desktop e mobile

## Variáveis De Ambiente

Exemplo completo em [.env.example](/e:/ProjetosPython/Conviva-Bot/azuredev-5b47/.env.example).

### Azure

- `AZURE_AI_PROJECT_ENDPOINT`: endpoint do projeto no Azure AI Foundry
- `AZURE_WORKFLOW_NAME`: nome do workflow/agente
- `AZURE_WORKFLOW_VERSION`: versão do workflow/agente
- `AZURE_EXISTING_AGENT_ID`: alternativa em formato `nome:versao`

### App

- `APP_HOST`: host do Flask
- `APP_PORT`: porta do Flask
- `APP_SECRET_KEY`: chave da sessão Flask

### UI

- `CHAT_TITLE`: título principal do template
- `CHAT_BADGE`: badge visual no painel lateral
- `CHAT_SUBTITLE`: texto introdutório
- `CHAT_WELCOME`: mensagem inicial da assistente
- `CHAT_INPUT_PLACEHOLDER`: placeholder do campo de mensagem
- `CHAT_SHOW_WELCOME`: exibe ou não a mensagem inicial
- `CHAT_PANEL_LABEL`: label superior da interface
- `CHAT_PANEL_TITLE`: título da área de conversa
- `CHAT_ASSISTANT_LABEL`: nome mostrado nas mensagens do agente
- `CHAT_USER_LABEL`: nome mostrado nas mensagens do usuário
- `CHAT_PENDING_MESSAGE`: texto temporário enquanto a resposta está sendo processada

### Filtros E Logs

- `AGENT_HIDE_VALIDATION_MESSAGES`: remove linhas técnicas de validação
- `AGENT_HIDE_PATTERNS`: remove linhas por regex
- `AGENT_HIDE_OUTPUT_AGENTS`: esconde mensagens de agentes específicos
- `AGENT_LOG_RESPONSES`: loga a lista final de respostas exibidas
- `AGENT_LOG_RESPONSE_JSON`: loga o JSON bruto retornado pela API

## Como Executar

Instale as dependências:

```bash
pip install -r requirements.txt
```

Copie e ajuste o ambiente:

```bash
copy .env.example .env
```

Inicie o app:

```bash
python app.py
```

Abra no navegador:

```text
http://127.0.0.1:8000
```

## Teste Rápido No Terminal

```bash
python run_agent.py
```

## Como Personalizar

### Trocar identidade visual

Altere:

- `CHAT_TITLE`
- `CHAT_BADGE`
- `CHAT_SUBTITLE`
- `CHAT_WELCOME`

### Ocultar respostas técnicas

Use:

```env
AGENT_HIDE_VALIDATION_MESSAGES="true"
AGENT_HIDE_PATTERNS=""
```

### Ocultar agentes auxiliares

Use:

```env
AGENT_HIDE_OUTPUT_AGENTS="Seguranca"
```

## Observações

- O projeto usa sessão Flask para manter o `conversation_id`.
- Ao abrir a página, a conversa anterior é resetada para evitar herdar contexto antigo.
- O retorno do workflow pode conter ações, mensagens e chamadas de ferramentas. O frontend exibe apenas as mensagens finais filtradas.

## Verificação

Validação local usada neste template:

```bash
python -m py_compile app.py agent_service.py config.py run_agent.py
```
