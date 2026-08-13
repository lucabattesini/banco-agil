# Banco Ágil

Sistema de atendimento ao cliente para um banco digital fictício, construído com múltiplos agentes de IA especializados (Triagem, Crédito, Entrevista de Crédito e Câmbio) orquestrados via LangGraph, com back-end em FastAPI e front-end em React.

## Visão Geral

O Banco Ágil simula um atendimento bancário completo conduzido por IA: o cliente conversa com um único "atendente" do início ao fim, mas por trás dessa conversa, diferentes agentes especializados assumem o controle conforme a necessidade identificada — autenticação, consulta e aumento de limite de crédito, reavaliação de score, e cotação de câmbio. A transição entre agentes é sempre invisível para o cliente.

## Arquitetura do Sistema

### Stack
- **Orquestração de agentes**: LangGraph
- **LLM**: Groq (modelos Llama/GPT-OSS via API compatível com OpenAI)
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

Um `StateGraph` pai registra os 4 agentes como nós; a entrada é decidida a cada turno por um roteador condicional que lê o estado (`current_agent`). Handoffs entre agentes acontecem via `Command(graph=Command.PARENT)`, que interrompe o subgrafo do agente atual e transfere o controle para outro nó do grafo pai, sempre passando pela Triagem quando o assunto sai do escopo do agente ativo (com exceção do ciclo Crédito⇄Entrevista de Crédito, que é direto e cíclico).

### Estado e dados

O estado da conversa (`GraphState`) é compartilhado entre todos os agentes — inclui o histórico de mensagens, o cliente autenticado, tentativas de autenticação e dados parciais capturados durante a conversa. A persistência entre mensagens de uma mesma sessão é feita via checkpointer em memória, indexado por um identificador de sessão.

O acesso aos dados (clientes, faixas de score, solicitações de aumento, log de erros) passa por uma camada de repositórios que isola a lógica de negócio do formato de armazenamento (hoje CSV, podendo ser trocado por um banco de dados real sem alterar as tools).

## Funcionalidades Implementadas

- **Validação de entrada nas tools** — tipos compartilhados (CPF, data, valores monetários, código de moeda) com regras de formato aplicadas antes da tool executar; entrada malformada vira erro tratável, não crash.
- **Tratamento de erro em duas categorias** — entrada inválida (corrige e tenta de novo, no máximo uma vez) vs. erro de sistema (desculpa ao cliente, sugere alternativa quando existe, registra em CSV para análise técnica) — nunca interrompe a conversa abruptamente.
- **Normalização de dados em linguagem livre** — datas por extenso, valores abreviados ("5k"), CPF com pontuação: convertidos automaticamente para o formato esperado, sem pedir ao cliente para reescrever.
- **Contagem de tentativas de autenticação** — controle de estado dedicado, com encerramento automático e amigável após a 3ª falha consecutiva.
- **Redirecionamento implícito entre agentes** — troca de contexto preservando os dados do cliente já autenticado, sem o cliente perceber a transição.
- **Guard contra loop de redirecionamento** — detecta quando o mesmo par de agentes fica se devolvendo a conversa repetidamente e interrompe o ciclo antes de esgotar tentativas.
- **Resolução de escopo múltiplo** — quando o pedido mistura mais de um assunto, resolve a parte própria antes de escalar o resto, ou pergunta ao cliente qual prioridade em vez de decidir sozinho.
- **Captura progressiva de dados, disponível mas desativada por padrão** — mecanismo para registrar dados parciais conforme informados ao longo da conversa (útil para fluxos longos ou modelos mais lentos); hoje trocado por captura direta (mais barato em chamadas ao modelo), mas o código permanece no projeto, pronto para reativar se necessário.
- **Otimização de custo de chamadas ao modelo** — histórico de mensagens limitado por tamanho, políticas de comportamento compartilhadas entre agentes em vez de duplicadas.
- **Persistência de conversa por sessão** — estado da conversa mantido por identificador de sessão, permitindo retomar o atendimento entre mensagens.
- **Camada de repositórios** — acesso aos CSVs isolado da lógica de negócio, facilitando troca futura por um banco de dados real.
- **Registro estruturado de erros técnicos** — falhas inesperadas gravadas com timestamp, origem e tipo de exceção, sem expor detalhes técnicos ao cliente.
- **Testes automatizados com execução em CI** — suíte cobrindo tools, validações e repositórios, rodando a cada pull request.
- **Execução via container** — todo o sistema (back-end + front-end) sobe com um único comando.
- **Recuperação automática de instabilidade do modelo de linguagem** — se o modelo principal falhar por limite de requisições ou demora excessiva, um modelo de backup assume a chamada automaticamente, sem o cliente perceber; se mesmo assim a resposta passar de 40 segundos no total, o atendimento informa uma instabilidade momentânea de forma amigável, em vez de deixar o cliente esperando indefinidamente ou ver um erro genérico.

## Desafios Enfrentados e Como Foram Resolvidos

**Condição de corrida em chamadas de tool paralelas.** Alguns modelos chamam várias tools na mesma resposta (ex.: capturar dado de autenticação, validar cliente e redirecionar, tudo de uma vez). Como o estado injetado em cada tool reflete o instante anterior ao lote inteiro, uma tool de redirecionamento podia "ver" o cliente ainda não autenticado mesmo que a validação tivesse acabado de acontecer na mesma resposta. Solução: as tools de redirecionamento passaram a rejeitar a chamada (erro de entrada inválida, tratável) se o cliente ainda não estiver autenticado no estado, em vez de assumir que a ordem de execução é confiável.

