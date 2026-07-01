from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd

from app import db


LOCAL_QUESTIONS = [
    {
        "match": "Lei Maria da Penha",
        "statement": "À luz da Lei Maria da Penha, a violência doméstica e familiar contra a mulher configura uma das formas de violação dos direitos humanos.",
        "options": {
            "A": "A assertiva está correta, pois a lei expressamente reconhece essa violência como violação de direitos humanos.",
            "B": "A assertiva está incorreta, pois a lei trata apenas de infrações penais comuns.",
            "C": "A assertiva está incorreta, pois a lei somente protege mulheres em relação conjugal atual.",
            "D": "A assertiva está correta apenas quando houver lesão corporal grave.",
            "E": "A assertiva está incorreta, pois a proteção depende de representação judicial prévia.",
        },
        "answer": "A",
        "justification": "A Lei Federal nº 11.340/2006, art. 6º, dispõe que a violência doméstica e familiar contra a mulher constitui uma das formas de violação dos direitos humanos.",
        "difficulty": 2,
    },
    {
        "match": "LDB",
        "statement": "Nos termos da LDB, a educação escolar compõe-se exclusivamente da educação básica, formada pela educação infantil, ensino fundamental e ensino médio.",
        "options": {
            "A": "Correto, pois a LDB restringe a educação escolar à educação básica.",
            "B": "Errado, pois a educação escolar compõe-se de educação básica e educação superior.",
            "C": "Correto, pois a educação superior é regulada apenas por normas administrativas do MEC.",
            "D": "Errado, pois a educação básica inclui também a pós-graduação.",
            "E": "Correto, desde que se trate de instituições públicas.",
        },
        "answer": "B",
        "justification": "A LDB, Lei nº 9.394/1996, art. 21, estabelece que a educação escolar compõe-se de educação básica e educação superior.",
        "difficulty": 3,
    },
    {
        "match": "Educação na Constituição Federal de 1988",
        "statement": "A Constituição Federal estabelece que a educação é direito de todos e dever exclusivo da família, cabendo ao Estado atuação apenas suplementar.",
        "options": {
            "A": "Correto, pois a família é a principal responsável pela educação.",
            "B": "Errado, pois a educação é direito de todos e dever do Estado e da família.",
            "C": "Correto, pois o Estado atua apenas no ensino superior.",
            "D": "Errado, pois a educação é dever exclusivo do Estado.",
            "E": "Correto, salvo no caso de educação infantil.",
        },
        "answer": "B",
        "justification": "O art. 205 da Constituição Federal afirma que a educação é direito de todos e dever do Estado e da família.",
        "difficulty": 2,
    },
    {
        "match": "CRAS, CREAS",
        "statement": "No SUAS, CRAS e CREAS possuem a mesma função, ambos voltados exclusivamente à proteção social especial de alta complexidade.",
        "options": {
            "A": "Correto, pois ambos executam acolhimento institucional.",
            "B": "Errado, pois o CRAS é referência da proteção social básica e o CREAS atua na proteção social especial.",
            "C": "Correto, pois a diferença entre CRAS e CREAS é apenas territorial.",
            "D": "Errado, pois o CREAS atua somente na saúde mental.",
            "E": "Correto, desde que no âmbito municipal.",
        },
        "answer": "B",
        "justification": "No SUAS, o CRAS é unidade de referência da proteção social básica; o CREAS é unidade de referência da proteção social especial, especialmente em violações de direitos.",
        "difficulty": 3,
    },
    {
        "match": "ECA",
        "statement": "O ECA adota a doutrina da proteção integral, reconhecendo crianças e adolescentes como sujeitos de direitos em condição peculiar de desenvolvimento.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois o ECA adota a doutrina da situação irregular.",
            "C": "Errado, pois adolescentes não são abrangidos pela proteção integral.",
            "D": "Correto apenas para crianças de até 12 anos incompletos.",
            "E": "Errado, pois a proteção integral depende de decisão judicial.",
        },
        "answer": "A",
        "justification": "O ECA é estruturado pela doutrina da proteção integral, em consonância com o art. 227 da Constituição Federal.",
        "difficulty": 2,
    },
    {
        "match": "gestão democrática",
        "statement": "A gestão democrática do ensino público é princípio constitucional e também consta entre os princípios da LDB.",
        "options": {
            "A": "Errado, pois é apenas diretriz administrativa interna.",
            "B": "Correto, conforme a Constituição Federal e a LDB.",
            "C": "Errado, pois a LDB prevê gestão democrática somente para escolas privadas.",
            "D": "Correto apenas para universidades federais.",
            "E": "Errado, pois o princípio foi revogado pela LDB.",
        },
        "answer": "B",
        "justification": "A gestão democrática do ensino público aparece no art. 206, VI, da Constituição Federal e no art. 3º, VIII, da LDB.",
        "difficulty": 3,
    },
    {
        "match": "Pessoa idosa",
        "statement": "O Estatuto da Pessoa Idosa considera pessoa idosa aquela com idade igual ou superior a 60 anos.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois o marco legal é 65 anos.",
            "C": "Errado, pois o marco legal é 70 anos.",
            "D": "Correto apenas para fins previdenciários.",
            "E": "Errado, pois a idade varia conforme renda familiar.",
        },
        "answer": "A",
        "justification": "A Lei nº 10.741/2003, art. 1º, destina-se a regular os direitos assegurados às pessoas com idade igual ou superior a 60 anos.",
        "difficulty": 1,
    },
    {
        "match": "CadÚnico",
        "statement": "O Cadastro Único é instrumento utilizado para identificação e caracterização socioeconômica das famílias brasileiras de baixa renda.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois serve apenas para famílias em situação de acolhimento institucional.",
            "C": "Errado, pois é instrumento exclusivo da política educacional.",
            "D": "Correto apenas para famílias residentes no Distrito Federal.",
            "E": "Errado, pois não se relaciona a programas sociais.",
        },
        "answer": "A",
        "justification": "O CadÚnico é instrumento de identificação e caracterização socioeconômica de famílias de baixa renda, utilizado para acesso a políticas e programas sociais.",
        "difficulty": 2,
    },
    {
        "match": "intersetorial",
        "statement": "A atuação pedagógica no SUAS pode demandar articulação intersetorial com assistência social, educação, saúde e justiça.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois o pedagogo deve atuar isoladamente no equipamento socioassistencial.",
            "C": "Errado, pois a articulação com saúde e justiça é vedada ao SUAS.",
            "D": "Correto apenas em unidades escolares.",
            "E": "Errado, pois intersetorialidade é conceito exclusivo da política de saúde.",
        },
        "answer": "A",
        "justification": "O edital de Pedagogia prevê trabalho em rede e articulação intersetorial envolvendo assistência social, educação, saúde e justiça.",
        "difficulty": 2,
    },
    {
        "match": "Educação social",
        "statement": "A pedagogia social, no contexto do edital, relaciona a educação à inclusão social e à garantia de direitos, especialmente em contextos de vulnerabilidade.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois pedagogia social trata apenas de alfabetização formal.",
            "C": "Errado, pois exclui contextos não escolares.",
            "D": "Correto apenas no ensino superior.",
            "E": "Errado, pois não possui relação com garantia de direitos.",
        },
        "answer": "A",
        "justification": "O conteúdo específico do edital menciona educação social e pedagogia social como instrumento de inclusão e garantia de direitos.",
        "difficulty": 2,
    },
    {
        "match": "Compreensão e interpretação",
        "statement": "Em interpretação de textos, informações pressupostas são aquelas explicitamente negadas pelo autor, embora o leitor possa inferi-las pelo contexto.",
        "options": {
            "A": "Correto, pois pressuposto é sempre uma negação explícita.",
            "B": "Errado, pois pressupostos são informações implícitas assumidas como base do enunciado.",
            "C": "Correto, pois toda inferência depende de contradição textual.",
            "D": "Errado, pois pressupostos existem apenas em textos literários.",
            "E": "Correto apenas em textos injuntivos.",
        },
        "answer": "B",
        "justification": "Pressuposto é conteúdo implícito acionado por marcas linguísticas e tomado como conhecido ou aceito; não é informação explicitamente negada.",
        "difficulty": 3,
    },
    {
        "match": "acentuação",
        "statement": "As palavras 'herói', 'chapéu' e 'anéis' são acentuadas por apresentarem ditongos abertos tônicos em posição final ou seguidos de s.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois ditongos abertos nunca são acentuados.",
            "C": "Errado, pois apenas proparoxítonas recebem acento.",
            "D": "Correto apenas para palavras oxítonas terminadas em a.",
            "E": "Errado, pois o acento decorre de hiato.",
        },
        "answer": "A",
        "justification": "Ditongos abertos tônicos em palavras oxítonas terminadas em éi, éu e ói, seguidos ou não de s, recebem acento gráfico.",
        "difficulty": 2,
    },
    {
        "match": "crase",
        "statement": "No trecho 'o relatório foi encaminhado à equipe técnica', o emprego da crase justifica-se pela fusão da preposição a com o artigo feminino a.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois não há crase antes de palavra feminina.",
            "C": "Errado, pois a crase só ocorre antes de verbo.",
            "D": "Correto apenas quando a palavra seguinte estiver no plural.",
            "E": "Errado, pois o verbo encaminhar não admite preposição.",
        },
        "answer": "A",
        "justification": "Quem encaminha encaminha algo a alguém; diante de 'equipe', há artigo feminino 'a'. Ocorre fusão: a + a = à.",
        "difficulty": 3,
    },
    {
        "match": "Concordância verbal",
        "statement": "Na frase 'Fazem dez anos que o serviço foi criado', a forma verbal 'fazem' está adequada à norma-padrão por concordar com 'dez anos'.",
        "options": {
            "A": "Correto, pois o verbo fazer concorda com o numeral.",
            "B": "Errado, pois o verbo fazer, indicando tempo decorrido, é impessoal e deve ficar no singular.",
            "C": "Correto apenas se o sujeito estiver oculto.",
            "D": "Errado, pois a frase exige obrigatoriamente o verbo haver.",
            "E": "Correto apenas em linguagem jurídica.",
        },
        "answer": "B",
        "justification": "O verbo fazer, quando indica tempo decorrido, é impessoal e permanece na terceira pessoa do singular: 'Faz dez anos'.",
        "difficulty": 3,
    },
    {
        "match": "Coesão textual",
        "statement": "Conectores como 'portanto', 'logo' e 'assim' costumam introduzir ideia de conclusão em relação ao segmento anterior.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois esses conectores indicam oposição.",
            "C": "Errado, pois conectores não estabelecem relações semânticas.",
            "D": "Correto apenas se estiverem no início absoluto do texto.",
            "E": "Errado, pois são marcas exclusivas de oralidade.",
        },
        "answer": "A",
        "justification": "Na coesão sequencial, 'portanto', 'logo' e 'assim' são conectores conclusivos ou consecutivos, conforme o contexto.",
        "difficulty": 1,
    },
    {
        "match": "LOAS",
        "statement": "A assistência social, conforme a LOAS, é política de seguridade social não contributiva, que provê mínimos sociais.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois a assistência social exige contribuição previdenciária prévia.",
            "C": "Errado, pois a LOAS trata apenas de educação básica.",
            "D": "Correto apenas para trabalhadores formais.",
            "E": "Errado, pois mínimos sociais são matéria exclusiva da saúde.",
        },
        "answer": "A",
        "justification": "A LOAS define a assistência social como política de seguridade social não contributiva, voltada a prover mínimos sociais.",
        "difficulty": 2,
    },
    {
        "match": "Proteção Social Básica",
        "statement": "A proteção social básica tem caráter preventivo e busca fortalecer vínculos familiares e comunitários antes do agravamento de riscos sociais.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois a proteção básica só atua após violação grave de direitos.",
            "C": "Errado, pois fortalecimento de vínculos é atribuição exclusiva do Judiciário.",
            "D": "Correto apenas na proteção de alta complexidade.",
            "E": "Errado, pois o SUAS não trabalha com prevenção.",
        },
        "answer": "A",
        "justification": "No SUAS, a proteção social básica tem foco preventivo, territorial e de fortalecimento de vínculos familiares e comunitários.",
        "difficulty": 2,
    },
    {
        "match": "NOB/SUAS",
        "statement": "A NOB/SUAS organiza aspectos da gestão do SUAS, incluindo responsabilidades dos entes federativos e parâmetros de cofinanciamento.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois a NOB/SUAS disciplina somente currículo escolar.",
            "C": "Errado, pois o SUAS não envolve repartição de responsabilidades federativas.",
            "D": "Correto apenas para entidades privadas sem fins lucrativos.",
            "E": "Errado, pois cofinanciamento é tema alheio à assistência social.",
        },
        "answer": "A",
        "justification": "A NOB/SUAS trata da organização e gestão do SUAS, abrangendo responsabilidades, pactuação, cofinanciamento e gestão do trabalho.",
        "difficulty": 3,
    },
    {
        "match": "Convivência familiar",
        "statement": "No ECA, a convivência familiar e comunitária é direito da criança e do adolescente, não se limitando à permanência em família natural.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois o ECA não prevê convivência comunitária.",
            "C": "Errado, pois adoção exclui proteção integral.",
            "D": "Correto apenas para adolescentes maiores de 16 anos.",
            "E": "Errado, pois esse direito depende de capacidade civil.",
        },
        "answer": "A",
        "justification": "O ECA assegura o direito à convivência familiar e comunitária, com regras sobre família natural, extensa, substituta, acolhimento e adoção.",
        "difficulty": 3,
    },
    {
        "match": "SINASE",
        "statement": "O SINASE relaciona-se à execução de medidas socioeducativas destinadas a adolescentes a quem se atribua autoria de ato infracional.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois o SINASE rege penas criminais de adultos.",
            "C": "Errado, pois medidas socioeducativas são aplicadas a crianças de qualquer idade.",
            "D": "Correto apenas para crimes militares.",
            "E": "Errado, pois ato infracional é conceito de direito eleitoral.",
        },
        "answer": "A",
        "justification": "O SINASE estrutura a política de atendimento e execução de medidas socioeducativas aplicáveis a adolescentes autores de ato infracional.",
        "difficulty": 2,
    },
    {
        "match": "LBI",
        "statement": "A Lei Brasileira de Inclusão adota a lógica de barreiras e acessibilidade, buscando assegurar participação social da pessoa com deficiência em igualdade de condições.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois a LBI restringe-se à previdência social.",
            "C": "Errado, pois acessibilidade é tema exclusivamente arquitetônico.",
            "D": "Correto apenas para pessoas com deficiência física.",
            "E": "Errado, pois a LBI substitui a Constituição Federal.",
        },
        "answer": "A",
        "justification": "A LBI trabalha com eliminação de barreiras, acessibilidade e participação plena e efetiva da pessoa com deficiência na sociedade.",
        "difficulty": 3,
    },
    {
        "match": "População em situação de rua",
        "statement": "A política para população em situação de rua demanda abordagem intersetorial, pois envolve assistência social, saúde, trabalho, moradia, segurança alimentar e direitos humanos.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois a matéria é exclusiva da segurança pública.",
            "C": "Errado, pois a política veda articulação entre serviços.",
            "D": "Correto apenas para capitais com mais de um milhão de habitantes.",
            "E": "Errado, pois população em situação de rua não é público de políticas sociais.",
        },
        "answer": "A",
        "justification": "A atenção à população em situação de rua exige articulação de políticas públicas e reconhecimento de múltiplas vulnerabilidades.",
        "difficulty": 2,
    },
    {
        "match": "RIDE",
        "statement": "A RIDE do Distrito Federal e Entorno foi instituída por lei complementar federal e envolve integração regional entre o DF e municípios do entorno.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois a RIDE é órgão interno da Câmara Legislativa.",
            "C": "Errado, pois abrange apenas regiões administrativas do DF.",
            "D": "Correto apenas para fins eleitorais.",
            "E": "Errado, pois não há previsão federal sobre a RIDE.",
        },
        "answer": "A",
        "justification": "O edital cobra a RIDE instituída pela Lei Complementar Federal nº 94/1998 e regulamentada por decreto federal.",
        "difficulty": 2,
    },
    {
        "match": "Lei Complementar 840",
        "statement": "A Lei Complementar distrital nº 840/2011 disciplina regime jurídico dos servidores públicos civis do Distrito Federal, incluindo deveres e regime disciplinar.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois a norma trata apenas de licitações.",
            "C": "Errado, pois servidores distritais são regidos exclusivamente pela CLT.",
            "D": "Correto apenas para empregados de empresas privadas.",
            "E": "Errado, pois regime disciplinar não consta do edital.",
        },
        "answer": "A",
        "justification": "O edital cobra a LC nº 840/2011 em disposições preliminares, deveres, regime disciplinar e processos de apuração.",
        "difficulty": 2,
    },
    {
        "match": "Plano Distrital de Política para Mulheres",
        "statement": "O Plano Distrital de Política para Mulheres deve ser estudado como política pública transversal, e não como conteúdo restrito ao direito penal.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois o plano só trata de tipificação criminal.",
            "C": "Errado, pois transversalidade é vedada em políticas públicas.",
            "D": "Correto apenas se vinculado à política tributária.",
            "E": "Errado, pois o edital não prevê política para mulheres.",
        },
        "answer": "A",
        "justification": "O edital cobra o PDPM como conteúdo próprio dentro de conhecimentos do DF, política para mulheres e legislação.",
        "difficulty": 2,
    },
    {
        "match": "Planejamento participativo",
        "statement": "No planejamento participativo, registro, monitoramento e avaliação são etapas dispensáveis quando a atividade socioeducativa é executada em grupo.",
        "options": {
            "A": "Correto, pois oficinas dispensam avaliação.",
            "B": "Errado, pois o edital inclui elaboração, execução, registro, monitoramento e avaliação de projetos socioeducativos.",
            "C": "Correto apenas em atividades comunitárias.",
            "D": "Errado, pois planejamento participativo exclui execução.",
            "E": "Correto quando houver equipe multidisciplinar.",
        },
        "answer": "B",
        "justification": "O conteúdo específico cobra expressamente as fases de elaboração, execução, registro, monitoramento e avaliação de projetos socioeducativos.",
        "difficulty": 2,
    },
    {
        "match": "Metodologias participativas",
        "statement": "Oficinas e práticas coletivas podem ser usadas como metodologias participativas em atividades socioeducativas no SUAS.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois oficinas são incompatíveis com educação em grupo.",
            "C": "Errado, pois metodologia participativa exige aula expositiva individual.",
            "D": "Correto apenas em escolas regulares.",
            "E": "Errado, pois o edital não prevê práticas coletivas.",
        },
        "answer": "A",
        "justification": "O edital menciona metodologias participativas, educação em grupo, oficinas, atividades socioeducativas e práticas coletivas.",
        "difficulty": 1,
    },
    {
        "match": "negligência",
        "statement": "Situações de negligência, abandono, institucionalização e exclusão social exigem intervenção pedagógica sensível ao contexto familiar, territorial e de direitos.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois a pedagogia não atua em contextos não escolares.",
            "C": "Errado, pois institucionalização exclui processo educativo.",
            "D": "Correto apenas em instituições privadas de ensino.",
            "E": "Errado, pois o tema não integra conhecimentos específicos.",
        },
        "answer": "A",
        "justification": "O edital cobra processos educativos com famílias e indivíduos em situações de negligência, abandono, institucionalização e exclusão social.",
        "difficulty": 2,
    },
    {
        "match": "adolescentes em conflito",
        "statement": "A atuação pedagógica com adolescentes em conflito com a lei deve ser compreendida apenas como punição disciplinar, sem finalidade socioeducativa.",
        "options": {
            "A": "Correto, pois a medida socioeducativa não tem dimensão educativa.",
            "B": "Errado, pois o edital cobra atuação pedagógica em contextos de atendimento a adolescentes em conflito com a lei.",
            "C": "Correto apenas nos casos de internação.",
            "D": "Errado, pois adolescentes em conflito com a lei são tema exclusivo de previdência.",
            "E": "Correto apenas quando houver sentença penal condenatória.",
        },
        "answer": "B",
        "justification": "O conteúdo específico prevê atuação pedagógica nesses contextos, com perspectiva socioeducativa e de responsabilização adequada à adolescência.",
        "difficulty": 3,
    },
    {
        "match": "Educação para cidadania",
        "statement": "Educação para cidadania, autonomia e protagonismo social são objetivos coerentes com práticas socioeducativas em contextos de vulnerabilidade.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois autonomia é incompatível com assistência social.",
            "C": "Errado, pois protagonismo social é tema exclusivo de administração financeira.",
            "D": "Correto apenas em educação superior.",
            "E": "Errado, pois o edital limita a atuação pedagógica à alfabetização.",
        },
        "answer": "A",
        "justification": "O edital inclui educação para cidadania, autonomia e protagonismo social entre os conteúdos específicos.",
        "difficulty": 1,
    },
    {
        "match": "Educação popular",
        "statement": "A educação popular valoriza o diálogo, a experiência dos sujeitos e a leitura crítica da realidade, sendo compatível com abordagens emancipatórias.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois educação popular é sinônimo de ensino privado.",
            "C": "Errado, pois abordagem emancipatória elimina participação dos sujeitos.",
            "D": "Correto apenas no ensino militar.",
            "E": "Errado, pois o edital exclui educação não formal.",
        },
        "answer": "A",
        "justification": "O edital cobra concepções críticas, histórico-dialéticas e emancipatórias, além de educação popular, formal, não formal e informal.",
        "difficulty": 3,
    },
    {
        "match": "Gestão democrática",
        "statement": "A gestão democrática da educação pública envolve participação e não se confunde com centralização absoluta das decisões pela direção escolar.",
        "options": {
            "A": "Correto.",
            "B": "Errado, pois gestão democrática significa ausência de normas.",
            "C": "Errado, pois a LDB veda participação da comunidade escolar.",
            "D": "Correto apenas no ensino privado confessional.",
            "E": "Errado, pois a Constituição não trata de gestão democrática.",
        },
        "answer": "A",
        "justification": "A gestão democrática é princípio constitucional e legal para o ensino público, com participação conforme a legislação dos sistemas de ensino.",
        "difficulty": 2,
    },
]


