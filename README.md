# Banco Ágil

Sistema de atendimento ao cliente para um banco digital fictício, construído com múltiplos agentes de IA especializados (Triagem, Crédito, Entrevista de Crédito e Câmbio) orquestrados via LangGraph, com back-end em FastAPI e front-end em React.

## Visão Geral

O Banco Ágil simula um atendimento bancário completo conduzido por IA: o cliente conversa com um único "atendente" do início ao fim, mas por trás dessa conversa, diferentes agentes especializados assumem o controle conforme a necessidade identificada — autenticação, consulta e aumento de limite de crédito, reavaliação de score, e cotação de câmbio. A transição entre agentes é sempre invisível para o cliente.

## Arquitetura do Sistema

### Stack
- **Orquestração de agentes**: LangGraph
- **LLM**: Google Gemini
- **Back-end**: FastAPI
- **Front-end**: React + TypeScript + Vite
- **Dados**: arquivos CSV (sem banco de dados relacional), acessados por uma camada de repositórios
- **Testes**: pytest
- **CI**: GitHub Actions
- **Execução**: Docker Compose

### Os quatro agentes

Cada agente é um subgrafo independente (`create_react_agent`), com seu próprio conjunto de tools e prompt de sistema, mas todos compartilham o mesmo tom e persona — o cliente nunca percebe qual agente está "atrás" da resposta.

- **Triagem** — porta de entrada: cumprimenta, autentica o cliente (CPF + data de nascimento contra `clientes.csv`) e identifica a necessidade para redirecionar.
- **Crédito** — consulta e solicitação de aumento de limite, checando o score do cliente contra as faixas permitidas.
- **Entrevista de Crédito** — conduz uma entrevista financeira conversacional e recalcula o score do cliente.
- **Câmbio** — consulta de cotação de moedas em tempo real via API externa.

### Orquestração e handoffs

Um `StateGraph` pai registra os 4 agentes como nós, com uma entrada condicional: a primeira mensagem da conversa entra pela Triagem; a partir do handoff, cada turno seguinte entra direto no agente que já está atendendo (`current_agent` no estado), sem reprocessar pela Triagem. Handoffs acontecem via `Command(graph=Command.PARENT)`, que transfere o controle para outro nó do grafo pai. O roteamento é de mão única: um especialista nunca devolve o atendimento para a Triagem, exceto o ciclo Crédito⇄Entrevista de Crédito, que é uma continuação direta e intencional do mesmo atendimento (não uma correção de rota).

### Estado e dados

O estado da conversa (`GraphState`) é compartilhado entre todos os agentes — inclui o histórico de mensagens, o cliente autenticado, tentativas de autenticação e dados parciais capturados durante a conversa. A persistência entre mensagens de uma mesma sessão é feita via checkpointer em memória, indexado por um identificador de sessão.

O acesso aos dados (clientes, faixas de score, solicitações de aumento, log de erros) passa por uma camada de repositórios que isola a lógica de negócio do formato de armazenamento (hoje CSV, podendo ser trocado por um banco de dados real sem alterar as tools).

## Funcionalidades Implementadas

