"""Definição das 'tabelas' (abas da planilha Google) e colunas."""

SHEETS = {
    "Clientes": ["id", "nome", "contato", "observacoes", "data_cadastro"],
    "Categorias": ["id", "nome"],
    "Programas": ["id", "nome"],
    "Projetos": ["id", "cliente_id", "nome_projeto", "descricao", "data_criacao", "finalizado"],
    "Artes": [
        "id", "projeto_id", "cliente_id", "categoria_id",
        "descricao", "valor", "data", "hora",
        # colunas novas ficam no final para não desalinhar dados já existentes
        "programas", "prazo_entrega", "anotacoes",
        "entregue", "desistencia",
    ],
    "Pagamentos": [
        "id", "cliente_id", "projeto_id", "valor",
        "forma_pagamento", "data", "hora", "observacoes",
    ],
    "Descontos": [
        "id", "cliente_id", "projeto_id", "valor",
        "motivo", "data", "hora",
    ],
    "Configuracoes": [
        "id", "salario_desejado", "valor_computador",
        "custos_extras", "horas_trabalho_mes",
    ],
    "Orcamentos": [
        "id", "tipo", "nome_orcamento", "cliente_id", "itens_json",
        "desconto_pct", "tempo_total_horas", "valor_hora_usado",
        "valor_bruto", "valor_final", "data", "hora", "observacoes",
    ],
}

FORMAS_PAGAMENTO = ["Pix", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "Transferência", "Boleto", "Outro"]
PROGRAMAS_PADRAO = ["CorelDRAW", "Photoshop", "After Effects", "Illustrator", "Premiere Pro", "Figma"]

CONFIG_PADRAO = {
    "salario_desejado": 1600.0,
    "valor_computador": 2000.0,
    "custos_extras": 145.0,
    "horas_trabalho_mes": 80.0,
}