def seed_question_bank(concurso_id: int) -> int:
    _delete_orphan_questions()
    topics = db.fetch_df("SELECT id, discipline, topic FROM topics WHERE concurso_id = ?", (concurso_id,))
    created = 0
    for item in LOCAL_QUESTIONS:
        match = str(item["match"]).lower()
        topic_text = topics["topic"].str.lower()
        discipline_text = topics["discipline"].str.lower()
        candidates = topics[topic_text.str.contains(match, regex=False, na=False)]
        if candidates.empty:
            candidates = topics[topic_text.str.contains(match.split()[0], regex=False, na=False)]
        if candidates.empty and item.get("discipline_contains"):
            discipline_match = str(item["discipline_contains"]).lower()
            candidates = topics[discipline_text.str.contains(discipline_match, regex=False, na=False)]
        if candidates.empty:
            continue
        topic_id = int(candidates.iloc[0]["id"])
        existing = db.fetch_one(
            "SELECT id FROM question_bank WHERE concurso_id = ? AND topic_id = ? AND statement = ?",
            (concurso_id, topic_id, item["statement"]),
        )
        if existing:
            continue
        options = item["options"]
        db.execute(
            """
            INSERT INTO question_bank
            (concurso_id, topic_id, source, mode, statement, option_a, option_b, option_c, option_d, option_e,
             correct_answer, justification, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                concurso_id,
                topic_id,
                "local_seed",
                "multipla_escolha",
                item["statement"],
                options.get("A"),
                options.get("B"),
                options.get("C"),
                options.get("D"),
                options.get("E"),
                item["answer"],
                item["justification"],
                item["difficulty"],
            ),
        )
        created += 1
    created += _seed_missing_topic_questions(concurso_id)
    return created


def _delete_orphan_questions() -> None:
    db.execute(
        """
        DELETE FROM question_attempts
        WHERE question_id IN (
            SELECT qb.id
            FROM question_bank qb
            LEFT JOIN topics t ON t.id = qb.topic_id
            WHERE t.id IS NULL
        )
        """
    )
    db.execute(
        """
        DELETE FROM question_bank
        WHERE id IN (
            SELECT qb.id
            FROM question_bank qb
            LEFT JOIN topics t ON t.id = qb.topic_id
            WHERE t.id IS NULL
        )
        """
    )


def _seed_missing_topic_questions(concurso_id: int) -> int:
    missing = db.fetch_df(
        """
        SELECT t.id, t.discipline, t.topic, t.difficulty
        FROM topics t
        LEFT JOIN question_bank qb ON qb.topic_id = t.id
        WHERE t.concurso_id = ?
        GROUP BY t.id
        HAVING COUNT(qb.id) = 0
        ORDER BY t.question_count DESC, t.priority DESC, t.topic
        """,
        (concurso_id,),
    )
    created = 0
    for row in missing.itertuples(index=False):
        question = _baseline_question(str(row.discipline), str(row.topic), int(row.difficulty))
        db.execute(
            """
            INSERT INTO question_bank
            (concurso_id, topic_id, source, mode, statement, option_a, option_b, option_c, option_d, option_e,
             correct_answer, justification, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                concurso_id,
                int(row.id),
                "local_baseline",
                "multipla_escolha",
                question["statement"],
                question["options"]["A"],
                question["options"]["B"],
                question["options"]["C"],
                question["options"]["D"],
                question["options"]["E"],
                question["answer"],
                question["justification"],
                question["difficulty"],
            ),
        )
        created += 1
    return created