- **Validação de entrada nas tools** — tipos compartilhados (CPF, data, valores monetários, código de moeda) com regras de formato aplicadas antes da tool executar; entrada malformada vira erro tratável, não crash.
- **Tratamento de erro em duas categorias** — entrada inválida (corrige e tenta de novo, no máximo uma vez) vs. erro de sistema (desculpa ao cliente, sugere alternativa quando existe, registra em CSV para análise técnica) — nunca interrompe a conversa abruptamente.
- **Normalização de dados em linguagem livre** — datas por extenso, valores abreviados ("5k"), CPF com pontuação: convertidos automaticamente para o formato esperado, sem pedir ao cliente para reescrever.
- **Contagem de tentativas de autenticação** — controle de estado dedicado, com encerramento automático e amigável após a 3ª falha consecutiva.
- **Redirecionamento implícito entre agentes** — troca de contexto preservando os dados do cliente já autenticado, sem o cliente perceber a transição.
- **Teto estrutural contra loop de redirecionamento** — o roteamento é de mão única: a Triagem decide para qual especialista enviar a conversa, mas nenhum especialista tem como devolvê-la (com exceção do ciclo intencional Crédito⇄Entrevista, que tem seu próprio limite de saltos). Sem um caminho de volta, não existe estado do grafo em que um redirecionamento possa se repetir indefinidamente — o teto é estrutural, não depende do modelo "decidir" parar.
- **Resolução de escopo múltiplo** — quando o pedido mistura mais de um assunto, resolve a parte própria antes de escalar o resto, ou pergunta ao cliente qual prioridade em vez de decidir sozinho.
- **Captura progressiva de dados, disponível mas desativada por padrão** — mecanismo para registrar dados parciais conforme informados ao longo da conversa (útil para fluxos longos ou modelos mais lentos); hoje trocado por captura direta (mais barato em chamadas ao modelo), mas o código permanece no projeto, pronto para reativar se necessário.
- **Redirecionamento direto entre especialista e Triagem, implementado mas não oferecido a nenhum agente** — a tool `return_to_triage` permanece implementada e testada, mas nenhum agente a recebe: o roteamento é de mão única por design (ver Desafios Enfrentados). Fica pronta para uma futura revisão que queira reabrir esse caminho, desde que a lógica de `last_bounced_agent` seja reverificada contra loops de redirecionamento antes de ligá-la a algum agente.
- **Otimização de custo de chamadas ao modelo** — histórico de mensagens limitado por tamanho, políticas de comportamento compartilhadas entre agentes em vez de duplicadas.
- **Persistência de conversa por sessão** — estado da conversa mantido por identificador de sessão, permitindo retomar o atendimento entre mensagens.
- **Registro estruturado de erros técnicos** — falhas inesperadas gravadas com timestamp, origem e tipo de exceção, sem expor detalhes técnicos ao cliente.
- **Recuperação automática de instabilidade do modelo de linguagem** — se o modelo principal falhar por limite de requisições ou demora excessiva, um modelo de backup assume a chamada automaticamente, sem o cliente perceber; se mesmo assim a resposta passar de 40 segundos no total, o atendimento informa uma instabilidade momentânea de forma amigável, em vez de deixar o cliente esperando indefinidamente ou ver um erro genérico.

## Desafios Enfrentados e Como Foram Resolvidos

**Condição de corrida em chamadas de tool paralelas.** Alguns modelos chamam várias tools na mesma resposta (ex.: capturar dado de autenticação, validar cliente e redirecionar, tudo de uma vez). Como o estado injetado em cada tool reflete o instante anterior ao lote inteiro, uma tool de redirecionamento podia "ver" o cliente ainda não autenticado mesmo que a validação tivesse acabado de acontecer na mesma resposta. Solução: as tools de redirecionamento passaram a rejeitar a chamada (erro de entrada inválida, tratável) se o cliente ainda não estiver autenticado no estado, em vez de assumir que a ordem de execução é confiável.

**Loop de redirecionamento entre agentes.** Um pedido envolvendo mais de um assunto ao mesmo tempo podia gerar um ciclo: um agente devolve para a Triagem, que redireciona de volta, que devolve de novo. A primeira tentativa de correção rastreava qual foi o último agente a devolver o atendimento e bloqueava uma segunda devolução consecutiva do mesmo agente. Na prática, essa mensagem de bloqueio era endereçada a quem chamou a tool de devolução ("explique você ao cliente"), mas quem processava a mensagem em seguida era sempre a Triagem — o aviso nunca chegava a quem deveria agir nele, e o ciclo podia continuar até estourar o tempo limite da requisição. Uma correção intermediária trocou o mecanismo de bloqueio por uma mudança de arquitetura: toda mensagem passava pela Triagem primeiro, sempre, e os especialistas perdiam a tool de devolução direta — eliminava o loop, mas ao custo de uma chamada extra ao modelo por turno, mesmo quando o atendimento já tinha um especialista definido havia várias mensagens. A correção definitiva ataca a causa raiz em vez de contornar o sintoma: a tool de devolução (`return_to_triage`) simplesmente não é oferecida a nenhum especialista, então não existe caminho de volta para a Triagem no grafo — o roteamento é de mão única (Triagem → especialista, mais o ciclo intencional Crédito⇄Entrevista). Sem esse caminho, o ciclo é impossível por construção, e turnos seguintes de um atendimento já em andamento entram direto no especialista responsável, sem reprocessar pela Triagem.

