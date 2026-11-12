from dominio.objetos_de_valor.ferramenta import NomeFerramenta
from dominio.objetos_de_valor.playbook import Playbook


def playbook_solar() -> Playbook:
    return Playbook(
        nome="energia-solar-residencial",
        objetivo="Qualificar lead e agendar visita técnica.",
        perguntas=(
            "Qual o nome e a cidade?",
            "O imóvel é próprio ou alugado?",
            "É casa ou apartamento?",
            "Qual o valor médio da conta de luz?",
            "Tem interesse em financiar o sistema de energia solar ou prefere pagar à vista?",
        ),
        criterios_de_qualificacao=(
            "Imóvel próprio, casa, conta acima de R$ 250 e cidade atendida.",
        ),
        regras=("Nunca prometer economia exata.",),
        ferramentas=(
            NomeFerramenta.MOVER_ESTAGIO,
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
        criterios_de_qualificacao=("Data futura e quantidade minima de 20 unidades.",),
        regras=("Nunca confirmar preco final.",),
        ferramentas=(
            NomeFerramenta.MOVER_ESTAGIO,
            NomeFerramenta.NOTIFICAR_EQUIPE,
            NomeFerramenta.TRANSFERIR_HUMANO,
            NomeFerramenta.CONSULTAR_AGENDA,
            NomeFerramenta.MARCAR_AGENDA,
        ),
    )
