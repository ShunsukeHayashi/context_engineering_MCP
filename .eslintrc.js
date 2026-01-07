module.exports = {
  env: {
    node: true,
    es2022: true,
  },
  extends: [
    'eslint:recommended',
    'prettier',
  ],
  plugins: ['prettier'],
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
  },
  rules: {
    // Prettier integration
    'prettier/prettier': 'error',

    // Code quality
    'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'no-debugger': 'error',
    'no-alert': 'error',

    // Best practices
    'eqeqeq': ['error', 'always'],
    'curly': ['error', 'all'],
    'no-eval': 'error',
    'no-implied-eval': 'error',
    'no-new-func': 'error',
    'no-script-url': 'error',
    'no-multi-str': 'error',
    'no-new-wrappers': 'error',
    'no-new': 'error',
    'no-undef-init': 'error',
    'no-undefined': 'off', // Allow undefined
    'no-use-before-define': ['error', { functions: false }],

    // ES6+
    'prefer-const': 'error',
    'no-var': 'error',
    'prefer-arrow-callback': 'error',
    'prefer-template': 'error',
    'object-shorthand': 'error',
    'prefer-destructuring': ['error', {
      array: true,
      object: true,
    }, {
      enforceForRenamedProperties: false,
    }],

    // Async/Await
    'require-await': 'error',
    'no-async-promise-executor': 'error',
    'no-await-in-loop': 'warn',

    // Imports
    'no-duplicate-imports': 'error',

    // Node.js specific
    'no-process-exit': 'error',
    'global-require': 'error',
    'handle-callback-err': 'error',

    // Security
    'no-new-require': 'error',
    'no-path-concat': 'error',

    // Stylistic (handled by Prettier, but some logical rules)
    'consistent-return': 'error',
    'default-case': 'error',
    'dot-notation': 'error',
    'no-else-return': 'error',
    'no-empty-function': 'error',
    'no-lone-blocks': 'error',
    'no-magic-numbers': ['warn', {
      ignore: [-1, 0, 1, 2],
      ignoreArrayIndexes: true,
      enforceConst: true,
      detectObjects: false,
    }],
    'no-return-assign': 'error',
    'no-useless-concat': 'error',
    'prefer-regex-literals': 'error',
    'yoda': 'error',

    // Variables
    'init-declarations': 'off',
    'no-catch-shadow': 'off',
    'no-shadow': 'error',
    'no-undef': 'error',
    'no-unused-expressions': 'error',

    // Complexity
    'complexity': ['warn', 10],
    'max-depth': ['warn', 4],
    'max-nested-callbacks': ['warn', 3],
    'max-params': ['warn', 4],
    'max-statements': ['warn', 15],
  },
  overrides: [
    // Test files
    {
      files: ['**/*.test.js', '**/*.spec.js', '**/test/**/*.js'],
      env: {
        jest: true,
        mocha: true,
      },
      rules: {
        'no-magic-numbers': 'off',
        'max-statements': 'off',
        'max-nested-callbacks': 'off',
      },
    },
    // Configuration files
    {
      files: ['*.config.js', '.eslintrc.js'],
      rules: {
        'no-console': 'off',
      },
    },
    // MCP Server specific
    {
      files: ['mcp-server/**/*.js'],
      rules: {
        'no-console': ['warn', { allow: ['error'] }], // Allow console.error for MCP logging
        'require-await': 'off', // MCP handlers might not always need await
      },
    },
  ],
};