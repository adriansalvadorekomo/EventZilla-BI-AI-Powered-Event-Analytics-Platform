import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { Assistant } from './assistant/assistant';
import { AssistantStore } from './assistant/store';
import { Icon } from './ui/icon';
import { PAGES, Palette } from './ui/palette';
import { Tour } from './ui/tour';
import { Trust } from './ui/trust';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Assistant, Palette, Icon, Tour, Trust],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected readonly store = inject(AssistantStore);
  protected readonly pages = PAGES;
  protected readonly isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform);
}
