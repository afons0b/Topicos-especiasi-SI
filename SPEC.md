# Especificação — Controle de Gastos Pessoais

**Versão da especificação:** 0.2.0  
**Status:** Rascunho para validação humana  
**Data:** 2026-09-28  
**Abordagem:** Specification-Driven Development (SDD)

## 1. Visão geral

Aplicação web simples para controle de gastos pessoais. O sistema será composto por um frontend separado de um backend. O frontend consumirá uma API REST exposta pelo backend, e somente o backend terá acesso ao banco PostgreSQL por meio do SQLAlchemy.

Esta especificação define o escopo da primeira entrega acadêmica (AP1), os contratos da API, as regras de negócio e os critérios verificáveis antes do início da implementação.

## 2. Objetivo

Permitir que uma pessoa registre, consulte, altere e exclua seus gastos pessoais, filtre a listagem por categoria e/ou período e visualize o total correspondente exatamente aos gastos retornados pelos filtros ativos.

## 3. Escopo

Estão incluídos na AP1:

- cadastrar um gasto com descrição, valor, categoria e data;
- listar os gastos cadastrados;
- buscar um gasto por identificador para apoiar consulta e edição;
- editar todos os dados informados de um gasto existente;
- excluir um gasto;
- filtrar gastos por uma categoria;
- filtrar gastos por período, usando data inicial e/ou data final;
- combinar o filtro de categoria com os filtros de período;
- calcular e exibir o total dos gastos que satisfazem os filtros ativos;
- validar os dados conforme as regras de negócio desta especificação;
- expor essas operações por uma API REST;
- disponibilizar uma interface web em HTML, CSS e JavaScript puro que consuma a API com `fetch`;
- incluir testes automatizados do backend com `pytest`.

## 4. Fora de escopo

Não fazem parte da AP1:

- autenticação, autorização, usuários ou múltiplas contas;
- receitas, saldos, orçamentos, metas ou limites de gastos;
- categorias personalizadas;
- parcelamento, recorrência ou agendamento de gastos;
- anexos, comprovantes ou imagens;
- importação ou exportação de dados;
- gráficos, relatórios ou análises estatísticas;
- integração bancária ou com serviços de pagamento;
- conversão entre moedas;
- paginação, busca textual ou ordenação configurável;
- exclusão ou edição em lote;
- notificações;
- aplicação móvel ou funcionamento offline;
- acesso direto do frontend ao PostgreSQL.

## 5. Arquitetura proposta

### 5.1 Componentes

1. **Frontend:** aplicação estática em HTML, CSS e JavaScript puro. Apresenta formulário e listagem, envia requisições com `fetch` e exibe respostas e erros da API.
2. **Backend:** aplicação Python com FastAPI. Expõe a API REST, valida as requisições, aplica as regras de negócio, calcula o total filtrado e acessa a persistência por meio do SQLAlchemy.
3. **Persistência:** banco PostgreSQL acessado exclusivamente pelo backend com SQLAlchemy.
4. **Testes:** testes automatizados do backend executados com `pytest`.

### 5.2 Fluxo de comunicação

`Navegador → requisição HTTP/JSON → API FastAPI → SQLAlchemy → PostgreSQL`

`Navegador ← resposta HTTP/JSON ← API FastAPI ← SQLAlchemy ← PostgreSQL`

### 5.3 Implantação prevista

- backend em serviço compatível com FastAPI, como Render;
- frontend em hospedagem de conteúdo estático, como Vercel ou GitHub Pages;
- URL do backend configurável no frontend;
- CORS configurado no backend para permitir, em produção, exclusivamente a origem do frontend implantado.

Os provedores definitivos, as URLs e o serviço PostgreSQL do ambiente de produção permanecem pendentes de decisão. A URL final do frontend determinará a única origem permitida por CORS em produção.

## 6. Modelo de dados

### 6.1 Entidade `Gasto`

| Campo | Tipo de domínio | Obrigatório | Restrições |
|---|---|---:|---|
| `id` | inteiro | sim | Gerado pelo backend; único; positivo; imutável. |
| `descricao` | texto | sim | Espaços no início e no fim são removidos; após a normalização, deve conter de 1 a 120 caracteres. |
| `valor` | decimal monetário | sim | Valor em BRL, maior que zero e com exatamente duas casas decimais; não usa `float` como fonte de verdade. |
| `categoria` | enumeração | sim | Um dos valores permitidos. |
| `data` | data civil | sim | Formato `AAAA-MM-DD`; não pode ser posterior à data corrente adotada pelo sistema. |

