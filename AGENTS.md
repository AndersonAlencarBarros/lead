
# Instruções do projeto para IA

## Objetivo
Desenvolver soluções corretas, seguras, simples e fáceis de manter.

## Stack
- Python
- FastAPI
- PostgreSQL
- Docker
- ETL

Confirme a stack real nos arquivos do projeto antes de assumir
que todos esses componentes estão em uso.

## Regras obrigatórias
- Antes de modificar código, inspecione apenas os arquivos
  relevantes para a tarefa.
- Respeite a arquitetura e os padrões existentes.
- Não reescreva módulos inteiros quando uma alteração pequena
  resolver o problema.
- Não crie abstrações, dependências ou arquivos desnecessários.
- Não invente funções, configurações, tabelas ou endpoints.
- Não altere contratos públicos sem necessidade.
- Nunca exponha segredos, tokens ou dados sensíveis.
- Não execute operações destrutivas sem autorização.

## Skills
- Consulte as skills disponíveis antes de iniciar uma tarefa.
- Carregue as skills relevantes usando a ferramenta skill.
- Para tarefas de código, aplique as skills de economia de tokens,
  Python e testes quando estiverem disponíveis.
- Para SQL, migrações ou consultas, use a skill de banco de dados.
- Não carregue skills sem relação com a tarefa.
- Se uma skill obrigatória não estiver disponível, informe isso.

## Fluxo de trabalho
1. Identifique o objetivo da tarefa.
2. Inspecione os arquivos diretamente relacionados.
3. Carregue as skills relevantes.
4. Faça a menor alteração que resolva o problema.
5. Execute testes e verificações pertinentes.
6. Revise o diff para detectar efeitos colaterais.
7. Informe arquivos alterados, testes executados e limitações.

## Economia de tokens
- Prefira buscas direcionadas a leituras recursivas de arquivos.
- Não leia arquivos grandes integralmente sem necessidade.
- Não repita contexto já conhecido.
- Não exiba arquivos completos quando um trecho for suficiente.
- Evite múltiplas investigações equivalentes.
- Dê respostas objetivas, com evidências e resultados.
- Não sacrifique correção, segurança ou testes para economizar tokens.

## Documentação
Consulte docs/ai/ somente quando a tarefa exigir detalhes
da arquitetura, dos testes ou do banco de dados.
Mantenha a documentação atualizada quando houver mudanças relevantes.

