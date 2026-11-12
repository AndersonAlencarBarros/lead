from dominio.objetos_de_valor.ferramenta import NomeFerramenta
from dominio.objetos_de_valor.playbook import CampoDaFicha, Playbook, TipoCampo


def playbook_solar() -> Playbook:
    return Playbook(
        nome="energia-solar-residencial",
        objetivo="Qualificar lead e agendar visita técnica.",
        perguntas=(
            "Qual o nome e a cidade?",
            "O imóvel é próprio ou alugado?",
            "É casa ou apartamento?",
            "Qual o valor médio da conta de luz?",
            "Tem interesse em financiar ou pagar à vista?",
        ),
        campos=(
            CampoDaFicha("nome", "Nome do lead", TipoCampo.TEXTO),
            CampoDaFicha("cidade", "Cidade do imóvel", TipoCampo.TEXTO),
            CampoDaFicha(
                "imovel",
                "Imóvel próprio ou alugado",
                TipoCampo.OPCAO,
                ("proprio", "alugado"),
            ),
            CampoDaFicha(
                "tipo_imovel",
                "Casa ou apartamento",
                TipoCampo.OPCAO,
                ("casa", "apartamento"),
            ),
            CampoDaFicha(
                "valor_conta",
                "Conta de luz mensal",
                TipoCampo.NUMERO,
            ),
            CampoDaFicha(
                "financiamento",
                "Forma de pagamento",
                TipoCampo.OPCAO,
                ("financiado", "a_vista"),
            ),
        ),
        criterios_de_qualificacao=(
            "Imóvel próprio, casa, conta acima de R$ 250 e cidade atendida.",
        ),
        regras=("Nunca prometer economia exata.",),
        ferramentas=(
            NomeFerramenta.ADICIONAR_TAG,
            NomeFerramenta.MOVER_ESTAGIO,
            NomeFerramenta.ATUALIZAR_FICHA,
            NomeFerramenta.NOTIFICAR_EQUIPE,
            NomeFerramenta.TRANSFERIR_HUMANO,
            NomeFerramenta.CONSULTAR_AGENDA,
            NomeFerramenta.MARCAR_AGENDA,
        ),
    )


def playbook_confeitaria() -> Playbook:
    return Playbook(
        nome="confeitaria-sob-encomenda",
        objetivo="Qualificar encomenda e confirmar data.",
        perguntas=(
            "Qual o nome e a cidade?",
            "Qual produto e quantidade?",
            "Qual a data do evento?",
        ),
        campos=(
            CampoDaFicha("nome", "Nome do lead", TipoCampo.TEXTO),
            CampoDaFicha("cidade", "Cidade do lead", TipoCampo.TEXTO),
            CampoDaFicha(
                "produto",
                "Produto encomendado",
                TipoCampo.OPCAO,
                ("bolo", "salgado", "doces"),
            ),
            CampoDaFicha("quantidade", "Quantidade", TipoCampo.NUMERO),
            CampoDaFicha("data_evento", "Data do evento", TipoCampo.DATA),
        ),
        criterios_de_qualificacao=("Data futura e quantidade minima de 20 unidades.",),
        regras=("Nunca confirmar preco final.",),
        ferramentas=(
            NomeFerramenta.ADICIONAR_TAG,
            NomeFerramenta.MOVER_ESTAGIO,
            NomeFerramenta.ATUALIZAR_FICHA,
            NomeFerramenta.NOTIFICAR_EQUIPE,
            NomeFerramenta.TRANSFERIR_HUMANO,
            NomeFerramenta.CONSULTAR_AGENDA,
            NomeFerramenta.MARCAR_AGENDA,
        ),
    )