Valores permitidos para `categoria`:

- `ALIMENTACAO`
- `TRANSPORTE`
- `LAZER`
- `SAUDE`
- `ESTUDOS`
- `OUTROS`

### 6.2 Representação de transporte

Exemplo ilustrativo de um gasto retornado pela API:

```json
{
  "id": 1,
  "descricao": "Almoço",
  "valor": "32.50",
  "categoria": "ALIMENTACAO",
  "data": "2026-09-27"
}
```

No contrato JSON, `valor` e `total` são strings decimais em BRL com exatamente duas casas, como `"32.50"`. No backend, valores e cálculos monetários usam tipo decimal exato; no PostgreSQL, usam coluna `NUMERIC` com escala 2. `float` binário não pode ser a fonte de verdade em transporte, validação, persistência ou cálculo. Valores com mais ou menos de duas casas são rejeitados, sem arredondamento automático. A precisão máxima da coluna e o maior valor aceito ainda precisam ser definidos.

### 6.3 Exclusão

A exclusão é física: ao concluir `DELETE`, o registro é removido do PostgreSQL. Depois disso, o gasto não pode ser recuperado pela API, aparecer nas listagens nem participar do total.

## 7. API

### 7.1 Convenções gerais

- Prefixo da API: `/api/gastos`.
- Corpos de requisição e resposta usam JSON, salvo respostas sem corpo.
- Datas usam o formato ISO `AAAA-MM-DD`.
- `categoria` usa exatamente um dos valores enumerados no modelo de dados.
- Filtros combinados são aplicados com lógica **E**: o gasto precisa satisfazer todos os filtros enviados.
- Os limites do período são inclusivos: `data_inicio <= data do gasto <= data_fim`.
- A ausência de filtros retorna todos os gastos existentes e o total correspondente.
- A ausência de resultados não é erro: a API retorna lista vazia e total `"0.00"`.
- Não há paginação nesta versão.
- A listagem é ordenada por `data` decrescente e, em caso de empate, por `id` decrescente.

Formato obrigatório e consistente para erros:

```json
{
  "erro": {
    "codigo": "CODIGO_ESTAVEL",
    "mensagem": "Mensagem legível",
    "campos": {
      "nome_do_campo": "Motivo da rejeição"
    }
  }
}
```

`campos` pode ser omitido quando o erro não estiver associado a um campo específico. A implementação deve normalizar inclusive os erros nativos de validação do FastAPI para esse contrato.

### 7.2 Criar gasto

- **Método e rota:** `POST /api/gastos`
- **Parâmetros:** nenhum.
- **Corpo:**

```json
{
  "descricao": "Almoço",
  "valor": "32.50",
  "categoria": "ALIMENTACAO",
  "data": "2026-09-27"
}
```

- **Resposta de sucesso:** `201 Created`, com o gasto criado, incluindo `id`.
- **Erros principais:**
  - `400 Bad Request` para JSON malformado;
  - `422 Unprocessable Entity` para campo ausente, tipo ou formato inválido, descrição fora do limite após normalização, valor não positivo ou sem exatamente duas casas decimais, categoria não permitida ou data futura.

Campos não pertencentes ao contrato deverão ser rejeitados com `422`, evitando aceitação silenciosa de dados não especificados.

### 7.3 Listar e filtrar gastos

- **Método e rota:** `GET /api/gastos`
- **Parâmetros de consulta opcionais:**
  - `categoria`: uma categoria permitida;
  - `data_inicio`: data no formato `AAAA-MM-DD`;
  - `data_fim`: data no formato `AAAA-MM-DD`.
- **Corpo:** não possui.
- **Resposta de sucesso:** `200 OK`.

```json
{
  "itens": [
    {
      "id": 1,
      "descricao": "Almoço",
      "valor": "32.50",
      "categoria": "ALIMENTACAO",
      "data": "2026-09-27"
    }
  ],
  "total": "32.50"
}
```