def _baseline_question(discipline: str, topic: str, difficulty: int) -> dict[str, Any]:
    if discipline == "Língua Portuguesa":
        return {
            "statement": f"No estudo de {topic}, assinale a alternativa que representa uma abordagem adequada para prova de múltipla escolha.",
            "options": {
                "A": "Considerar apenas palavras isoladas, sem observar contexto, coesão e finalidade comunicativa.",
                "B": "Ignorar marcas gramaticais quando elas alterarem sentido, referência ou relação sintática.",
                "C": "Analisar o enunciado pelo contexto, pelas marcas linguísticas e pela norma-padrão quando cobrada.",
                "D": "Escolher a alternativa mais longa sempre que houver dúvida interpretativa.",
                "E": "Tratar toda reescrita como equivalente, ainda que mude sentido ou correção gramatical.",
            },
            "answer": "C",
            "justification": "Em Língua Portuguesa, a banca costuma cobrar sentido, correção gramatical, coesão e reescrita com atenção a mudanças sutis no enunciado.",
            "difficulty": max(2, min(difficulty, 4)),
        }
    if "Pedagogia" in discipline:
        return {
            "statement": f"Considerando o conteúdo de {topic}, assinale a alternativa mais adequada ao cargo de Pedagoga no SUAS.",
            "options": {
                "A": "A atuação pedagógica deve ficar restrita à sala de aula formal e desvinculada da rede socioassistencial.",
                "B": "A prática socioeducativa deve articular planejamento, participação, território, vínculos e garantia de direitos.",
                "C": "O trabalho pedagógico no SUAS dispensa registro, monitoramento e avaliação dos projetos.",
                "D": "A educação não formal é incompatível com contextos de vulnerabilidade social.",
                "E": "A interdisciplinaridade afasta a necessidade de diálogo com família, comunidade e rede de serviços.",
            },
            "answer": "B",
            "justification": "O edital de Pedagogia enfatiza prática socioeducativa, planejamento participativo, trabalho em rede, território, vínculos e garantia de direitos.",
            "difficulty": max(2, min(difficulty, 4)),
        }
    return {
        "statement": f"Acerca de {topic}, assinale a alternativa compatível com a preparação para a banca Quadrix.",
        "options": {
            "A": "O estudo deve priorizar leitura literal, conceitos centrais e atenção a pequenas trocas de palavras no enunciado.",
            "B": "Normas, princípios e diretrizes devem ser ignorados quando aparecerem com redação literal.",
            "C": "Conceitos de proteção social, direitos e políticas públicas são sempre sinônimos e podem ser tratados como equivalentes.",
            "D": "A alternativa correta costuma depender apenas de memorização de números, sem compreensão do instituto cobrado.",
            "E": "Conteúdos de legislação e políticas sociais não exigem revisão espaçada nem treino por questões.",
        },
        "answer": "A",
        "justification": "Para conteúdos normativos e de políticas públicas, a Quadrix tende a cobrar literalidade, conceitos diretos e pegadinhas de substituição terminológica.",
        "difficulty": max(2, min(difficulty, 4)),
    }


