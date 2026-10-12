# Avaliação gerencial — conjunto novo

Conjunto `evaluation/managerial-cases-v1.json`: 35 cenários, IDs independentes dos 40 casos originais. Desenvolvimento D21–D45: 20 respostas, dois esclarecimentos e três explicações de limites. Reservado T21–T30: oito respostas, um esclarecimento e uma explicação de limite. Ao todo, 28 referências SQL, escritas independentemente dos templates de produção e executadas pela role de leitura no PostgreSQL comparativo.

Base: perfil comparativo-v1, seed 42, 100 clientes, janeiro/2025 a outubro/2026. Registrar fingerprint real antes/depois; não executar na base antiga dos experimentos por engano. Outubro inteiro é cenário sintético. Os gabaritos incluem definições de emissão/pagamento, cancelamento, participação e desvio; não são evidência de causa ou previsão. Gabaritos revisados tecnicamente, sem alegar revisão de especialista externo.

As formas de saída esperadas são explícitas: agrupamentos de cliente/contrato incluem identificador e nome, rankings incluem posição calculada e comparações incluem direção calculada. Ordenação é estável. Comparação decimal continua exata, sem tolerância; representação equivalente fora desse contrato não é automaticamente julgada como semanticamente correta. A coluna auxiliar `registros` não é dado de negócio avaliado. Essas restrições do gabarito devem acompanhar qualquer taxa divulgada.

## Engenharia e aprendizagem não são avaliação do Gemini

A classificação de intenções usa outro corpus, com 196/28/56 formulações de treino/validação/teste, sem resultados financeiros. Seu teste reservado já foi executado; não ajustar o classificador usando o desempenho observado. Macro-F1 e accuracy de intenção não medem SQL, esclarecimento ou entrega no Telegram.

Em 12/10/2026 as 28 referências foram executadas no PostgreSQL local. Os 20 cenários de resposta de desenvolvimento também podem ser conferidos com planos e APIs simulados, para validar compilação/renderização contra os gabaritos. Essa verificação não mede interpretação do Gemini nem é rodada real. Os dez cenários reservados do agente só recebem resultado oficial após congelar o código e executar o teste real.

## Rodadas reais

Preparar no ambiente conectado `.local/gerencial.env`, privadamente combinando chave/modelo existentes e DSN readonly da base comparativa. Não incluir senhas, token ou IDs nos relatórios. O executor não precisa de Telegram e não deve enviar mensagens ou reiniciar o bot durante a avaliação.

```sh
python -m scripts.evaluate validate --dataset evaluation/managerial-cases-v1.json --env-file .local/gerencial.env
python -m scripts.evaluate run --live --dataset evaluation/managerial-cases-v1.json --split development --interval 60 --limit 25 --env-file .local/gerencial.env
# Após concluir ajustes de desenvolvimento, revisão e congelamento:
python -m scripts.evaluate run --live --dataset evaluation/managerial-cases-v1.json --split test --interval 60 --limit 10 --env-file .local/gerencial.env
```

Manter classificador desativado por padrão: a validação selecionou limiar com cobertura aceita zero. Conferir em desenvolvimento, separadamente, os exemplos aceitos e os prompts com flag ligada/desligada. Se os prompts forem iguais, não atribuir melhora ao classificador; uma rodada duplicada real sem mudança de entrada não demonstra benefício causal e pode ser substituída por essa conferência de engenharia, com justificativa registrada. Não concluir ganho de latência a partir dessa equivalência de prompts.

O manifesto registra fonte, dataset, modelo configurado, flag do classificador, hashes do artefato/corpus e banco. Tokens e versão resolvida ficam no trace quando o SDK informar. Cota/erro externo interrompe a rodada com checkpoint; não inventar resultados faltantes ou concluir taxa oficial de uma rodada incompleta. Não mudar para provedor/modelo pago ou repetir automaticamente chamadas interrompidas.

Reportar separadamente acerto de respostas, esclarecimentos e explicações de limites. Latência mede agente/banco, sem transporte Telegram. Revisar também legibilidade, períodos mostrados, avisos de parcialidade, fidelidade dos dígitos e ausência de causalidade inventada. Uma resposta numericamente correta não comprova sozinha texto útil ao gestor; revisão técnica não equivale a validação qualitativa humana.

Depois de ajustes baseados em desenvolvimento, congelar versão, dataset e banco antes do reservado. Se resultados reservados orientarem mudanças, declarar contaminação e usar um novo conjunto independente para uma conclusão posterior. Preservar a versão e as métricas antigas `59c9eb8`.
