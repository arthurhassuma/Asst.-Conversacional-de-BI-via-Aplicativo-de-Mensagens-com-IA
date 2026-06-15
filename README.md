# Assistente Conversacional de BI via Aplicativo de Mensagens com Agentes de IA

> Pergunte ao banco de dados da sua empresa em português, por um aplicativo de mensagens, e receba a resposta em segundos — sem dashboards, sem SQL.

Projeto de portfólio do **PAC Extensionista** do curso de Engenharia de Software do Centro Universitário Católica de Santa Catarina (Jaraguá do Sul, SC), desenvolvido em parceria com a **Galvitech**, empresa de desenvolvimento de software sob medida para clientes B2B.

**Autor:** Arthur Hassuma · [arthur.hassuma@catolicasc.edu.br](mailto:arthur.hassuma@catolicasc.edu.br)

---

## Sobre o projeto

Gestores de empresas de serviços B2B dependem de analistas de dados ou de acesso manual a dashboards para obter informações estratégicas. Esse processo introduz latência na tomada de decisão, cria gargalo nas equipes técnicas e impede que perfis não técnicos acessem os dados de que precisam de forma autônoma — sobretudo fora do horário comercial.

Este projeto propõe um **agente conversacional de Business Intelligence** acessível por um aplicativo de mensagens. O sistema utiliza um agente de IA baseado em *Large Language Models* (LLMs) com **function calling** e a técnica **Text-to-SQL**: interpreta perguntas em linguagem natural, gera a consulta SQL correspondente, executa-a sobre o banco de dados e devolve a resposta humanizada em português.

### Pergunta de pesquisa

> Em que medida um agente de IA conversacional, integrado a um aplicativo de mensagens e baseado em LLMs com *function calling* e Text-to-SQL, é capaz de fornecer respostas precisas e compreensíveis sobre indicadores de BI a gestores não técnicos, reduzindo o tempo de acesso à informação frente ao uso de dashboards convencionais?

### Hipótese

Um agente com LLM, equipado com ferramentas de consulta ao banco via *function calling* e instruído com o esquema e o vocabulário do domínio B2B, atingirá **execution accuracy superior a 70%** e **tempo de resposta inferior ao acesso manual a dashboards**.

---

## Como funciona

```
Pergunta no          LLM             Text-to-SQL         Executa          Resposta
 mensageiro    ->   interpreta   ->   gera a query   ->  no banco    ->  em português
```

O gestor escreve uma pergunta como *"Qual foi o faturamento desta semana?"*. O agente a interpreta, gera o SQL, executa no PostgreSQL e devolve a resposta em linguagem natural — em segundos.

---

## Arquitetura

A solução adota uma arquitetura em **quatro camadas** com comunicação via **API RESTful**:

| Camada | Responsabilidade | Tecnologia |
|--------|------------------|------------|
| **Interface** | Recebe a mensagem do gestor via *webhook* (HTTP POST) e devolve a resposta | Telegram Bot API + `python-telegram-bot` |
| **Backend** | Orquestra o fluxo e expõe o *endpoint* REST | Python + FastAPI |
| **Agente** | LLM com *function calling* (`get_schema`, `execute_sql`) | Anthropic API (Claude) ou OpenAI API (GPT-4o) |
| **Dados** | Consultas somente leitura sobre dados sintéticos | PostgreSQL + `psycopg` |

### Fluxo de uma consulta

1. O gestor envia a mensagem; a Telegram Bot API a encaminha ao backend via `POST /webhook`.
2. O backend (FastAPI) valida o *payload* e aciona o agente.
3. O agente envia a pergunta ao LLM (`POST /v1/messages`), que decide invocar `get_schema` e depois `execute_sql` via *function calling*.
4. As ferramentas consultam o PostgreSQL (driver `psycopg`), com consultas restritas a `SELECT`.
5. A resposta volta ao backend, que a entrega ao gestor via `POST /sendMessage`.

---

## Segurança e integridade dos dados

- **Somente leitura:** apenas comandos `SELECT` são aceitos, validados na aplicação e reforçados por um usuário de banco com permissão mínima (`GRANT SELECT`) — duas barreiras independentes.
- **Timeout e limite de linhas:** protege contra consultas pesadas e preserva a disponibilidade.
- **Integridade da resposta:** o número sempre vem do banco, nunca é gerado/alucinação pelo LLM — a resposta é rastreável até a query executada.
- **Privacidade por design:** a base é inteiramente sintética, sem dados reais de clientes, eliminando riscos de LGPD durante o desenvolvimento.

---

## Inovação

Levantamento de 3 artigos científicos e 3 softwares de mercado identificou **três diferenciais exclusivos** desta proposta:

1. **Canal de mensagens como interface primária** — nenhum trabalho analisado entrega BI por um aplicativo de mensagens; todos usam interface web ou desktop.
2. **Foco no português brasileiro** — os sistemas existentes são projetados para o inglês; aqui o PT-BR é requisito primário.
3. **Dados sintéticos** — estratégia explícita de privacidade e reprodutibilidade, não adotada pelos trabalhos relacionados.

### Comparativo

| Ponto-chave | A1 | A2 | A3 | S1 | S2 | S3 | **Proposta** |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Text-to-SQL com LLM | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Agente autônomo (function calling) | ◐ | ✅ | ✅ | ✅ | ◐ | ❌ | ✅ |
| Respostas em linguagem natural | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Foco em usuários não técnicos | ✅ | ✅ | ◐ | ✅ | ✅ | ✅ | ✅ |
| **Integração com app de mensagens** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Suporte ao português brasileiro** | ❌ | ❌ | ❌ | ◐ | ❌ | ❌ | ✅ |
| **Dados sintéticos / privacidade** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Avaliação (execution accuracy) | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Domínio B2B / indicadores operacionais | ❌ | ◐ | ❌ | ◐ | ◐ | ◐ | ✅ |
| Implantação leve (solo dev) | ❌ | ❌ | ❌ | ◐ | ◐ | ✅ | ✅ |
| Fine-tuning do modelo | ❌ | ◐ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Geração de gráficos | ❌ | ◐ | ❌ | ✅ | ✅ | ✅ | ❌ |

✅ atende · ◐ parcial · ❌ não atende
**A1–A3:** artigos científicos · **S1–S3:** softwares (DB-GPT, WrenAI, Chat2DB)

A proposta atende **9 dos 12 critérios**. Os dois não atendidos (fine-tuning e geração de gráficos) são decisões conscientes de escopo e integram a agenda de trabalhos futuros.

---

## Resultados esperados

- **Execution accuracy > 70%** sobre 30–50 perguntas de validação em português.
- **Tempo de resposta < 10s** ponta a ponta.
- **Validação qualitativa** com ao menos um gestor da Galvitech.

Entregáveis secundários: base de dados sintética pública, *system prompt* em PT-BR otimizado para o domínio B2B e um protocolo de avaliação de agentes Text-to-SQL em português.

---

## Stack tecnológica

- **Linguagem:** Python 3.12
- **Backend / API:** FastAPI
- **Mensageiro:** Telegram Bot API (`python-telegram-bot`)
- **LLM:** Anthropic API (Claude) ou OpenAI API (GPT-4o), com *function calling*
- **Banco de dados:** PostgreSQL 16 (`psycopg`)
- **Dados sintéticos:** Faker

---

## Status do projeto

🚧 Em desenvolvimento — projeto de portfólio do PAC Extensionista.

### Roadmap

- [ ] Modelagem da base de dados sintética em PostgreSQL
- [ ] Geração dos dados sintéticos (Faker)
- [ ] Implementação do agente (pipeline Text-to-SQL + function calling)
- [ ] Integração com o aplicativo de mensagens
- [ ] Conjunto de perguntas de validação
- [ ] Experimentos e avaliação (execution accuracy, latência)
- [ ] Validação qualitativa com a Galvitech

### Trabalhos futuros

Geração de gráficos *inline*, suporte a mensagens de voz, autenticação por gestor com controle de acesso a indicadores, e *fine-tuning* do modelo para o vocabulário do domínio B2B brasileiro.

---

## Referências principais

- Golfarelli & Rizzi (2009). *Data Warehouse Design: Modern Principles and Methodologies.* McGraw-Hill.
- Guo et al. (2019). *Towards Complex Text-to-SQL in Cross-Domain Database with Intermediate Representation.* ACL. DOI: 10.18653/v1/P19-1444
- Wang et al. (2024). *A Survey on Large Language Model Based Autonomous Agents.* Frontiers of Computer Science. DOI: 10.1007/s11704-024-40231-1
- Mohammadjafari et al. (2024). *From Natural Language to SQL: Review of LLM-based Text-to-SQL Systems.* [arXiv:2410.01066](https://arxiv.org/abs/2410.01066)
- Shi et al. (2024). *A Survey on Employing Large Language Models for Text-to-SQL Tasks.* ACM Computing Surveys. DOI: 10.1145/3737873
- Yu et al. (2018). *Spider: A Large-Scale Human-Labeled Dataset for Text-to-SQL.* EMNLP. DOI: 10.18653/v1/D18-1425

---

## Licença

Este projeto será disponibilizado sob a licença **MIT**. A base de dados utilizada é inteiramente sintética, gerada pelo próprio autor, não contendo dados reais de clientes ou transações.

---

<p align="center">
  <em>Engenharia de Software — Centro Universitário Católica de Santa Catarina · 2026</em>
</p>