**Limites de taxa de provedores de LLM.** O free tier do Gemini se mostrou insuficiente (20 requisições/dia) para o volume de chamadas de um sistema multi-agente com tool-calling extensivo, o que motivou uma rodada de otimização independente do provedor: histórico de mensagens limitado, textos de política e descrições de tools enxutos, e remoção de capturas intermediárias que custavam uma chamada extra ao modelo a cada dado informado. Combinada ao mecanismo de fallback automático entre dois modelos (`gemini-3.5-flash` como principal, `gemini-3.5-flash-lite` como backup), essa otimização absorve picos de uso sem exigir troca de provedor.

**Avaliação de modelos alternativos sob pressão de cota.** Diferentes modelos foram avaliados na prática ao longo do projeto: alguns apresentaram bugs conhecidos e documentados de formatação de tool-calling; outros, por serem modelos bem menores, chegaram a inventar dados de cliente para forçar uma chamada de tool. A escolha final priorizou os modelos com melhor aderência a schema de ferramentas.

## Escolhas Técnicas e Justificativas

- **Roteamento de mão única, sem devolução à Triagem** — a Triagem decide o agente de destino uma vez, e turnos seguintes de um atendimento já em andamento entram direto nesse agente, sem reprocessar pela Triagem a cada mensagem. Uma primeira tentativa fazia o caminho inverso (especialistas devolvendo a conversa pra Triagem quando o assunto saía do escopo deles, com a Triagem podendo ser pulada em turnos seguintes) e se mostrou frágil — abriu espaço pra loops de redirecionamento não determinísticos. A correção definitiva foi estrutural, não de prompt: sem nenhuma tool de devolução oferecida a nenhum especialista, não existe caminho de volta no grafo, então o loop é impossível por construção, e o custo de uma chamada extra ao modelo por turno (só pra redecidir um roteamento que não mudou) deixa de existir.
- **Crédito como único ponto de entrada para a Entrevista de Crédito** — a Triagem só direciona para Crédito ou Câmbio; pedidos de atualização/melhoria de score também vão para Crédito, que decide se aciona a Entrevista. Mantém a regra de que nenhum agente atua fora do próprio escopo, e evita que a Triagem precise conhecer o fluxo interno do ciclo Crédito⇄Entrevista.
- **Camada de repositórios** entre as tools e os arquivos CSV — isola a lógica de negócio do formato de armazenamento, facilitando uma futura migração para um banco de dados real.
- **Validação centralizada via tipos Pydantic compartilhados**, em vez de checagens manuais espalhadas pelas tools.
- **Tratamento de erro em duas categorias com registro técnico em CSV** — atende diretamente o requisito de informar o cliente com clareza, oferecer alternativa quando possível, e registrar o erro para análise posterior.
- **Captura progressiva de dados avaliada e desativada conscientemente**, mantendo o código-base disponível, porém desativada por decisão de custo, por cada captura intermediária custar uma chamada extra ao modelo, tornando inviável a implementação em um sistema usando modelos com cota free tyer.
- **Front-end em React em vez de Streamlit** — optei por uma interface de chat dedicada em React para uma experiência mais próxima de um atendimento real.
- **AwesomeAPI para cotação de câmbio** — escolhida por não exigir chave de API/token reduzindo a chance de falhas ou incoerências em produção, pelo formato simples de requisição e resposta em JSON plano facilitanndo o parsing e pela velocidade de resposta observada nos testes.
- **Modelo de linguagem de backup com troca automática e prazo de 40s por requisição** — em vez de só reagir a um erro com uma mensagem, o sistema tenta um segundo modelo automaticamente antes de desistir e, se mesmo após chamar o backup o sistema não retornar uma resposta em 40 segundos, o trabalho é cancelado e uma mensagem automática é enviada ao usuário.

