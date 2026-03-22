# Workshop Agent

Template web para integrar um agente do Azure AI Foundry a uma interface de chat em Flask.

O projeto foi organizado para servir como base de demonstracao e tambem como ponto de partida para integracoes reais. A aplicacao abre uma conversa, envia mensagens para um workflow ou agente no Foundry, filtra respostas tecnicas ou de agentes auxiliares quando necessario e renderiza as respostas em bolhas separadas no chat.

## Visao Geral

- Backend em `Flask`
- Integracao com Azure AI Foundry via `azure-ai-projects`
- Frontend simples com HTML, CSS e JavaScript puro
- Configuracao centralizada em `.env`
- Filtro opcional de mensagens por agente e por padroes de texto
- Logging opcional do JSON bruto retornado pela API `responses`

## Estrutura

- `app.py`: rotas HTTP, sessao da conversa e renderizacao da interface
- `agent_service.py`: comunicacao com Azure AI Foundry e tratamento das respostas
- `config.py`: leitura e normalizacao das variaveis de ambiente
- `templates/index.html`: estrutura da interface
- `static/styles.css`: identidade visual do template
- `static/app.js`: envio de mensagens, reset do chat e renderizacao das bolhas
- `run_agent.py`: teste simples no terminal

## Fluxo Da Aplicacao

1. O usuario abre a pagina `/`.
2. O backend reseta a conversa anterior da sessao para evitar contexto residual.
3. Ao enviar uma mensagem, o frontend faz `POST /api/chat`.
4. O backend cria a conversa se ainda nao existir para a sessao atual.
5. O servico chama `openai_client.responses.create(...)` com a referencia do workflow.
6. O retorno JSON da API e analisado em `output[]`.
7. Apenas mensagens `assistant` relevantes sao mantidas.
8. Mensagens de agentes ocultos por configuracao sao removidas.
9. Cada mensagem final volta para o frontend em `replies`.
10. O frontend cria uma bolha para cada item recebido.

## Backend

### `app.py`

Responsavel por tres pontos principais:

- renderizar a pagina inicial
- receber mensagens do chat
- resetar a conversa atual

Rotas:

- `GET /`: limpa a conversa da sessao e entrega a interface
- `POST /api/chat`: envia a mensagem para o agente e retorna `reply` e `replies`
- `POST /api/reset`: remove a conversa atual

### `agent_service.py`

Centraliza a integracao com o Azure AI Foundry.

Principais responsabilidades:

- criar cliente com `AIProjectClient`
- criar e apagar conversas
- enviar mensagens ao workflow configurado
- registrar o JSON bruto da resposta quando habilitado
- extrair mensagens uteis do campo `output`
- filtrar mensagens por agente
- limpar prefixos como `TRUE` e `FALSE`

#### Extracao das respostas

O projeto nao depende apenas de `response.output_text`, porque workflows com multiplos agentes podem devolver mensagens em `output[]` com varios itens intermediarios. Por isso, o codigo percorre `output[]`, seleciona apenas itens:

- `type == "message"`
- `role == "assistant"`

Depois, cada texto e normalizado e devolvido como uma lista.

#### Filtro por agente

Se um agente auxiliar aparecer no JSON e voce nao quiser exibir sua mensagem no chat, basta usar:

```env
AGENT_HIDE_OUTPUT_AGENTS="Seguranca"
```

Para ocultar varios:

```env
AGENT_HIDE_OUTPUT_AGENTS="Seguranca,Classificador"
```

### `config.py`

Concentra a leitura do `.env` e evita espalhar `os.getenv(...)` pelo projeto.

Tambem resolve:

- fallback entre `AZURE_EXISTING_AGENT_ID` e `AZURE_WORKFLOW_NAME` + `AZURE_WORKFLOW_VERSION`
- leitura de booleanos
- leitura de listas separadas por virgula
- configuracao especifica por workflow para filtros do agente

## Frontend

### `templates/index.html`

Define a estrutura da pagina:

- painel lateral introdutorio
- cabecalho do chat
- lista de mensagens
- composer com textarea e botao de envio

Tambem injeta `window.chatConfig` com os rotulos e mensagens usados pelo JavaScript.

### `static/app.js`

Responsavel por:

- enviar mensagens ao backend
- adicionar bolha do usuario
- mostrar estado temporario de processamento
- substituir esse estado pelas respostas finais
- renderizar varias bolhas quando `replies` contem mais de uma mensagem
- resetar visualmente o chat

### `static/styles.css`

Implementa o visual do template:

- fundo com gradientes e glow
- paineis translucidos
- tipografia forte para hero e cabecalho
- animacoes suaves de entrada
- responsividade para desktop e mobile

## Variaveis De Ambiente

Exemplo completo em `.env.example`.

### Azure

- `AZURE_AI_PROJECT_ENDPOINT`: endpoint do projeto no Azure AI Foundry
- `AZURE_WORKFLOW_NAME`: nome do workflow ou agente
- `AZURE_WORKFLOW_VERSION`: versao do workflow ou agente
- `AZURE_EXISTING_AGENT_ID`: alternativa em formato `nome:versao`

### App

- `APP_HOST`: host do Flask
- `APP_PORT`: porta do Flask
- `APP_SECRET_KEY`: chave da sessao Flask

### UI

- `CHAT_TITLE`: titulo principal do template
- `CHAT_BADGE`: badge visual no painel lateral
- `CHAT_SUBTITLE`: texto introdutorio
- `CHAT_WELCOME`: mensagem inicial da assistente
- `CHAT_INPUT_PLACEHOLDER`: placeholder do campo de mensagem
- `CHAT_SHOW_WELCOME`: exibe ou nao a mensagem inicial
- `CHAT_PANEL_LABEL`: label superior da interface
- `CHAT_PANEL_TITLE`: titulo da area de conversa
- `CHAT_ASSISTANT_LABEL`: nome mostrado nas mensagens do agente
- `CHAT_USER_LABEL`: nome mostrado nas mensagens do usuario
- `CHAT_PENDING_MESSAGE`: texto temporario enquanto a resposta esta sendo processada

### Filtros E Logs

- `AGENT_HIDE_VALIDATION_MESSAGES`: remove linhas tecnicas de validacao
- `AGENT_HIDE_PATTERNS`: remove linhas por regex
- `AGENT_HIDE_OUTPUT_AGENTS`: esconde mensagens de agentes especificos
- `AGENT_LOG_RESPONSES`: loga a lista final de respostas exibidas
- `AGENT_LOG_RESPONSE_JSON`: loga o JSON bruto retornado pela API

## Como Executar

Instale as dependencias:

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

## Teste Rapido No Terminal

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

### Ocultar respostas tecnicas

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

## Observacoes

- O projeto usa sessao Flask para manter o `conversation_id`.
- Ao abrir a pagina, a conversa anterior e resetada para evitar herdar contexto antigo.
- O retorno do workflow pode conter acoes, mensagens e chamadas de ferramentas. O frontend exibe apenas as mensagens finais filtradas.

## Verificacao

Validacao local usada neste template:

```bash
python -m py_compile app.py agent_service.py config.py run_agent.py
```