- **Erros principais:** `422 Unprocessable Entity` para categoria não permitida, data em formato inválido ou intervalo em que `data_inicio` seja posterior a `data_fim`.

O backend calcula `total`; o frontend não deve recalcular um valor divergente a partir de outra coleção.

### 7.4 Buscar gasto por id

- **Método e rota:** `GET /api/gastos/{id}`
- **Parâmetro de rota:** `id`, inteiro positivo.
- **Corpo:** não possui.
- **Resposta de sucesso:** `200 OK`, com o gasto encontrado.
- **Erros principais:**
  - `422 Unprocessable Entity` para identificador com formato inválido ou não positivo;
  - `404 Not Found` quando não existir gasto com o identificador informado.

### 7.5 Editar gasto

- **Método e rota:** `PUT /api/gastos/{id}`
- **Parâmetro de rota:** `id`, inteiro positivo.
- **Corpo:** representação completa dos campos editáveis:

```json
{
  "descricao": "Jantar",
  "valor": "45.00",
  "categoria": "ALIMENTACAO",
  "data": "2026-09-27"
}
```

- **Resposta de sucesso:** `200 OK`, com o gasto atualizado.
- **Erros principais:**
  - `400 Bad Request` para JSON malformado;
  - `422 Unprocessable Entity` para `id` inválido ou qualquer campo ausente ou inválido, conforme as mesmas regras da criação;
  - `404 Not Found` quando não existir gasto com o identificador informado.

O `id` não integra o corpo editável e não pode ser alterado. `PUT` exige todos os campos editáveis. Não existe endpoint `PATCH`; atualização parcial não faz parte da AP1.

### 7.6 Excluir gasto

- **Método e rota:** `DELETE /api/gastos/{id}`
- **Parâmetro de rota:** `id`, inteiro positivo.
- **Corpo:** não possui.
- **Resposta de sucesso:** `204 No Content`, sem corpo.
- **Erros principais:**
  - `422 Unprocessable Entity` para identificador com formato inválido ou não positivo;
  - `404 Not Found` quando não existir gasto com o identificador informado, inclusive em nova tentativa de excluir um gasto já removido.

## 8. Regras de negócio

1. A descrição é obrigatória; seus espaços no início e no fim são removidos antes da validação e da persistência.
2. Após a normalização, a descrição deve conter entre 1 e 120 caracteres, inclusive.
3. O valor é obrigatório, expresso em BRL, deve ser estritamente maior que zero e possuir exatamente duas casas decimais.
4. Valores monetários e totais usam aritmética decimal exata; `float` não pode ser usado como fonte de verdade.
5. Categoria é obrigatória e deve pertencer à lista fechada de categorias iniciais.
6. Data é obrigatória e deve representar uma data civil válida no formato `AAAA-MM-DD`.
7. A data do gasto não pode estar no futuro, segundo a referência de data corrente que ainda será definida.
8. As mesmas validações se aplicam ao cadastro e à edição completa por `PUT`.
9. A exclusão é física; após a remoção, o gasto não aparece na listagem, não é retornado na busca por id e não participa do total.
10. O total é calculado pelo backend, com aritmética decimal exata, somando somente os gastos retornados após a aplicação de todos os filtros ativos.
11. Os filtros de data têm limites inclusivos.
12. Quando `data_inicio` e `data_fim` forem informadas, `data_inicio` não pode ser posterior a `data_fim`.
13. Quando nenhum gasto satisfizer os filtros, a lista será vazia e o total será `"0.00"`.
14. A listagem é ordenada primeiro por data decrescente e depois por `id` decrescente.

## 9. Casos de uso

### UC01 — Cadastrar gasto

1. A pessoa informa descrição, valor, categoria e data.
2. O frontend envia os dados à API.
3. A API valida e persiste o gasto.
4. O sistema confirma o cadastro e permite que a listagem seja atualizada.
5. Se os dados forem inválidos, nada é persistido e o erro é apresentado.

### UC02 — Listar gastos

1. A pessoa acessa a aplicação.
2. O frontend solicita a listagem sem filtros.
3. A API retorna todos os gastos existentes, na ordenação padrão, e o total deles.
4. O frontend apresenta a lista e o total.

### UC03 — Filtrar gastos

