#!/usr/bin/env node
/**
 * IDE Integration MCP Server
 * Provides VS Code diagnostics and Jupyter execution capabilities
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');

class IDEIntegrationServer {
  constructor() {
    this.server = new Server(
      {
        name: 'ide-integration-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.diagnosticsCache = new Map();
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'get_diagnostics',
          description: 'Get TypeScript/ESLint diagnostics for a file or entire project',
          inputSchema: {
            type: 'object',
            properties: {
              uri: {
                type: 'string',
                description: 'File URI to get diagnostics for (optional, omit for all files)',
              },
            },
          },
        },
        {
          name: 'execute_code',
          description: 'Execute code in Jupyter kernel',
          inputSchema: {
            type: 'object',
            properties: {
              code: {
                type: 'string',
                description: 'Code to execute',
              },
              language: {
                type: 'string',
                description: 'Programming language (python, javascript, typescript)',
                enum: ['python', 'javascript', 'typescript'],
              },
            },
            required: ['code', 'language'],
          },
        },
        {
          name: 'format_code',
          description: 'Format code using project formatter (Prettier/ESLint)',
          inputSchema: {
            type: 'object',
            properties: {
              code: {
                type: 'string',
                description: 'Code to format',
              },
              filePath: {
                type: 'string',
                description: 'File path for context (determines formatter)',
              },
            },
            required: ['code'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'get_diagnostics':
            return await this.getDiagnostics(args);
          case 'execute_code':
            return await this.executeCode(args);
          case 'format_code':
            return await this.formatCode(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  async getDiagnostics(args) {
    const { uri } = args;
    const { execSync } = require('child_process');
    const path = require('path');

    try {
      // Run TypeScript compiler
      let tsOutput = '';
      try {
        execSync('npm run typecheck', { encoding: 'utf8', stdio: 'pipe' });
      } catch (error) {
        tsOutput = error.stdout || error.stderr || '';
      }

      // Run ESLint
      let eslintOutput = '';
      try {
        const targetPath = uri ? uri.replace('file://', '') : '.';
        execSync(`npx eslint ${targetPath} --format json`, { encoding: 'utf8', stdio: 'pipe' });
      } catch (error) {
        eslintOutput = error.stdout || '';
      }

      // Parse diagnostics
      const diagnostics = {
        typescript: this.parseTypeScriptDiagnostics(tsOutput),
        eslint: eslintOutput ? JSON.parse(eslintOutput) : [],
      };

      // Cache results
      const cacheKey = uri || 'all';
      this.diagnosticsCache.set(cacheKey, diagnostics);

      // Format response
      const summary = {
        totalErrors: diagnostics.typescript.errors + diagnostics.eslint.filter(f => f.errorCount > 0).length,
        totalWarnings: diagnostics.typescript.warnings + diagnostics.eslint.filter(f => f.warningCount > 0).length,
        files: diagnostics.eslint.length,
      };

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              summary,
              diagnostics,
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Failed to get diagnostics: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }

  parseTypeScriptDiagnostics(output) {
    const errorMatch = output.match(/(\d+) error/);
    const warningMatch = output.match(/(\d+) warning/);

    return {
      errors: errorMatch ? parseInt(errorMatch[1], 10) : 0,
      warnings: warningMatch ? parseInt(warningMatch[1], 10) : 0,
      output: output.trim(),
    };
  }

  async executeCode(args) {
    const { code, language } = args;
    const { execSync } = require('child_process');
    const fs = require('fs');
    const path = require('path');
    const os = require('os');

    try {
      // Create temporary file
      const tempDir = os.tmpdir();
      const tempFile = path.join(tempDir, `mcp_exec_${Date.now()}.${this.getExtension(language)}`);
      fs.writeFileSync(tempFile, code);

      // Execute based on language
      let command;
      switch (language) {
        case 'python':
          command = `python3 ${tempFile}`;
          break;
        case 'javascript':
          command = `node ${tempFile}`;
          break;
        case 'typescript':
          command = `npx tsx ${tempFile}`;
          break;
        default:
          throw new Error(`Unsupported language: ${language}`);
      }

      const output = execSync(command, { encoding: 'utf8', timeout: 30000 });

      // Cleanup
      fs.unlinkSync(tempFile);

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              status: 'success',
              output: output.trim(),
              language,
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              status: 'error',
              error: error.message,
              stderr: error.stderr || '',
              stdout: error.stdout || '',
            }, null, 2),
          },
        ],
        isError: true,
      };
    }
  }

  async formatCode(args) {
    const { code, filePath } = args;
    const { execSync } = require('child_process');
    const fs = require('fs');
    const path = require('path');
    const os = require('os');

    try {
      // Determine file extension
      const ext = filePath ? path.extname(filePath) : '.ts';
      const tempFile = path.join(os.tmpdir(), `mcp_format_${Date.now()}${ext}`);
      fs.writeFileSync(tempFile, code);

      // Run Prettier
      const formatted = execSync(`npx prettier --write ${tempFile}`, { encoding: 'utf8' });
      const formattedCode = fs.readFileSync(tempFile, 'utf8');

      // Cleanup
      fs.unlinkSync(tempFile);

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              status: 'success',
              formatted: formattedCode,
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Failed to format code: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }

  getExtension(language) {
    const extensions = {
      python: 'py',
      javascript: 'js',
      typescript: 'ts',
    };
    return extensions[language] || 'txt';
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('IDE Integration MCP Server running on stdio');
  }
}

const server = new IDEIntegrationServer();
server.run().catch(console.error);
