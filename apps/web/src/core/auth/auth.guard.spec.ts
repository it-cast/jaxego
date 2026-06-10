import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { provideRouter } from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from './auth.service';

describe('authGuard', () => {
  function run(authenticated: boolean): boolean | UrlTree {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        {
          provide: AuthService,
          useValue: { isAuthenticated: () => authenticated },
        },
      ],
    });
    return TestBed.runInInjectionContext(
      () => authGuard({} as never, {} as never)
    ) as boolean | UrlTree;
  }

  it('allows access when authenticated', () => {
    expect(run(true)).toBeTrue();
  });

  it('redirects to /entrar when not authenticated', () => {
    const result = run(false);
    expect(result instanceof UrlTree).toBeTrue();
    const router = TestBed.inject(Router);
    expect(router.serializeUrl(result as UrlTree)).toBe('/entrar');
  });
});
