# ✨ Infinity Designer

Sistema de gestão de clientes freelancer (design/artes): projetos, artes, pagamentos,
descontos, cupons e relatórios — banco de dados em Google Planilhas, interface em Streamlit.

## Estrutura
```
sistema -> cliente -> projeto -> artes/alterações do projeto
```

## 1. Configurar o Google Sheets (banco de dados)

1. Acesse https://console.cloud.google.com/ e crie um projeto.
2. Ative as APIs **Google Sheets API** e **Google Drive API**.
3. Vá em "Credenciais" → "Criar credenciais" → **Conta de serviço**.
4. Crie uma chave para essa conta de serviço em formato **JSON** e baixe o arquivo.
5. Copie o e-mail da conta de serviço (algo como `xxx@xxx.iam.gserviceaccount.com`).
6. O app cria a planilha automaticamente na primeira execução (usando a API), mas
   é preciso que a conta de serviço tenha permissão — se preferir, crie a planilha
   manualmente no Google Drive com o nome definido em `spreadsheet_name` e
   compartilhe-a (permissão de Editor) com o e-mail da conta de serviço.

## 2. Configurar as credenciais no projeto

Copie `/.streamlit/secrets.toml.example` para `/.streamlit/secrets.toml` e preencha
com os dados do JSON baixado (`type`, `project_id`, `private_key`, `client_email` etc.)
e o nome desejado para a planilha em `spreadsheet_name`.

**Nunca suba o `secrets.toml` real para o GitHub** (já está no `.gitignore`).

## 3. Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 4. Subir para o GitHub

```bash
git init
git add .
git commit -m "Infinity Designer - versão inicial"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/infinity-designer.git
git push -u origin main
```

## 5. Deploy (Streamlit Community Cloud)

1. Acesse https://share.streamlit.io e conecte seu repositório do GitHub.
2. Aponte para o arquivo `app.py`.
3. Em "Settings" → "Secrets", cole o conteúdo do seu `secrets.toml` real
   (o mesmo formato do `secrets.toml.example`, preenchido).
4. Deploy — pronto.

## Páginas do sistema

- **Dashboard (app.py)**: totais gerais, gráfico de pizza (a receber / pago / descontos) e gráfico de vendas x pagamentos por mês.
- **Categorias**: painel admin para criar/renomear/excluir categorias de arte (motion, identidade visual, logos, etc.) livremente.
- **Clientes**: cadastro de clientes; dentro do perfil de cada cliente — projetos, artes (com valor editável por categoria), pagamentos (abatem o saldo devedor automaticamente), descontos, histórico completo de movimentações, gráfico individual, e geração de cupom (simples/completo) e relatório (PDF/TXT) para download.
- **Finanças**: relatórios diário, semanal, mensal e anual de vendas x pagamentos.
- **Relatórios**: visão consolidada de todos os clientes + download de relatório individual.

## Observações

- Todo pagamento é abatido automaticamente do saldo devedor do cliente (saldo = total vendido − pago − descontos).
- O cupom **simples** mostra apenas valor total, quantidade de artes, valor e categoria de cada arte.
- O cupom **completo** inclui tudo isso + o relatório completo de movimentações (com datas, horas e formas de pagamento).