def get_question_count(concurso_id: int) -> int:
    row = db.fetch_one(
        """
        SELECT COUNT(*) AS qtd
        FROM question_bank qb
        JOIN topics t ON t.id = qb.topic_id
        WHERE qb.concurso_id = ? AND t.concurso_id = ?
        """,
        (concurso_id, concurso_id),
    )
    return int(row["qtd"]) if row else 0


def next_question(concurso_id: int, topic_id: int | None = None) -> dict[str, Any] | None:
    params: tuple[Any, ...]
    where = "qb.concurso_id = ?"
    params = (concurso_id,)
    if topic_id:
        where += " AND qb.topic_id = ?"
        params = (concurso_id, topic_id)
    row = db.fetch_one(
        f"""
        SELECT qb.*, t.discipline, t.topic,
               COALESCE(SUM(qa.is_correct), 0) AS correct_attempts,
               COUNT(qa.id) AS attempts
        FROM question_bank qb
        JOIN topics t ON t.id = qb.topic_id
        LEFT JOIN question_attempts qa ON qa.question_id = qb.id
        WHERE {where}
        GROUP BY qb.id
        ORDER BY attempts ASC, qb.difficulty DESC, RANDOM()
        LIMIT 1
        """,
        params,
    )
    return dict(row) if row else None


