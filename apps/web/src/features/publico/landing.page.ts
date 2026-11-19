import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import {
  faArrowRight,
  faBolt,
  faCamera,
  faCode,
  faLink,
  faLocationDot,
  faMoneyBillWave,
  faMotorcycle,
  faRoute,
  faStore,
  faWallet,
  faChartLine,
} from '@fortawesome/free-solid-svg-icons';

/**
 * Landing pública do Jaxegô (rota "/"): apresenta o produto para lojas e entregadores
 * e leva ao cadastro da loja e ao login. Só tokens do design system (v3), Fraunces
 * italic em uma palavra por título, dados em mono. Sem imagens: mapa em SVG/CSS.
 */
@Component({
  selector: 'jx-landing',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, FaIconComponent],
  templateUrl: './landing.page.html',
  styleUrl: './landing.page.scss',
})
export class LandingPage {
  protected readonly ano = new Date().getFullYear();
  protected readonly i = {
    seta: faArrowRight,
    raio: faBolt,
    camera: faCamera,
    codigo: faCode,
    link: faLink,
    local: faLocationDot,
    dinheiro: faMoneyBillWave,
    moto: faMotorcycle,
    rota: faRoute,
    loja: faStore,
    carteira: faWallet,
    grafico: faChartLine,
  };

  protected readonly passos = [
    {
      n: '1',
      titulo: 'Crie a entrega',
      texto: 'Endereço de coleta, destino e forma de pagamento. Leva menos de um minuto.',
    },
    {
      n: '2',
      titulo: 'Um entregador aceita',
      texto: 'O pedido vai para os entregadores da sua área, do mais perto para o mais longe.',
    },
    {
      n: '3',
      titulo: 'Chegou, comprovado',
      texto: 'O destinatário acompanha pelo link e a entrega fecha com foto e GPS.',
    },
  ];

  protected readonly recursosLoja = [
    {
      icone: faLocationDot,
      titulo: 'Entregadores da sua cidade',
      texto: 'Uma malha local, com validação de documentos, pronta para o pico de sexta.',
    },
    {
      icone: faCamera,
      titulo: 'Comprovação em toda entrega',
      texto: 'Foto e posição GPS no momento da entrega. Sem "mas eu entreguei".',
    },
    {
      icone: faWallet,
      titulo: 'Pague do seu jeito',
      texto: 'PIX, cartão ou pagamento direto ao entregador. Tudo registrado.',
    },
    {
      icone: faLink,
      titulo: 'Rastreio sem app',
      texto: 'O destinatário recebe um link e vê o entregador chegando no mapa.',
    },
    {
      icone: faRoute,
      titulo: 'Trajeto registrado',
      texto: 'Veja o caminho que o entregador fez em cada entrega.',
    },
    {
      icone: faCode,
      titulo: 'API para o seu sistema',
      texto: 'Crie e acompanhe entregas direto do seu sistema de pedidos.',
    },
  ];

  protected readonly recursosEntregador = [
    'Você vê o valor da corrida antes de aceitar',
    'Preço por zona definido por você',
    'Score explicável: você sabe o que subiu e o que caiu',
    'Ganhos e saques na palma da mão',
  ];
}
