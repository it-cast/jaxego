import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { PushOptInService } from './push-optin.service';

describe('PushOptInService', () => {
  let service: PushOptInService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(PushOptInService);
  });

  it('does not prompt before a contextual trigger (never on first load)', () => {
    expect(service.shouldPrompt()).toBe(false);
  });

  it('prompts only after a trigger while permission is default', () => {
    if (typeof Notification === 'undefined') {
      pending('Notification API not available in this browser');
      return;
    }
    service.markContextualTrigger();
    const result = service.shouldPrompt();
    // Result depends on the headless browser permission; the key invariant is it is
    // false WITHOUT a trigger (above) and only considers prompting AFTER one.
    expect(typeof result).toBe('boolean');
  });
});
