/**
 * Global jest-axe setup
 * 
 * Após copiar para o projeto, referenciar em jest.config.js:
 *   setupFilesAfterEach: ['<rootDir>/src/test/jest.setup.a11y.js']
 * 
 * Uso em testes:
 *   import { axe, toHaveNoViolations } from 'jest-axe';
 *   it('no a11y violations', async () => {
 *     const { container } = render(<Component />);
 *     expect(await axe(container)).toHaveNoViolations();
 *   });
 */

const { toHaveNoViolations, configureAxe } = require('jest-axe');

expect.extend(toHaveNoViolations);

// Regras ativas — WCAG 2.1 AA
const axe = configureAxe({
  rules: {
    // Cor e contraste
    'color-contrast': { enabled: true },
    'color-contrast-enhanced': { enabled: false }, // AAA — opt-in

    // Estrutura semântica
    'landmark-one-main': { enabled: true },
    'page-has-heading-one': { enabled: true },
    'heading-order': { enabled: true },
    'region': { enabled: true },

    // Formulários
    'label': { enabled: true },
    'label-title-only': { enabled: true },
    'form-field-multiple-labels': { enabled: true },
    'autocomplete-valid': { enabled: true },

    // Imagens e mídia
    'image-alt': { enabled: true },
    'image-redundant-alt': { enabled: true },
    'area-alt': { enabled: true },

    // Interação
    'button-name': { enabled: true },
    'link-name': { enabled: true },
    'aria-allowed-role': { enabled: true },
    'aria-required-attr': { enabled: true },
    'aria-valid-attr': { enabled: true },
    'aria-valid-attr-value': { enabled: true },
    'aria-roles': { enabled: true },
    'aria-hidden-focus': { enabled: true },

    // Navegação por teclado
    'tabindex': { enabled: true },
    'focus-order-semantics': { enabled: true },

    // Tabelas
    'table-fake-caption': { enabled: true },
    'td-headers-attr': { enabled: true },
    'th-has-data-cells': { enabled: true },

    // Idioma
    'html-has-lang': { enabled: true },
    'html-lang-valid': { enabled: true },
    'valid-lang': { enabled: true },
  },
});

global.axe = axe;
