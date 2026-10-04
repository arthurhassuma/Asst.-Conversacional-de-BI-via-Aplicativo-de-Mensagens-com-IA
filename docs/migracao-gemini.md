# Migração para Gemini — 27/09/2026

## Decisão e escopo

O usuário autorizou substituir a Anthropic pelo Gemini para viabilizar o teste com cota gratuita. A proposta acadêmica original permanece intacta em PDF/DOCX; esta nota registra a mudança de implementação e sua justificativa de custo. As quatro camadas e as regras de segurança permanecem: Telegram, FastAPI, agente com duas tools e PostgreSQL 16.

Modelo padrão: `gemini-3.5-flash-lite`, configurável em GEMINI_MODEL. A documentação oficial lista entrada e saída gratuitas no Free Tier e recomenda essa família para projetos novos. A família 2.5 está restrita a usuários que já a utilizavam. A disponibilidade concreta e a cota dependem do projeto/chave; não foram presumidas nem verificadas sem credencial.

## Integração

- SDK oficial `google-genai`, cliente assíncrono `aio.models.generate_content`, API Gemini Developer (não Vertex AI).
- Planejador sem tools, saída JSON com schema explícito. Evidência do período e compatibilidade da métrica continuam validadas na aplicação antes de SQL.
- Executor declara exatamente `get_schema` e `execute_sql`. Automatic function calling do SDK desativado: a execução passa obrigatoriamente pelos validadores existentes.
- Respostas das tools usam `functionResponse` com nome e ID original quando fornecido. Chamadas paralelas recebem respostas correspondentes na mesma ordem.
- O conteúdo nativo do modelo, inclusive `thought_signature`, é preservado para as próximas chamadas; pensamentos não são exibidos ao gestor.
- As tentativas de autocorreção SQL, o timeout do turno e os limites de rounds continuam aplicados. O SDK faz uma tentativa por requisição, sem retries ocultos de cota e sem trocar o modelo automaticamente.
- Erros de chave/permissão, configuração, modelo indisponível, cota e indisponibilidade recebem mensagens PT-BR sem expor a resposta interna do provedor.
- A resposta final continua um identificador de resultado, renderizado com as células exatas pelo backend.

## Configuração e custo

Use GEMINI_API_KEY e GEMINI_MODEL; as antigas variáveis ANTHROPIC não são mais utilizadas. Chaves locais já existentes foram preservadas, mas não são enviadas ao novo provedor. O SDK Anthropic saiu das dependências do projeto.

Crie um projeto/chave no Google AI Studio e mantenha o projeto no **Free Tier**, sem ativar faturamento para este teste. O código não altera faturamento; se a chave pertencer a um projeto pago, as mesmas chamadas podem ser cobradas. Na cota gratuita, atingir limites produz erro e interrompe a consulta. A cota não é ilimitada e pode variar.

O Google informa que conteúdo no Free Tier pode ser usado para melhorar seus produtos. Envie apenas as perguntas e dados sintéticos deste projeto, sem informações reais de clientes ou credenciais em mensagens ao bot.

## Verificação

Testes usam o SDK oficial com transporte HTTP simulado. Cobrem declarações de tools, schema JSON do planejador, assinaturas opacas, chamadas paralelas, erros SQL, bloqueio de segurança e códigos HTTP de erro. A integração com Telegram também usa o SDK real com transporte simulado; PostgreSQL é real nos testes de integração.

O teste com a API Gemini e o Telegram reais ainda depende de configurar GEMINI_API_KEY, TELEGRAM_BOT_TOKEN e o usuário autorizado. Esta migração não inicia as avaliações acadêmicas da Fase 4.

## Fontes

- [SDK Python oficial](https://googleapis.github.io/python-genai/)
- [Preços e Free Tier](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite)
- [Disponibilidade e substituição de modelos](https://ai.google.dev/gemini-api/docs/deprecations)
- [Criação da chave](https://ai.google.dev/gemini-api/docs/get-started)
- [Function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [Saídas estruturadas](https://ai.google.dev/gemini-api/docs/structured-output)
