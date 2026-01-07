module.exports = {
  // Basic formatting
  semi: true,
  trailingComma: 'es5',
  singleQuote: true,
  doubleQuote: false,
  printWidth: 88, // Match Python black line length
  tabWidth: 2,
  useTabs: false,

  // Object formatting
  bracketSpacing: true,
  bracketSameLine: false,

  // Arrow functions
  arrowParens: 'avoid',

  // File-specific overrides
  overrides: [
    // JavaScript/TypeScript
    {
      files: ['*.js', '*.jsx', '*.ts', '*.tsx'],
      options: {
        parser: 'babel',
        semi: true,
        singleQuote: true,
        trailingComma: 'es5',
      },
    },
    // JSON
    {
      files: ['*.json'],
      options: {
        parser: 'json',
        printWidth: 100,
        tabWidth: 2,
      },
    },
    // YAML
    {
      files: ['*.yml', '*.yaml'],
      options: {
        parser: 'yaml',
        singleQuote: false,
        tabWidth: 2,
      },
    },
    // Markdown
    {
      files: ['*.md'],
      options: {
        parser: 'markdown',
        printWidth: 100,
        proseWrap: 'always',
        tabWidth: 2,
      },
    },
    // Package.json - preserve exact formatting
    {
      files: ['package.json'],
      options: {
        printWidth: 100,
        tabWidth: 2,
      },
    },
  ],

  // Plugin-specific settings
  plugins: [],

  // Ignore patterns
  ignore: [
    'node_modules/**',
    'dist/**',
    'build/**',
    'coverage/**',
    '*.min.js',
    '*.min.css',
    '.git/**',
    '.venv/**',
    'venv/**',
    '__pycache__/**',
    '*.pyc',
    '.pytest_cache/**',
    '.mypy_cache/**',
    '.ruff_cache/**',
    'htmlcov/**',
    'logs/**',
  ],
};