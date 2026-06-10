/**
 * ESLint rule: no-hardcoded-colors
 * 
 * Proíbe uso de hex colors hardcoded em CSS-in-JS, templates, e styles.
 * Força uso de tokens do design system.
 * 
 * Copy para: .eslint-rules/no-hardcoded-colors.js
 * 
 * Ativar em .eslintrc.js:
 *   module.exports = {
 *     rulePaths: ['.eslint-rules'],
 *     rules: { 'no-hardcoded-colors': 'error' },
 *   };
 * 
 * Enforces: product/component-library-governance (tokens obrigatórios)
 */

module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Proíbe cores hardcoded — use tokens do design system',
      category: 'Design System',
      recommended: true,
    },
    messages: {
      hardcodedColor:
        "Cor hardcoded '{{color}}' detectada. Use um token do design system: var(--color-*). " +
        "Se não existe, adicione ao packages/design-tokens primeiro.",
    },
    schema: [
      {
        type: 'object',
        properties: {
          allowInFiles: {
            type: 'array',
            items: { type: 'string' },
          },
        },
        additionalProperties: false,
      },
    ],
  },

  create(context) {
    const options = context.options[0] || {};
    const allowList = options.allowInFiles || ['design-tokens', 'tokens.ts', 'tokens.scss'];
    const filename = context.getFilename();

    // Pula arquivos de tokens (fonte de verdade)
    if (allowList.some((pattern) => filename.includes(pattern))) {
      return {};
    }

    const HEX_REGEX = /#([0-9a-fA-F]{3,8})(?![0-9a-fA-F])/g;
    const RGB_REGEX = /rgba?\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+/g;
    const HSL_REGEX = /hsla?\s*\(\s*\d+/g;

    function checkString(node, value) {
      const matches = [
        ...(value.match(HEX_REGEX) || []),
        ...(value.match(RGB_REGEX) || []),
        ...(value.match(HSL_REGEX) || []),
      ];
      for (const match of matches) {
        context.report({
          node,
          messageId: 'hardcodedColor',
          data: { color: match },
        });
      }
    }

    return {
      Literal(node) {
        if (typeof node.value === 'string') {
          checkString(node, node.value);
        }
      },
      TemplateLiteral(node) {
        for (const quasi of node.quasis) {
          checkString(node, quasi.value.raw);
        }
      },
    };
  },
};
