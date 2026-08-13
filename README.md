# Banco Ágil 🏦

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

- **Triagem** — porta de entrada: cumprimenta, autentica o cliente com CPF + data de nascimento, e identifica a necessidade para redirecionar.
- **Crédito** — consulta e solicitação de aumento de limite, checando o score do cliente contra as faixas permitidas, podendo redirecionar cliente para agente de entrevista de crédito caso o score não seja o suficiente no momento.
- **Entrevista de Crédito** — conduz uma entrevista financeira conversacional e recalcula o score do cliente.
- **Câmbio** — consulta de cotação de moedas em tempo real via API externa.

<img width="1785" height="1040" alt="image" src="https://github.com/user-attachments/assets/3239325f-3445-4886-a3da-8affc493d4bf" />

### Orquestração e dados

A primeira mensagem da conversa entra pela Triagem, que faz a autenticação e decide para qual agente passar a conversa; a partir da transferência, cada turno seguinte entra direto no agente que já está atendendo (`current_agent` no estado), sem reprocessar pela Triagem. Handoffs acontecem via `Command(graph=Command.PARENT)`, que transfere o controle para outro nó do grafo pai. O roteamento é de mão única: um especialista nunca devolve o atendimento para a Triagem, exceto o ciclo Crédito⇄Entrevista de Crédito, que é uma continuação direta e intencional do mesmo atendimento.

O estado da conversa (`GraphState`) é compartilhado entre todos os agentes, inclui o histórico de mensagens, o cliente autenticado, tentativas de autenticação e dados parciais capturados durante a conversa. A persistência entre mensagens de uma mesma sessão é feita via checkpointer em memória, indexado por um identificador de sessão.

O acesso aos dados (clientes, faixas de score, solicitações de aumento, log de erros) passa por uma camada de repositórios que isola a lógica de negócio do formato de armazenamento, tornando possível uma troca entre formato CSV e banco de dados relacional sem alterar as tools.

## Funcionalidades Implementadas

- **Validação de entrada nas tools** — tipos compartilhados (CPF, data, valores monetários, código de moeda) com regras de formato aplicadas antes da tool executar; entrada malformada vira erro tratável, não crash.
- **Tratamento de erro em duas categorias** — entrada inválida, que já retorna o problema para o agente antes de chamar a tool, dando para o agente uma secunda chance de fazer a requisição vs. erro de sistema que registra automaticamente o erro em um csv para análises e informa o agente, para que uma mensagem amigável informando que aconteceu um problema seja enviada, e se necessário(Quando o problema for câmbio por decisão de design), informando um outro modo de fazer a operação.
- **Normalização de dados em linguagem livre** — convertendo dados como datas por extenso, valores abreviados ("6k") e CPF com pontuação automaticamente para o formato pedido pelas tools.
- **Contagem de tentativas de autenticação** — controle de estado dedicado, com encerramento automático e amigável após a 3ª falha consecutiva.
- **Redirecionamento implícito entre agentes** — troca de contexto preservando os dados do cliente já autenticado, sem o cliente perceber a transição.
- **Resolução de escopo múltiplo** — quando o pedido mistura mais de um assunto, resolve a parte própria antes de escalar o resto, ou pergunta ao cliente qual prioridade em vez de decidir sozinho.
- **Otimização de custo de chamadas ao modelo** — histórico de mensagens limitado por tamanho, políticas de comportamento compartilhadas entre agentes em vez de duplicadas.
- **Persistência de conversa por sessão** — estado da conversa mantido por identificador de sessão.
- **Registro estruturado de erros técnicos** — falhas inesperadas gravadas em csv dedicado com timestamp, origem e tipo de exceção.
- **Recuperação automática de instabilidade do modelo de linguagem** — se o modelo principal falhar por limite de requisições ou demora excessiva, um modelo de backup assume a chamada automaticamente; se mesmo assim a resposta passar de 40 segundos no total, o atendimento informa uma instabilidade momentânea de forma amigável em vez de deixar o cliente esperando.