1. A pessoa seleciona uma categoria e/ou informa data inicial e/ou final.
2. O frontend envia somente os filtros ativos.
3. A API retorna os gastos que satisfazem todos os filtros e o total desses gastos.
4. O frontend substitui a listagem e o total pelos dados da resposta.

### UC04 — Editar gasto

1. A pessoa escolhe um gasto existente.
2. O frontend obtém ou reutiliza os dados atuais e apresenta a edição.
3. A pessoa envia a representação completa atualizada.
4. A API valida e persiste as alterações.
5. Em caso de erro, os dados persistidos permanecem inalterados e o erro é apresentado.

### UC05 — Excluir gasto

1. A pessoa solicita a exclusão de um gasto existente.
2. O frontend envia a solicitação à API.
3. A API remove fisicamente o gasto do PostgreSQL.
4. O frontend atualiza a listagem e o total do conjunto filtrado atual.

## 10. Critérios de aceitação

### CA01 — Cadastro válido

**Dado** um corpo com descrição que resulte em 1 a 120 caracteres após normalização, valor em BRL maior que zero representado com duas casas decimais, categoria permitida e data válida não futura,  
**quando** `POST /api/gastos` for chamado,  
**então** a resposta será `201`, conterá um `id` positivo, a descrição sem espaços nas extremidades e os demais dados enviados, e o gasto estará disponível na listagem.

### CA02 — Campos obrigatórios

**Dado** um cadastro ou edição sem qualquer um dos campos `descricao`, `valor`, `categoria` ou `data`,  
**quando** a requisição for enviada,  
**então** a resposta será `422` e nenhum dado será criado ou alterado.

### CA03 — Descrição inválida

**Dado** um cadastro ou edição cuja descrição, após remover espaços no início e no fim, possua zero ou mais de 120 caracteres,  
**quando** a requisição for enviada,  
**então** a resposta será `422` e indicará erro no campo `descricao`.

### CA04 — Valor inválido

**Dado** um cadastro ou edição com valor igual a zero, negativo, que não seja uma string decimal ou que não possua exatamente duas casas decimais,  
**quando** a requisição for enviada,  
**então** a resposta será `422` e indicará erro no campo `valor`.

### CA05 — Categoria inválida

**Dado** um cadastro, edição ou filtro com categoria diferente das seis categorias permitidas,  
**quando** a requisição for enviada,  
**então** a resposta será `422` e indicará erro em `categoria`.

### CA06 — Data futura

**Dado** um cadastro ou edição cuja data seja posterior à data corrente adotada pelo sistema,  
**quando** a requisição for enviada,  
**então** a resposta será `422`, indicará erro no campo `data` e não criará nem alterará o gasto.

### CA07 — Listagem sem filtros

**Dado** que existam gastos e nenhum filtro seja enviado,  
**quando** `GET /api/gastos` for chamado,  
**então** a resposta será `200`, `itens` conterá todos os gastos existentes na ordenação padrão e `total` será a soma decimal exata de seus valores.

### CA08 — Filtro por categoria

**Dado** que existam gastos em categorias distintas,  
**quando** a listagem for solicitada com `categoria=SAUDE`,  
**então** todos os itens retornados terão categoria `SAUDE` e `total` será a soma somente desses itens.

### CA09 — Filtro por período inclusivo

**Dado** que existam gastos antes, dentro e depois de um período, inclusive nas duas datas-limite,  
**quando** a listagem for solicitada com `data_inicio` e `data_fim`,  
**então** serão retornados os gastos das datas-limite e entre elas, mas nenhum gasto fora delas; `total` somará somente os itens retornados.

### CA10 — Filtro com apenas um limite de data

**Dado** um conjunto de gastos,  
**quando** somente `data_inicio` for enviada,  
**então** serão retornados apenas gastos nessa data ou posteriores;  
**e quando** somente `data_fim` for enviada,  
**então** serão retornados apenas gastos nessa data ou anteriores.

### CA11 — Combinação de filtros

**Dado** que categoria e pelo menos um limite de data estejam ativos,  
**quando** a listagem for solicitada,  
**então** cada item retornado satisfará simultaneamente a categoria e o período, e `total` será exatamente a soma desses itens.

### CA12 — Nenhum resultado

**Dado** um filtro que não corresponda a nenhum gasto,  
**quando** a listagem for solicitada,  
**então** a resposta será `200`, `itens` será `[]` e `total` será `"0.00"`.