**Loop de redirecionamento entre agentes.** Um pedido envolvendo mais de um assunto ao mesmo tempo podia gerar um ciclo: um agente devolve para a Triagem, que redireciona de volta, que devolve de novo. Resolvido com um mecanismo que rastreia qual foi o último agente a devolver o atendimento e bloqueia uma segunda devolução consecutiva do mesmo agente, entregando a instrução de parar diretamente na mensagem de retorno da tool — sem exigir nenhuma mudança na Triagem.

**Limites de taxa de provedores de LLM.** O free tier do provedor inicial (Gemini) se mostrou insuficiente (20 requisições/dia) para o volume de chamadas de um sistema multi-agente com tool-calling extensivo. Migrado para Groq, que oferece um free tier maior — mas com seus próprios limites por minuto e por dia, o que motivou uma rodada de otimização: histórico de mensagens limitado, textos de política e descrições de tools enxutos, e remoção de capturas intermediárias que custavam uma chamada extra ao modelo a cada dado informado.

**Avaliação de modelos alternativos sob pressão de cota.** Três alternativas do mesmo provedor foram avaliadas na prática: uma apresentou um bug conhecido e documentado de formatação de tool-calling; outra, por ser um modelo bem menor, chegou a inventar dados de cliente para forçar uma chamada de tool. A escolha final priorizou o modelo com melhor aderência a schema de ferramentas, mesmo com cota diária mais restrita.

## Escolhas Técnicas e Justificativas

- **Entrada direta no agente atual, com uma tool de return_to_triage pra transitar entre agentes quando necessário** — os agentes especialistas têm uma tool pra devolver a conversa à Triagem sempre que o assunto sai do próprio escopo, tornando possível o cliente "viajar" entre Crédito, Entrevista e Câmbio ao longo da mesma conversa, sem que seja necessário dar tools de navegação direta para os agentes especializados, ou que as requisições sempre passem pelo orquestrador. Passar pelo orquestrador em toda chamada não é necessário num sistema deste porte e custaria uma chamada extra ao modelo gastando mais tokens e mais latência, mesmo quando não é necessário identificar contexto.
- **Redirecionamentos sempre passando pela Triagem** (exceto o ciclo Crédito⇄Entrevista) — mantém a regra de que nenhum agente atua fora do próprio escopo, e centraliza a decisão de roteamento em um único lugar.
- **Camada de repositórios** entre as tools e os arquivos CSV — isola a lógica de negócio do formato de armazenamento, facilitando uma futura migração para um banco de dados real.
- **Validação centralizada via tipos Pydantic compartilhados**, em vez de checagens manuais espalhadas pelas tools.
- **Tratamento de erro em duas categorias com registro técnico em CSV** — atende diretamente o requisito de informar o cliente com clareza, oferecer alternativa quando possível, e registrar o erro para análise posterior.
- **Captura progressiva de dados avaliada e desativada conscientemente**, mantendo o código-base disponível, porém desativada por decisão de custo, por cada captura intermediária custar uma chamada extra ao modelo, tornando inviável a implementação em um sistema usando modelos com cota free tyer.
- **Execução via Docker Compose com CI no GitHub Actions** — maior facilidade para rodar o projeto e verificação automática da suíte de testes a cada PR
- **Front-end em React em vez de Streamlit** — optei por uma interface de chat dedicada em React para uma experiência mais próxima de um atendimento real.
- **AwesomeAPI para cotação de câmbio** — escolhida por não exigir chave de API/token reduzindo a chance de falhas ou incoerências em produção, pelo formato simples de requisição e resposta em JSON plano facilitanndo o parsing e pela velocidade de resposta observada nos testes.
- **Modelo de linguagem de backup com troca automática e prazo de 40s por requisição** — em vez de só reagir a um erro com uma mensagem, o sistema tenta um segundo modelo automaticamente antes de desistir e, se mesmo após chamar o backup o sistema não retornar uma resposta em 40 segundos, o trabalho é cancelado e uma mensagem automática é enviada ao usuário.

## Tutorial de Execução e Testes

### Pré-requisitos
- [Docker](https://www.docker.com/) e Docker Compose, **ou**
- Python 3.12+ e Node.js 20+ (para rodar back-end e front-end manualmente)
- Uma chave de API do [Groq](https://console.groq.com/) (gratuita)

### Rodando com Docker

1. Copie os arquivos de exemplo de variáveis de ambiente e preencha com seus valores:
   ```bash
   cp back-end/.env.example back-end/.env
   cp front-end/.env.example front-end/.env
   ```
   Em `back-end/.env`, preencha `GROQ_API_KEY` com sua chave do Groq. `GROQ_MODEL` já vem com um valor recomendado (`llama-3.3-70b-versatile`).

2. Na raiz do repositório:
   ```bash
   docker compose up --build
   ```
3. Acesse a interface em `http://localhost:5173`. O back-end fica disponível em `http://localhost:8000` (`/docs` para a documentação interativa da API). Os dados de teste (`clientes.csv`, `score_limite.csv`) são gerados automaticamente no primeiro start.

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
| `back-end/.env` | `GROQ_API_KEY` | Chave de API do Groq |
| `back-end/.env` | `GROQ_MODEL` | Modelo principal usado pelos agentes (ex.: `llama-3.3-70b-versatile`) |
| `back-end/.env` | `GROQ_FALLBACK_MODEL` | Modelo acionado automaticamente se o principal falhar por limite de requisições ou timeout |
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