## Funcionalidades desativadas
- **Captura progressiva de dados** — mecanismo para registrar dados parciais no state conforme informados ao longo da conversa. Foi desativado por não ser necessário em um sistema com esse escopo, gerando gasto de tokens e aumento de tempo de resposta desnecessários, porém mantido para uso posterior caso o sistema ganhe escopo.
- **Tool de redirecionamento para agente de triagem** — Uma tools para redirecionar as requests para o agente de triagem, quando mensagens estivessem em contextos diferenntes de seus objetivos, possibilitando uma troca dinâmica entre agentes sem a necessidade de requests sempre passando pelo triagem economizando tokens e otimizando tempo de resposta, ou tools de decisão de redirecionamento para múltiplos agentes dentro dos proprios agentes especializados. Descontinuado por não estar dentro do escopo do sistema no momento, mas mantido caso o sistema necessite de troca dinâmica entre agentes.

## Desafios Enfrentados e Como Foram Resolvidos

- **Testes de modelos** - Realizando testes com múltiplos modelos free tyer para testes no sistema, escolhendo o gemini 3.5-flash como padrão por sua qualidade, tempo de resposta e compatibilidade com tools
- **Loop entre agente de crédito e entrevista** - O agente de entrevista e crédito estavam entrando em loop chamando um ao outro infinitamente, solucionado fazendo com que o agente de entrevista, só chame o créditonovamente ao fim da entrevista com Score calculado, passando esse contexto para o outro agente.
- **Segunda chance quando o erro da tool for do agente** - Quando realizando testes com modelos mais fracos, percebi que eles tinham dificuldade de formatar o input no formato da tool, mesmo com formatos detalhados. Solução: Implementação de segunda chance quando erro é input do agente, ao invez de rodar a tool retornando erro, uma validação de input veta inputs com formato errado antes de rodar a tool, retornando um feedback resumido para o agente sobre qual campo está errado e como deve ser formatado, dando uma nova tentativa de request sem que o usuário saiba de nada.

## Escolhas Técnicas e Justificativas

- **Crédito como único ponto de entrada para a Entrevista de Crédito** — a Triagem só direciona para Crédito ou Câmbio; pedidos de atualização/melhoria de score também vão para Crédito, que decide se aciona a Entrevista. Mantém a regra de que nenhum agente atua fora do próprio escopo, e evita que a Triagem precise conhecer o fluxo interno do ciclo Crédito⇄Entrevista.
- **Camada de repositórios** entre as tools e os arquivos CSV — isola a lógica de negócio do formato de armazenamento, facilitando uma futura migração para um banco de dados real.
- **Validação centralizada via tipos Pydantic compartilhados**, em vez de checagens manuais espalhadas pelas tools.
- **Tratamento de erro em duas categorias com registro técnico em CSV** — atende diretamente o requisito de informar o cliente com clareza, oferecer alternativa quando possível, e registrar o erro para análise posterior.
- **Front-end em React em vez de Streamlit** — optei por uma interface de chat dedicada em React para uma experiência mais próxima de um atendimento real.
- **AwesomeAPI para cotação de câmbio** — escolhida por não exigir chave de API/token reduzindo a chance de falhas ou incoerências em produção, pelo formato simples de requisição e resposta em JSON plano facilitanndo o parsing e pela velocidade de resposta observada nos testes.
- **Modelo de linguagem de backup com troca automática e prazo de 40s por requisição** — em vez de só reagir a um erro com uma mensagem, o sistema tenta um segundo modelo automaticamente antes de desistir e, se mesmo após chamar o backup o sistema não retornar uma resposta em 40 segundos, o trabalho é cancelado e uma mensagem automática é enviada ao usuário.

## Tutorial de Execução e Testes

### Pré-requisitos
- [Docker](https://www.docker.com/) e Docker Compose, **ou**
- Python 3.12+ e Node.js 20+ (para rodar back-end e front-end manualmente)
- Uma chave de API do [Google AI Studio](https://aistudio.google.com/apikey) para o Gemini (gratuita)
### Rodando os testes

  ```bash
  cd back-end
  pytest
```
A suíte roda automaticamente em cada pull request via GitHub Actions (.github/workflows/tests.yml).

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
