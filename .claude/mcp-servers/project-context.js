#!/usr/bin/env node
/**
 * Project Context MCP Server
 * Provides project-specific context and dependency information
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const fs = require('fs');
const path = require('path');

class ProjectContextServer {
  constructor() {
    this.server = new Server(
      {
        name: 'project-context-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.projectRoot = process.cwd();
    this.setupToolHandlers();
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'get_project_structure',
          description: 'Get project directory structure and file tree',
          inputSchema: {
            type: 'object',
            properties: {
              depth: {
                type: 'number',
                description: 'Maximum depth to traverse',
                default: 3,
              },
              includeHidden: {
                type: 'boolean',
                description: 'Include hidden files/directories',
                default: false,
              },
            },
          },
        },
        {
          name: 'get_dependencies',
          description: 'Get project dependencies and their versions',
          inputSchema: {
            type: 'object',
            properties: {
              type: {
                type: 'string',
                enum: ['all', 'dependencies', 'devDependencies'],
                default: 'all',
              },
            },
          },
        },
        {
          name: 'get_agent_config',
          description: 'Get agent configuration and settings',
          inputSchema: {
            type: 'object',
            properties: {},
          },
        },
        {
          name: 'analyze_codebase',
          description: 'Analyze codebase metrics (LOC, files, complexity)',
          inputSchema: {
            type: 'object',
            properties: {
              includeTests: {
                type: 'boolean',
                default: true,
              },
            },
          },
        },
        {
          name: 'get_recent_changes',
          description: 'Get recent git changes and commits',
          inputSchema: {
            type: 'object',
            properties: {
              limit: {
                type: 'number',
                description: 'Number of commits to retrieve',
                default: 10,
              },
            },
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'get_project_structure':
            return await this.getProjectStructure(args);
          case 'get_dependencies':
            return await this.getDependencies(args);
          case 'get_agent_config':
            return await this.getAgentConfig(args);
          case 'analyze_codebase':
            return await this.analyzeCodebase(args);
          case 'get_recent_changes':
            return await this.getRecentChanges(args);
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

  async getProjectStructure(args) {
    const { depth = 3, includeHidden = false } = args;

    const buildTree = (dir, currentDepth = 0, prefix = '') => {
      if (currentDepth >= depth) return [];

      const items = fs.readdirSync(dir);
      const lines = [];

      items
        .filter(item => {
          if (!includeHidden && item.startsWith('.')) return false;
          if (item === 'node_modules') return false;
          return true;
        })
        .forEach((item, index) => {
          const itemPath = path.join(dir, item);
          const isLast = index === items.length - 1;
          const connector = isLast ? '└── ' : '├── ';
          const stats = fs.statSync(itemPath);

          lines.push(`${prefix}${connector}${item}${stats.isDirectory() ? '/' : ''}`);

          if (stats.isDirectory()) {
            const newPrefix = prefix + (isLast ? '    ' : '│   ');
            lines.push(...buildTree(itemPath, currentDepth + 1, newPrefix));
          }
        });

      return lines;
    };

    const tree = buildTree(this.projectRoot);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            root: this.projectRoot,
            tree: tree.join('\n'),
          }, null, 2),
        },
      ],
    };
  }

  async getDependencies(args) {
    const { type = 'all' } = args;

    const packageJsonPath = path.join(this.projectRoot, 'package.json');
    if (!fs.existsSync(packageJsonPath)) {
      throw new Error('package.json not found');
    }

    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

    const result = {
      name: packageJson.name,
      version: packageJson.version,
    };

    if (type === 'all' || type === 'dependencies') {
      result.dependencies = packageJson.dependencies || {};
    }

    if (type === 'all' || type === 'devDependencies') {
      result.devDependencies = packageJson.devDependencies || {};
    }

    // Count total
    result.counts = {
      dependencies: Object.keys(packageJson.dependencies || {}).length,
      devDependencies: Object.keys(packageJson.devDependencies || {}).length,
      total: Object.keys(packageJson.dependencies || {}).length + Object.keys(packageJson.devDependencies || {}).length,
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  async getAgentConfig(args) {
    const settingsPath = path.join(this.projectRoot, '.claude', 'settings.example.json');
    const localSettingsPath = path.join(this.projectRoot, '.claude', 'settings.local.json');

    let config = {};

    if (fs.existsSync(settingsPath)) {
      config.example = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
    }

    if (fs.existsSync(localSettingsPath)) {
      config.local = JSON.parse(fs.readFileSync(localSettingsPath, 'utf8'));
    }

    // Get agent implementations
    const agentsDir = path.join(this.projectRoot, 'agents');
    if (fs.existsSync(agentsDir)) {
      config.agents = fs.readdirSync(agentsDir, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory())
        .map(dirent => dirent.name);
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(config, null, 2),
        },
      ],
    };
  }

  async analyzeCodebase(args) {
    const { includeTests = true } = args;

    const countLines = (filePath) => {
      const content = fs.readFileSync(filePath, 'utf8');
      return content.split('\n').length;
    };

    const analyzeDirectory = (dir, stats = { files: 0, lines: 0, byExtension: {} }) => {
      const items = fs.readdirSync(dir);

      items.forEach(item => {
        const itemPath = path.join(dir, item);
        const stat = fs.statSync(itemPath);

        if (stat.isDirectory()) {
          if (item === 'node_modules' || item === '.git' || item === 'dist' || item === 'build') {
            return;
          }
          if (!includeTests && (item === 'tests' || item === '__tests__')) {
            return;
          }
          analyzeDirectory(itemPath, stats);
        } else if (stat.isFile()) {
          const ext = path.extname(item);
          if (['.ts', '.js', '.tsx', '.jsx', '.json', '.md'].includes(ext)) {
            stats.files++;
            const lines = countLines(itemPath);
            stats.lines += lines;

            if (!stats.byExtension[ext]) {
              stats.byExtension[ext] = { files: 0, lines: 0 };
            }
            stats.byExtension[ext].files++;
            stats.byExtension[ext].lines += lines;
          }
        }
      });

      return stats;
    };

    const stats = analyzeDirectory(this.projectRoot);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            summary: {
              totalFiles: stats.files,
              totalLines: stats.lines,
              averageLinesPerFile: Math.round(stats.lines / stats.files),
            },
            byExtension: stats.byExtension,
          }, null, 2),
        },
      ],
    };
  }

  async getRecentChanges(args) {
    const { limit = 10 } = args;
    const { execSync } = require('child_process');

    try {
      // Get recent commits
      const commits = execSync(`git log -${limit} --pretty=format:'%H|%an|%ae|%ad|%s' --date=iso`, {
        encoding: 'utf8',
        cwd: this.projectRoot,
      });

      const commitList = commits.split('\n').map(line => {
        const [hash, author, email, date, message] = line.split('|');
        return { hash, author, email, date, message };
      });

      // Get current branch
      const branch = execSync('git branch --show-current', {
        encoding: 'utf8',
        cwd: this.projectRoot,
      }).trim();

      // Get file changes
      const stats = execSync('git diff --stat HEAD~1 HEAD', {
        encoding: 'utf8',
        cwd: this.projectRoot,
      });

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              branch,
              recentCommits: commitList,
              latestChanges: stats,
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: 'Git repository not found or git command failed',
          },
        ],
        isError: true,
      };
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Project Context MCP Server running on stdio');
  }
}

const server = new ProjectContextServer();
server.run().catch(console.error);
