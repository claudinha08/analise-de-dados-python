# Mini Projeto - Manipulação de Dados com Python e SQL

## 1. Visão Geral

Este projeto foi desenvolvido no contexto do curso de manipulação de dados com Python e SQL, com foco na preparação de uma base de dados para análises mais avançadas e para alimentar dashboards. A proposta principal é entender os dados, realizar a limpeza necessária, extrair estatísticas descritivas e comunicar os principais insights de forma objetiva.

O objetivo é criar um script em Python capaz de:

- importar uma base de dados de varejo;
- verificar a qualidade dos dados;
- identificar inconsistências e problemas estruturais;
- aplicar técnicas de limpeza e padronização;
- gerar estatísticas descritivas;
- realizar agrupamentos para análise de padrões;
- apresentar conclusões relevantes para tomada de decisão.

---

## 2. Objetivo do Projeto

Preparar uma base de dados para análises futuras, transformando-a em um conjunto estruturado, consistente e pronto para uso em relatórios, dashboards ou estudos estatísticos.

---

## 3. Descrição do Projeto

O projeto é útil para treinar a montagem e organização de scripts em Python para análise de dados. A base escolhida representa um conjunto de informações de varejo, com dados que exigem atenção à qualidade, estrutura e consistência antes da análise exploratória.

A proposta é simular um fluxo real de trabalho de analista de dados, com etapas que vão desde a carga dos dados até a interpretação dos resultados.

---

## 4. Requisitos

Para executar o projeto, é necessário ter instalado:

- Python 3.x
- Pandas
- Jupyter Notebook ou ambiente Python local
- Visual Studio Code (opcional, mas recomendado)
- Acesso à base de dados em CSV

---

## 5. Base de Dados

A base utilizada foi uma base de varejo sugerida no Kaggle:

https://www.kaggle.com/datasets/namespaiva/base-varejo/data

---

## 6. Metodologia

O desenvolvimento do projeto foi organizado em etapas.

### Etapa 1 - Importação dos dados
- Carregar a base em Python;
- verificar o número de registros, colunas e tipos de dados;
- validar a estrutura inicial da tabela.

### Etapa 2 - Transformação de strings, inteiros, floats e datas
- ajustar tipos de dados;
- padronizar valores textuais;
- converter colunas de data para datetime quando necessário.

### Etapa 3 - Limpeza de nulos e duplicatas
- identificar valores ausentes por coluna;
- remover ou imputar dados faltantes conforme a necessidade;
- eliminar registros duplicados;
- corrigir inconsistências em campos como datas e categorias.

### Etapa 4 - Estatística descritiva
- calcular métricas da coluna de número de filhos do cliente, como:
  - média; mediana; desvio padrão; moda; máximo; mínimo; contagem; quartis.

### Etapa 5 - Agrupamentos e análise de padrões
- comparar categorias e padrões de comportamento, por exemplo:
  - gênero com maior volume de vendas;
  - agrupamento por categoria, região ou outra variável relevante;
  - análise de relacionamento entre segmentos e indicadores de compra.

### Etapa 6 - Relatório e documentação
- registrar os principais achados;
- destacar problemas remanescentes na base;
- organizar o README e concluir o projeto.

---

## 7. Fluxo de Trabalho do Projeto

O script foi estruturado para seguir uma sequência lógica com base na proposta pelo projeto:

1. carregar a base de dados;
2. inspecionar a base;
3. validar a qualidade dos dados;
4. aplicar limpeza e padronização;
5. gerar estatísticas descritivas;
6. realizar agrupamentos;
7. registrar conclusões.

---

## 8. Resultados Esperados

Ao final do projeto, espera-se obter:

- uma base tratada e mais confiável;
- um relatório de qualidade dos dados;
- métricas estatísticas da variável escolhida;
- insights sobre padrões de compra e comportamento;
- uma documentação clara para uso futuro do projeto.

---

## 9. Exemplo de Conclusões

Entre os principais insights esperados, podem ser listados:

- a base contém registros com possíveis inconsistências que exigem tratamento antes de análises mais aprofundadas;
- a ausência de valores e duplicatas pode distorcer métricas e comparações;
- a conversão de colunas para tipos adequados facilita operações estatísticas e de agrupamento;
- a análise por categoria revela padrões importantes de comportamento de compra;
- a limpeza dos dados é essencial para garantir confiabilidade nos resultados.

---

## 10. Estrutura do Projeto

O projeto pode ser organizado da seguinte forma:

- script principal em Python
- base de dados original em CSV
- base tratada após limpeza
- README com a documentação do projeto
- arquivos de versionamento no GitHub

---

## 11. Sprints do Projeto

### Sprint 1 - Importação dos dados
Realização da importação da base no Kaggle e execução do script na IDE VS Code ou no Google Colab.

### Sprint 2 - Transformação de strings, inteiros, float e datetime
Desenvolvimento das funções de limpeza e conversão de tipos para garantir consistência dos dados.

### Sprint 3 - Limpeza de nulos e duplicatas
Aplicação de condições e funções para identificar e tratar valores ausentes, além de corrigir inconsistências de data e texto.

### Sprint 4 - Estatística descritiva
Aplicação de funções estatísticas para coletar parâmetros relevantes da variável número de filhos do cliente.

### Sprint 5 - Relatório e documentação
Construção do relatório final exibido no terminal e finalização do README com reflexão teórica.

### Sprint 6 - Versionamento
Envio dos arquivos para o repositório do GitHub, incluindo script, README e base tratada.

---

## 12. Como Executar

1. Clonar ou baixar o projeto;
2. abrir o arquivo Python no ambiente escolhido;
3. garantir que as bibliotecas necessárias estejam instaladas;
4. carregar a base de dados;
5. executar o script;
6. revisar as saídas no terminal e os resultados gerados.

---

## 13. Autoria

- Autora: Claudia Pedroso Ferreira
- E-mail: claudinha08@gmail.com

---

## 14. Observações Finais

Este projeto tem caráter didático e tem como principal objetivo desenvolver habilidades em manipulação, limpeza e análise exploratória de dados com Python. Além disso, ele reforça a importância da organização do código, documentação e interpretação dos resultados para tornar a análise útil e confiável.

