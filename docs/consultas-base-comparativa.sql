-- Referências somente leitura para o cenário 2025-01 a 2026-10.
-- Outubro de 2026 é um mês sintético completo; comparar anos por períodos iguais.

SELECT date_trunc('month', emissao)::date AS mes, SUM(valor) AS total
FROM faturamento
WHERE status <> 'cancelada'
  AND emissao >= DATE '2025-01-01' AND emissao < DATE '2026-11-01'
GROUP BY 1 ORDER BY 1;

SELECT date_part('year', emissao)::integer AS ano, SUM(valor) AS total
FROM faturamento
WHERE status <> 'cancelada'
  AND emissao >= DATE '2025-01-01' AND emissao < DATE '2026-11-01'
  AND date_part('month', emissao) <= 10
GROUP BY 1 ORDER BY 1;

SELECT date_trunc('month', pagamento)::date AS mes, SUM(valor) AS total
FROM faturamento
WHERE status = 'paga'
  AND pagamento >= DATE '2025-01-01' AND pagamento < DATE '2026-11-01'
GROUP BY 1 ORDER BY 1;

SELECT date_trunc('month', data_pedido)::date AS mes,
       COUNT(*) AS quantidade, SUM(valor) AS valor
FROM pedidos
WHERE status <> 'cancelado'
  AND data_pedido >= DATE '2025-01-01' AND data_pedido < DATE '2026-11-01'
GROUP BY 1 ORDER BY 1;

SELECT competencia AS mes, SUM(horas_previstas) AS horas_previstas,
       SUM(horas_realizadas) AS horas_realizadas,
       SUM(chamados_abertos) AS chamados_abertos,
       SUM(chamados_resolvidos) AS chamados_resolvidos,
       SUM(chamados_resolvidos)::numeric / NULLIF(SUM(chamados_abertos), 0) AS taxa
FROM indicadores_operacionais
WHERE competencia >= DATE '2025-01-01' AND competencia < DATE '2026-11-01'
GROUP BY 1 ORDER BY 1;

SELECT c.segmento, SUM(f.valor) AS total
FROM faturamento f
JOIN pedidos p ON p.id = f.pedido_id
JOIN contratos ct ON ct.id = p.contrato_id
JOIN clientes c ON c.id = ct.cliente_id
WHERE f.status <> 'cancelada'
  AND f.emissao >= DATE '2026-09-01' AND f.emissao < DATE '2026-10-01'
GROUP BY c.segmento ORDER BY total DESC;
