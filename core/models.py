"""Definição das 'tabelas' (abas da planilha Google) e colunas."""

SHEETS = {
    "Clientes": ["id", "nome", "contato", "observacoes", "data_cadastro"],
    "Categorias": ["id", "nome"],
    "Projetos": ["id", "cliente_id", "nome_projeto", "descricao", "data_criacao"],
    "Artes": [
        "id", "projeto_id", "cliente_id", "categoria_id",
        "descricao", "valor", "data", "hora",
    ],
    "Pagamentos": [
        "id", "cliente_id", "projeto_id", "valor",
        "forma_pagamento", "data", "hora", "observacoes",
    ],
    "Descontos": [
        "id", "cliente_id", "projeto_id", "valor",
        "motivo", "data", "hora",
    ],
}

FORMAS_PAGAMENTO = ["Pix", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "Transferência", "Boleto", "Outro"]
