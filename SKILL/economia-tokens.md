
---
name: economia-tokens
description: Reduzir o consumo de tokens durante exploração do código, implementação, debugging, testes e revisão sem perder qualidade.
---

# Economia de tokens

## Quando usar
Em tarefas de desenvolvimento, investigação de bugs, testes e revisão.

## Regras
- Entenda o pedido antes de explorar o repositório.
- Identifique os arquivos relevantes usando buscas direcionadas.
- Leia apenas os trechos necessários.
- Prefira rg, grep e git diff a leituras integrais desnecessárias.
- Não repita comandos ou buscas que já produziram resultados úteis.
- Evite explicações extensas durante a execução.
- Não gere arquivos de documentação sem necessidade.
- Não replique código existente para resolver um problema local.
- Não carregue outras skills sem relação com a tarefa.
- Reutilize o contexto já disponível.

## Implementação
1. Identifique a causa ou o requisito.
2. Localize o menor conjunto de arquivos relevante.
3. Faça a menor alteração segura.
4. Execute verificações específicas.
5. Revise o diff.
6. Resuma as alterações e os resultados.

## Limites
- Nunca omita testes importantes apenas para economizar tokens.
- Não invente resultados de comandos.
- Não remova validações, segurança ou tratamento de erros
  para encurtar a implementação.
- Não leia o repositório inteiro sem uma justificativa concreta.

## Resposta final
Informe de forma objetiva:
- O que mudou.
- Quais testes foram executados.
- Problemas ou limitações encontrados.

