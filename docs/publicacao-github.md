# Publicação e nova verificação — 04/10/2026

## Origem e preservação

O projeto foi encontrado em `C:/Users/arthu/PAC - TCC`, com Git inicializado,
sem commits e sem remote. O destino `arthurhassuma/pac_privado` estava privado,
sem branches e sem conteúdo. Não havia trabalho remoto a sobrescrever.

Foram copiados 43 arquivos elegíveis pelo ignore original, incluindo código,
testes, documentação, proposta PDF e relatório DOCX. A cópia foi conferida por
SHA-256. Os 43 arquivos originais permaneceram inalterados. O ambiente virtual,
o `.env` e o banco original ficaram na pasta de origem.

O `.gitignore` foi ampliado para credenciais, variantes de `.env`, chaves privadas,
logs, bancos locais, backups e artefatos gerados. `.env.example` continua versionado.
Uma inspeção local procurou padrões de tokens/chaves e os segredos conhecidos do
`.env` original no material selecionado, incluindo XML do DOCX e streams
descompactáveis do PDF; não houve achados. Essa inspeção não substitui revisão
de novos arquivos antes de cada publicação.

## Evidências atuais

- 65 testes aprovados, sem skips, em Windows com Python 3.13.1 e PostgreSQL 16.
- Banco novo e isolado, seed 42, 30 clientes; o banco original não foi utilizado.
- Carga: 30 clientes, 56 contratos, 672 pedidos, 628 registros de faturamento,
  672 indicadores operacionais.
- As seis verificações de consistência retornaram zero problemas.
- `ruff check app scripts tests` passou; `pip check` não encontrou conflitos.
- O PostgreSQL temporário foi encerrado após os testes; arquivos locais ignorados
  foram preservados para retomada.
- A árvore publicada no commit de importação `68d55baf67729448aba1912742c7927b06662d35`
  coincide com a árvore local: `05f3617031142b61cecd6043ca73b71f1244e4e1`.

O registro em `verificacao.md` descreve a primeira entrega, anterior à migração
Gemini. Não deve ser interpretado como a contagem atual nem como prova de API real.

## Integração contínua

O workflow `.github/workflows/tests.yml` prepara PostgreSQL 16 descartável,
instala as dependências fixadas, verifica consistência, executa lint e a suíte
completa. Usa APIs Gemini/Telegram simuladas e não necessita de chaves externas.
Senhas `ci_only_*` pertencem somente ao serviço efêmero de testes.

O resultado local acima não comprova execução do workflow no GitHub: consulte a
execução vinculada ao commit em [Actions](https://github.com/arthurhassuma/pac_privado/actions).
O workflow segue os exemplos oficiais de [serviços PostgreSQL](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers),
[checkout](https://github.com/actions/checkout) e [setup-python](https://github.com/actions/setup-python).

## Limitações e próxima validação

Gemini e Telegram reais ainda não foram testados. A origem possui chave Gemini,
token Telegram e lista de usuários vazios. Configure esses valores apenas no
`.env` do checkout usado para executar o projeto. Não os envie em commits, issues
ou mensagens. Confirme o modelo disponível na conta antes do teste.

A execução do Docker Compose também permanece pendente. Os testes de integração
locais usaram PostgreSQL nativo. A avaliação semântica e a entrega acadêmica estão
organizadas no [roteiro até dezembro](roteiro-entrega-dezembro.md).