### CA13 — Intervalo inválido

**Dado** `data_inicio` posterior a `data_fim`,  
**quando** a listagem for solicitada,  
**então** a resposta será `422` e não retornará uma listagem parcial.

### CA14 — Busca por id

**Dado** o `id` de um gasto existente,  
**quando** `GET /api/gastos/{id}` for chamado,  
**então** a resposta será `200` e conterá exatamente esse gasto.

### CA15 — Edição válida

**Dado** um gasto existente e um corpo completo válido com dados alterados,  
**quando** `PUT /api/gastos/{id}` for chamado,  
**então** a resposta será `200`, manterá o mesmo `id` e a consulta posterior retornará os novos dados.

### CA16 — Edição inválida é atômica

**Dado** um gasto existente e um corpo de edição inválido,  
**quando** a edição for solicitada,  
**então** a resposta será `422` e uma consulta posterior retornará todos os dados anteriores sem alteração.

### CA17 — Exclusão

**Dado** um gasto existente que participa da listagem e do total,  
**quando** `DELETE /api/gastos/{id}` for chamado,  
**então** a resposta será `204`, sem corpo; o registro deixará de existir no PostgreSQL; consultas posteriores por id retornarão `404`; o gasto não aparecerá em nenhuma listagem e seu valor não participará de nenhum total.

### CA18 — Recurso inexistente

**Dado** um `id` positivo inexistente ou já excluído,  
**quando** houver busca, edição ou exclusão por esse `id`,  
**então** a resposta será `404` e nenhum outro gasto será alterado.

### CA19 — Integração do frontend

**Dado** que frontend e backend estejam configurados e acessíveis,  
**quando** a pessoa cadastrar, listar, filtrar, editar ou excluir pela interface,  
**então** o frontend realizará a operação pela API com `fetch`, sem acesso direto ao banco, e refletirá o resultado ou erro retornado.

### CA20 — Ordenação padrão

**Dado** que existam gastos em datas diferentes e mais de um gasto na mesma data,  
**quando** `GET /api/gastos` for chamado com ou sem filtros,  
**então** os itens serão ordenados por `data` decrescente e os itens com a mesma data por `id` decrescente.

### CA21 — Formato consistente de erro

**Dado** qualquer requisição que resulte em erro de validação, recurso inexistente ou JSON malformado,  
**quando** a API responder,  
**então** o corpo será JSON e conterá `erro.codigo` e `erro.mensagem`, além de `erro.campos` quando houver erros associados a campos.

### CA22 — CORS em produção

**Dado** o backend executando com configuração de produção e a origem final do frontend definida,  
**quando** forem avaliadas requisições entre origens,  
**então** somente a origem exata do frontend estará autorizada pela política CORS.

## 11. Requisitos não funcionais

- **Separação:** frontend e backend devem permanecer componentes separados; apenas o backend acessa o PostgreSQL, usando SQLAlchemy.
- **Compatibilidade:** a API deve executar em ambiente compatível com Python e FastAPI; o frontend deve executar em navegadores modernos com suporte a `fetch`.
- **Integridade:** criação e edição inválidas não podem persistir alterações parciais.
- **Consistência:** listagem e total devem ser calculados sobre o mesmo conjunto filtrado e retornados na mesma resposta; valores monetários devem manter duas casas decimais sem usar `float` como fonte de verdade.
- **Testabilidade:** regras de negócio e contratos da API devem possuir testes automatizados com `pytest`.
- **Manutenibilidade:** as responsabilidades de API, regras de negócio e persistência devem ser separadas no backend, sem exigir arquitetura além da necessária para a AP1.
- **Segurança básica:** entradas devem ser validadas no backend; mensagens de erro não devem expor caminhos internos, comandos SQL ou rastros de exceção.
- **Configuração:** URL da API, conexão PostgreSQL, CORS e demais configurações de ambiente não devem ficar duplicadas em vários pontos da aplicação; em produção, CORS deve permitir somente a origem exata do frontend.
- **Desempenho:** não há meta quantitativa definida nesta etapa; a solução deve ser adequada ao pequeno volume acadêmico esperado.
- **Acessibilidade e responsividade:** níveis ou métricas específicos não foram definidos e permanecem como ponto de decisão, sem autorizar novas funcionalidades.