## Tutorial de Execução e Testes

### Pré-requisitos
- [Docker](https://www.docker.com/) e Docker Compose, **ou**
- Python 3.12+ e Node.js 20+ (para rodar back-end e front-end manualmente)
- Uma chave de API do [Google AI Studio](https://aistudio.google.com/apikey) para o Gemini (gratuita)

### Rodando com Docker

1. Copie os arquivos de exemplo de variáveis de ambiente e preencha com seus valores:
   ```bash
   cp back-end/.env.example back-end/.env
   cp front-end/.env.example front-end/.env
   ```
   Em `back-end/.env`, preencha `GEMINI_API_KEY` com sua chave do Gemini. `GEMINI_MODEL`, `GEMINI_FALLBACK_MODEL`, `FRONTEND_URL` (em `back-end/.env`) e `VITE_API_URL` (em `front-end/.env`) já vêm com valores padrão compatíveis com o `docker-compose.yml` (`http://localhost:5173` e `http://localhost:8000`) — só precisam ser alterados se essas portas já estiverem em uso na sua máquina (veja [Portas já em uso](#portas-já-em-uso-8000--5173) abaixo).

2. Na raiz do repositório:
   ```bash
   docker compose up --build
   ```
3. Acesse a interface em `http://localhost:5173`. O back-end fica disponível em `http://localhost:8000` (`/docs` para a documentação interativa da API). Os dados de teste (`clientes.csv`, `score_limite.csv`) são gerados automaticamente no primeiro start.

#### Portas já em uso (8000 / 5173)

Se uma dessas portas já estiver ocupada na sua máquina, informe `BACKEND_PORT` e/ou `FRONTEND_PORT` na hora de subir os containers:
```bash
BACKEND_PORT=8080 FRONTEND_PORT=5174 docker compose up --build
```
O `docker-compose.yml` propaga a mudança para tudo que depende da porta (mapeamento de porta, `VITE_API_URL` do front-end e `FRONTEND_URL`/CORS do back-end) — não precisa editar mais nada nem criar arquivo novo.

### Rodando manualmente (desenvolvimento)

**Back-end:**
```bash
cd back-end
pip install -r requirements.txt
python -m db.seed_data     # gera os CSVs de teste
uvicorn app.main:app --reload
```

**Front-end**:
```bash
cd front-end
npm install
npm run dev
```

### Variáveis de ambiente

| Arquivo | Variável | Descrição |
|---|---|---|
| `back-end/.env` | `GEMINI_API_KEY` | Chave de API do Gemini |
| `back-end/.env` | `GEMINI_MODEL` | Modelo principal usado pelos agentes (ex.: `gemini-3.5-flash`) |
| `back-end/.env` | `GEMINI_FALLBACK_MODEL` | Modelo acionado automaticamente se o principal falhar por limite de requisições ou timeout (ex.: `gemini-3.5-flash-lite`) |
| `back-end/.env` | `FRONTEND_URL` | Origem permitida no CORS (ex.: `http://localhost:5173`) |
| `front-end/.env` | `VITE_API_URL` | URL do back-end (ex.: `http://localhost:8000`) |

### Rodando os testes

```bash
cd back-end
pytest
```

A suíte roda automaticamente em cada pull request via GitHub Actions (`.github/workflows/tests.yml`), sem necessidade de chave de API real — os testes exercitam as tools e validações diretamente, isolando o acesso a dados.

### Clientes de teste

Para testar o atendimento manualmente, use um dos clientes já cadastrados nos dados de exemplo:

| CPF | Data de nascimento | Score | Limite atual |
|---|---|---|---|
| 11111111111 | 1990-05-12 | 750 | R$ 5.000,00 |
| 22222222222 | 1985-11-30 | 420 | R$ 1.500,00 |
| 33333333333 | 1998-02-20 | 900 | R$ 12.000,00 |
| 44444444444 | 1975-07-08 | 150 | R$ 500,00 |
| 55555555555 | 2000-09-15 | 600 | R$ 3.000,00 |
