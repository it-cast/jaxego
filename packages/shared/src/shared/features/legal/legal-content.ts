/**
 * Textos dos Termos de Uso e da Política de Privacidade do Jaxegô.
 *
 * TEXTO PADRÃO: descreve o que o sistema faz hoje (dados coletados, prazos de guarda,
 * parceiros). Antes de publicar, um advogado deve revisar, e os dados da empresa abaixo
 * precisam ser confirmados — é o único lugar onde eles aparecem.
 */

export const EMPRESA = {
  marca: 'Jaxegô',
  /** Razão social de quem opera o Jaxegô (confirmar). */
  razaoSocial: 'Grupo Itcast',
  /** CNPJ (preencher; vazio = não aparece no texto). */
  cnpj: '',
  /** E-mail para dúvidas e pedidos sobre dados pessoais (confirmar se existe). */
  email: 'contato@jaxego.com.br',
  /** Comarca do foro (confirmar). */
  foro: 'Santo Antônio de Pádua/RJ',
};

export const ATUALIZADO_EM = '19 de novembro de 2026';

export type LegalTipo = 'termos' | 'privacidade';

export interface LegalSecao {
  titulo: string;
  paragrafos?: string[];
  itens?: string[];
  /** Parágrafos depois da lista. */
  depois?: string[];
}

export interface LegalDoc {
  titulo: string;
  resumo: string;
  secoes: LegalSecao[];
}

const operadora = EMPRESA.cnpj ? `${EMPRESA.razaoSocial}, CNPJ ${EMPRESA.cnpj}` : EMPRESA.razaoSocial;

export const TERMOS: LegalDoc = {
  titulo: 'Termos de Uso',
  resumo:
    'As regras para usar o Jaxegô como loja, entregador, equipe ou administrador. Ao criar uma conta você concorda com elas.',
  secoes: [
    {
      titulo: '1. O que é o Jaxegô',
      paragrafos: [
        `O Jaxegô é uma plataforma operada por ${operadora} que liga lojas a entregadores independentes da mesma cidade. A loja cria a entrega, um entregador aceita, faz a coleta e a entrega, e o destinatário acompanha por um link.`,
        'O Jaxegô não é transportadora nem empregador. Os entregadores trabalham por conta própria, escolhem quais corridas aceitar e definem o próprio preço por zona, respeitando o valor mínimo da cidade.',
      ],
    },
    {
      titulo: '2. Conta e cadastro',
      itens: [
        'Você precisa ter 18 anos ou mais e informar dados verdadeiros e atualizados.',
        'A loja precisa de um CNPJ ativo, que consultamos na Receita Federal.',
        'O entregador passa por uma análise de documentos (selfie, CNH, documento do veículo e, quando a cidade exigir, antecedentes e MEI) antes de receber corridas.',
        'A senha é pessoal. Você responde pelo que for feito com a sua conta; se achar que alguém a usou, troque a senha e nos avise.',
        'Podemos recusar ou pedir correção de um cadastro com dados incompletos, inconsistentes ou suspeitos.',
      ],
    },
    {
      titulo: '3. Como funciona uma entrega',
      itens: [
        'A loja informa coleta, destino, itens e forma de pagamento, e vê uma estimativa de valor antes de confirmar.',
        'A corrida é oferecida aos entregadores da área, um por vez, e o primeiro que aceitar fica com ela.',
        'O entregador vê o valor antes de aceitar. Na entrega, registra uma foto e a posição do GPS como comprovação.',
        'O destinatário pode acompanhar a entrega por um link, sem precisar de cadastro.',
      ],
    },
    {
      titulo: '4. Preços, pagamentos e planos',
      itens: [
        'A corrida pode ser paga por PIX, cartão ou diretamente ao entregador (pagamento direto), conforme o que estiver disponível.',
        'Os pagamentos por PIX e cartão são processados por uma empresa de pagamentos parceira. O Jaxegô não guarda os dados do seu cartão.',
        'A loja paga a taxa da plataforma e, se escolher um plano pago, a mensalidade, nos valores mostrados na tela de Plano antes da contratação.',
        'Nas entregas com pagamento direto, a taxa da plataforma é cobrada em uma fatura mensal. A fatura em atraso pode bloquear a criação de novas entregas até o pagamento.',
        'O entregador recebe o valor das corridas pagas pela plataforma no saldo e pode sacar para a conta bancária cadastrada, respeitando o valor mínimo de saque.',
      ],
    },
    {
      titulo: '5. Cancelamento',
      paragrafos: [
        'A loja pode cancelar uma entrega. Se o entregador já tiver aceitado ou se deslocado, pode haver um custo de cancelamento, que é mostrado antes da confirmação. Pagamentos feitos pela plataforma são estornados quando cabível.',
      ],
    },
    {
      titulo: '6. Compromissos da loja',
      itens: [
        'Enviar apenas itens lícitos, bem embalados e descritos corretamente.',
        'Informar endereço e contato corretos do destinatário e ter autorização para compartilhá-los com o entregador.',
        'Não enviar produtos proibidos por lei, como armas, drogas ilícitas, animais ou itens perigosos sem a devida autorização.',
        'Tratar os entregadores com respeito e não combinar pagamentos por fora da plataforma para fugir das regras.',
      ],
    },
    {
      titulo: '7. Compromissos do entregador',
      itens: [
        'Cumprir as leis de trânsito e manter em dia documentos, habilitação e veículo.',
        'Cuidar do item do momento da coleta até a entrega.',
        'Registrar uma comprovação real (foto e GPS feitos no local da entrega).',
        'Usar os dados do destinatário só para fazer aquela entrega, sem guardar ou repassar a ninguém.',
      ],
    },
    {
      titulo: '8. Avaliações, nota e suspensões',
      paragrafos: [
        'Lojas avaliam entregadores, e o entregador tem uma nota calculada por regras que ele pode consultar no app. Violações destes Termos, fraude ou reclamações graves podem levar à suspensão da conta.',
        'Toda suspensão é informada com o motivo, e você pode apresentar um recurso, que é analisado pela administração da cidade.',
      ],
    },
    {
      titulo: '9. Disputas',
      paragrafos: [
        'Problemas com uma entrega ou com um pagamento (por exemplo, "não recebi" no pagamento direto) podem ser registrados como disputa na plataforma, dentro do prazo indicado nela. A administração analisa as informações das duas partes, inclusive a comprovação de entrega.',
      ],
    },
    {
      titulo: '10. Responsabilidades',
      paragrafos: [
        'O Jaxegô fornece a tecnologia que liga lojas e entregadores e se esforça para manter o serviço disponível e seguro, mas não garante funcionamento sem interrupções. Cada usuário responde pelos próprios atos, pelos itens enviados e pelas informações que fornece, nos termos da lei.',
        'Nada nestes Termos afasta direitos garantidos pelo Código de Defesa do Consumidor quando ele se aplicar.',
      ],
    },
    {
      titulo: '11. Encerramento da conta',
      paragrafos: [
        `Você pode pedir o encerramento da sua conta a qualquer momento pelo e-mail ${EMPRESA.email}. Valores e faturas pendentes continuam devidos. Podemos encerrar contas que violem estes Termos.`,
      ],
    },
    {
      titulo: '12. Mudanças nestes Termos',
      paragrafos: [
        'Podemos atualizar estes Termos. Quando a mudança for importante, avisaremos na plataforma antes de ela valer. Continuar usando o Jaxegô depois disso significa concordar com a nova versão.',
      ],
    },
    {
      titulo: '13. Lei e foro',
      paragrafos: [
        `Estes Termos seguem as leis do Brasil. Fica eleito o foro da comarca de ${EMPRESA.foro}, ressalvado o direito do consumidor de usar o foro do seu domicílio.`,
        `Dúvidas: ${EMPRESA.email}.`,
      ],
    },
  ],
};