## 12. Plano de implementação

1. **Aprovar a especificação:** resolver os pontos de decisão humana, atualizar a versão deste documento e congelar o contrato inicial.
2. **Preparar o backend mínimo:** estruturar o projeto FastAPI, configuração e execução de testes, sem implementar o frontend.
3. **Modelar a persistência:** criar com SQLAlchemy o esquema PostgreSQL, incluindo valor `NUMERIC` com escala 2 e exclusão física.
4. **Implementar validações e persistência:** cobrir as regras de criação, leitura, atualização e exclusão com testes unitários.
5. **Implementar a API CRUD:** adicionar cada endpoint e seus testes de contrato de forma incremental.
6. **Implementar filtros e total:** aplicar categoria e período com lógica E, limites inclusivos e total calculado no backend; cobrir combinações em testes.
7. **Construir o frontend mínimo:** criar formulário, listagem, controles de filtro, total e ações de edição/exclusão consumindo a API.
8. **Tratar estados da interface:** apresentar carregamento, ausência de resultados, sucesso e erros necessários às operações definidas.
9. **Realizar testes integrados:** validar os critérios de aceitação entre frontend, API e banco.
10. **Preparar deploy:** escolher provedores, configurar a conexão PostgreSQL, a URL da API e CORS restrito à origem do frontend em produção.
11. **Validar a AP1:** executar testes, revisar o escopo e confirmar que nenhuma funcionalidade fora de escopo foi incorporada.

## 13. Tarefas

- [ ] Revisar e aprovar a versão 0.2.0 da especificação.
- [ ] Definir a precisão máxima da coluna monetária e o maior valor aceito.
- [ ] Definir referência de data corrente e fuso horário.
- [ ] Escolher os provedores de deploy e o serviço PostgreSQL.
- [ ] Definir a origem de desenvolvimento permitida por CORS.
- [ ] Criar a estrutura mínima do backend FastAPI e do ambiente de testes.
- [ ] Criar com SQLAlchemy o esquema no PostgreSQL conforme as decisões aprovadas.
- [ ] Implementar e testar validações de gasto.
- [ ] Implementar e testar `POST /api/gastos`.
- [ ] Implementar e testar `GET /api/gastos/{id}`.
- [ ] Implementar e testar `GET /api/gastos` sem filtros.
- [ ] Implementar e testar filtros por categoria e período.
- [ ] Implementar e testar o total do conjunto filtrado.
- [ ] Implementar e testar `PUT /api/gastos/{id}`.
- [ ] Implementar e testar `DELETE /api/gastos/{id}`.
- [ ] Criar a estrutura mínima do frontend.
- [ ] Implementar o cadastro no frontend via `fetch`.
- [ ] Implementar listagem, filtros e exibição do total no frontend.
- [ ] Implementar edição e exclusão no frontend.
- [ ] Implementar a apresentação dos estados e erros definidos.
- [ ] Executar todos os cenários de aceitação integrados.
- [ ] Configurar e validar o deploy do backend.
- [ ] Configurar e validar o deploy do frontend.
- [ ] Fazer a revisão final de escopo da AP1.

## Pontos de atenção e decisões humanas pendentes

Não foram identificadas contradições diretas entre os requisitos fornecidos. Foram identificadas as seguintes ambiguidades, mantidas explicitamente sem suposição silenciosa:

1. **Data corrente:** falta definir qual fuso ou relógio determina se a data está no futuro, especialmente com frontend e backend em regiões diferentes.
2. **Limite monetário:** a escala de duas casas está definida, mas ainda faltam a precisão total da coluna `NUMERIC` e o maior valor aceito pela API.
3. **Deploy:** faltam os provedores definitivos, as URLs e o serviço PostgreSQL de produção.
4. **CORS em desenvolvimento:** produção permitirá somente a origem do frontend, mas as origens autorizadas no ambiente de desenvolvimento ainda não foram definidas.
5. **Requisitos mensuráveis:** não foram fornecidas metas de desempenho, volume, navegadores específicos, acessibilidade, responsividade, disponibilidade ou retenção/backup.

Nenhuma dessas lacunas autoriza adicionar autenticação, relatórios, categorias configuráveis, paginação ou qualquer outra funcionalidade indicada como fora de escopo.