def record_attempt(concurso_id: int, question: dict[str, Any], selected_answer: str) -> dict[str, Any]:
    skipped = selected_answer == "Pular"
    expected = str(question["correct_answer"]).upper()
    chosen = "" if skipped else selected_answer.upper()
    is_correct = (chosen == expected) and not skipped
    score_delta = 0.0 if skipped else (1.0 if is_correct else 0.0)
    db.execute(
        """
        INSERT INTO question_attempts
        (concurso_id, question_id, topic_id, selected_answer, is_correct, skipped, score_delta)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            concurso_id,
            int(question["id"]),
            int(question["topic_id"]),
            selected_answer,
            1 if is_correct else 0,
            1 if skipped else 0,
            score_delta,
        ),
    )
    if not skipped:
        db.execute(
            """
            INSERT INTO question_results
            (concurso_id, topic_id, total_questions, correct_answers, difficulty, feedback)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                concurso_id,
                int(question["topic_id"]),
                1,
                1 if is_correct else 0,
                int(question.get("difficulty", 3)),
                f"Banco local: resposta={selected_answer}; gabarito={expected}",
            ),
        )
    if not is_correct and not skipped:
        db.execute(
            """
            INSERT INTO reviews (concurso_id, topic_id, review_date, reason)
            VALUES (?, ?, ?, ?)
            """,
            (
                concurso_id,
                int(question["topic_id"]),
                (date.today() + timedelta(days=2)).isoformat(),
                "Erro em questão do banco local",
            ),
        )
    return {
        "expected": expected,
        "selected": selected_answer,
        "is_correct": is_correct,
        "skipped": skipped,
        "score_delta": score_delta,
    }


def attempts_summary(concurso_id: int) -> pd.DataFrame:
    return db.fetch_df(
        """
        SELECT t.discipline, t.topic,
               COUNT(qa.id) AS attempts,
               SUM(qa.is_correct) AS correct,
               SUM(qa.skipped) AS skipped,
               ROUND(100.0 * SUM(qa.is_correct) / NULLIF(COUNT(qa.id) - SUM(qa.skipped), 0), 1) AS accuracy
        FROM question_attempts qa
        JOIN topics t ON t.id = qa.topic_id
        WHERE qa.concurso_id = ?
        GROUP BY t.discipline, t.topic
        ORDER BY accuracy ASC, attempts DESC
        """,
        (concurso_id,),
    )
