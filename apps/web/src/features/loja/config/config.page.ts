import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

interface MerchantProfile {
  id: number;
  trade_name: string;
  address: string | null;
  address_number: string | null;
  address_neighborhood: string | null;
  category: string;
  email: string;
}

@Component({
  selector: 'jx-loja-config',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule],
  templateUrl: './config.page.html',
  styleUrl: './config.page.scss',
})
export class LojaConfigPage implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly loading = signal(true);
  protected readonly saving = signal(false);
  protected readonly msg = signal<{ text: string; tone: 'ok' | 'err' } | null>(null);

  protected form = {
    trade_name: '',
    address: '',
    address_number: '',
    address_neighborhood: '',
  };
  protected email = '';
  protected category = '';

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  private async load(): Promise<void> {
    this.loading.set(true);
    try {
      const profile = await firstValueFrom(
        this.http.get<MerchantProfile>('/v1/merchants/profile'),
      );
      this.form.trade_name = profile.trade_name;
      this.form.address = profile.address ?? '';
      this.form.address_number = profile.address_number ?? '';
      this.form.address_neighborhood = profile.address_neighborhood ?? '';
      this.email = profile.email;
      this.category = profile.category;
    } catch {
      this.msg.set({ text: 'Erro ao carregar dados da loja.', tone: 'err' });
    } finally {
      this.loading.set(false);
    }
  }

  protected async save(): Promise<void> {
    this.saving.set(true);
    this.msg.set(null);
    try {
      await firstValueFrom(
        this.http.patch('/v1/merchants/profile', {
          trade_name: this.form.trade_name,
          address: this.form.address || null,
          address_number: this.form.address_number || null,
          address_neighborhood: this.form.address_neighborhood || null,
        }),
      );
      this.msg.set({ text: 'Dados atualizados com sucesso.', tone: 'ok' });
    } catch {
      this.msg.set({ text: 'Erro ao salvar. Tente novamente.', tone: 'err' });
    } finally {
      this.saving.set(false);
    }
  }

  protected categoryLabel(): string {
    const map: Record<string, string> = {
      restaurante: 'Restaurante/Lanchonete',
      comercio: 'Comercio',
      farmacia: 'Farmacia',
      mercado: 'Mercado',
      outro: 'Outro',
    };
    return map[this.category] ?? this.category;
  }
}