export const PRIVACIDADE: LegalDoc = {
  titulo: 'Política de Privacidade',
  resumo:
    'Quais dados pessoais o Jaxegô usa, para quê, com quem compartilha, por quanto tempo guarda e como você exerce seus direitos pela LGPD.',
  secoes: [
    {
      titulo: '1. Quem cuida dos seus dados',
      paragrafos: [
        `O controlador dos dados é ${operadora}, que opera o Jaxegô. Para qualquer assunto sobre dados pessoais, fale com o nosso encarregado pelo e-mail ${EMPRESA.email}.`,
      ],
    },
    {
      titulo: '2. Dados que coletamos',
      itens: [
        'Loja: razão social, nome fantasia, CNPJ, endereço, telefone, e-mail e o nome de quem cuida da conta.',
        'Entregador: nome, CPF, data de nascimento, telefone, e-mail, endereço, tipo e placa do veículo, CNPJ do MEI, dados bancários para receber os repasses e as fotos dos documentos (selfie, CNH, documento do veículo e, quando exigido, antecedentes).',
        'Localização do entregador: enviada pelo app enquanto ele está disponível ou fazendo uma entrega.',
        'Destinatário: nome, telefone e endereço de entrega informados pela loja. Se o CPF for informado, guardamos só uma versão cifrada dele, nunca o número.',
        'Comprovação: foto da entrega com a posição do GPS no momento.',
        'Uso da plataforma: registros de acesso (data, hora e IP), ações feitas nas contas e informações técnicas do aparelho para envio de notificações.',
        'Pagamentos: dados das cobranças e repasses. Os dados de cartão vão direto para a empresa de pagamentos e não ficam guardados no Jaxegô.',
      ],
    },
    {
      titulo: '3. Para que usamos',
      itens: [
        'Criar e manter a sua conta e fazer as entregas acontecerem.',
        'Validar identidade e documentos, prevenir fraudes e proteger lojas, entregadores e destinatários.',
        'Mostrar o trajeto e a posição da entrega para a loja e para o destinatário.',
        'Processar pagamentos, faturas, repasses e saques.',
        'Enviar avisos por notificação, e-mail ou SMS sobre a sua conta e as suas entregas.',
        'Resolver disputas e recursos e cumprir obrigações legais e fiscais.',
        'Melhorar o serviço com estatísticas de uso.',
      ],
      depois: ['Não vendemos dados pessoais e não usamos os seus dados para publicidade de terceiros.'],
    },
    {
      titulo: '4. Bases legais (LGPD)',
      itens: [
        'Execução do contrato: para prestar o serviço que você pediu.',
        'Obrigação legal: guarda de dados fiscais e de registros de acesso.',
        'Legítimo interesse: segurança, prevenção a fraudes e melhoria do serviço, sempre respeitando os seus direitos.',
        'Consentimento: quando a lei exigir, pedimos antes e você pode retirar quando quiser.',
      ],
    },
    {
      titulo: '5. Com quem compartilhamos',
      itens: [
        'Entre loja e entregador, só o necessário para a entrega: a loja vê nome, veículo e trajeto do entregador; o entregador vê o endereço de coleta, o destino e o contato do destinatário.',
        'O link de acompanhamento mostra ao destinatário o andamento e uma posição aproximada do entregador, sem expor dados pessoais dele.',
        'Empresas que prestam serviço para o Jaxegô: processamento de pagamentos, armazenamento em nuvem, envio de e-mail e SMS, mapas e monitoramento de erros. Elas só usam os dados para esse serviço.',
        'Consulta de CNPJ em bases públicas da Receita Federal, no cadastro da loja.',
        'Autoridades, quando houver ordem judicial ou obrigação legal.',
      ],
    },
    {
      titulo: '6. Por quanto tempo guardamos',
      itens: [
        'Trajeto do entregador: 7 dias. Depois é apagado automaticamente.',
        'Registro das ações de cada entrega (aceite, coleta, entrega) com a posição naquele momento: guardado com o histórico da entrega, como comprovação.',
        'Contas e destinatários sem movimento há 12 meses: os dados pessoais são anonimizados automaticamente.',
        'Conta encerrada: os dados pessoais são anonimizados em até 30 dias, exceto o que a lei manda guardar (dados fiscais pelo prazo legal e registros de acesso por 6 meses).',
        'Documentos do entregador: enquanto a conta estiver ativa e pelo prazo necessário para defesa em processos.',
      ],
    },
    {
      titulo: '7. Segurança',
      paragrafos: [
        'As senhas são guardadas de forma cifrada e ninguém da equipe consegue vê-las. A comunicação é criptografada, cada administrador só acessa os dados da própria cidade, as ações nas contas ficam registradas e as fotos de documentos são gravadas sem as informações escondidas do arquivo (como localização da câmera).',
        'Se acontecer um incidente de segurança que possa trazer risco a você, avisaremos você e a ANPD, como manda a lei.',
      ],
    },
    {
      titulo: '8. Seus direitos',
      paragrafos: ['Pela LGPD, você pode pedir a qualquer momento:'],
      itens: [
        'Confirmação de que tratamos seus dados e acesso a eles.',
        'Correção de dados incompletos ou errados.',
        'Anonimização, bloqueio ou eliminação de dados desnecessários.',
        'Portabilidade para outro serviço.',
        'Informação sobre com quem compartilhamos.',
        'Revogação do consentimento, quando ele for a base do uso.',
      ],
      depois: [
        `Faça o pedido pelo e-mail ${EMPRESA.email}, a partir do e-mail da sua conta. Respondemos em até 15 dias. Você também pode reclamar à Autoridade Nacional de Proteção de Dados (ANPD).`,
      ],
    },
    {
      titulo: '9. Cookies e armazenamento no navegador',
      paragrafos: [
        'Usamos um cookie para manter você conectado com segurança e o armazenamento do navegador para lembrar preferências, como o e-mail do login. Não usamos cookies de publicidade.',
      ],
    },
    {
      titulo: '10. Menores de idade',
      paragrafos: ['O Jaxegô não é destinado a menores de 18 anos e não coletamos dados deles de propósito.'],
    },
    {
      titulo: '11. Mudanças nesta Política',
      paragrafos: [
        'Podemos atualizar esta Política. A data da última atualização fica no topo, e mudanças importantes serão avisadas na plataforma.',
      ],
    },
  ],
};

export const LEGAL: Record<LegalTipo, LegalDoc> = { termos: TERMOS, privacidade: PRIVACIDADE };
