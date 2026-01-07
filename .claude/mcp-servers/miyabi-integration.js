#!/usr/bin/env node

/**
 * Miyabi MCP Server
 *
 * Claude Code内でMiyabi CLIの全機能を直接呼び出せるMCPサーバー
 *
 * 提供ツール:
 * - miyabi__init - 新規プロジェクト作成
 * - miyabi__install - 既存プロジェクトにインストール
 * - miyabi__status - ステータス確認
 * - miyabi__agent_run - Agent実行
 * - miyabi__auto - Water Spider全自動モード起動
 * - miyabi__todos - TODOコメント自動検出
 * - miyabi__config - 設定管理
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { execSync } from 'child_process';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

const server = new Server(
  {
    name: 'miyabi-integration',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

/**
 * Execute miyabi command
 */
function executeMiyabiCommand(command, options = {}) {
  try {
    const cmd = `npx miyabi ${command}`;
    const result = execSync(cmd, {
      encoding: 'utf-8',
      cwd: options.cwd || process.cwd(),
      stdio: options.silent ? 'pipe' : 'inherit',
      maxBuffer: 10 * 1024 * 1024, // 10MB
    });

    return {
      success: true,
      output: result,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      stderr: error.stderr?.toString() || '',
      stdout: error.stdout?.toString() || '',
    };
  }
}

/**
 * Get project status
 */
function getProjectStatus() {
  const cwd = process.cwd();

  // Check if .miyabi.yml exists
  const hasMiyabi = existsSync(join(cwd, '.miyabi.yml'));

  // Check if .claude/ directory exists
  const hasClaude = existsSync(join(cwd, '.claude'));

  // Read package.json if exists
  let packageInfo = null;
  const packagePath = join(cwd, 'package.json');
  if (existsSync(packagePath)) {
    try {
      const pkg = JSON.parse(readFileSync(packagePath, 'utf-8'));
      packageInfo = {
        name: pkg.name,
        version: pkg.version,
        dependencies: pkg.dependencies || {},
        devDependencies: pkg.devDependencies || {},
      };
    } catch (e) {
      // Ignore parse errors
    }
  }

  return {
    hasMiyabi,
    hasClaude,
    packageInfo,
    workingDirectory: cwd,
  };
}

// Tool definitions
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'miyabi__init',
        description: '新しいMiyabiプロジェクトを作成します。GitHub連携、Agent設定、Claude Code統合を含む完全なセットアップを実行します。',
        inputSchema: {
          type: 'object',
          properties: {
            projectName: {
              type: 'string',
              description: 'プロジェクト名（英数字、ハイフン、アンダースコアのみ）',
            },
            private: {
              type: 'boolean',
              description: 'プライベートリポジトリとして作成するか',
              default: false,
            },
            skipInstall: {
              type: 'boolean',
              description: 'npm installをスキップするか',
              default: false,
            },
          },
          required: ['projectName'],
        },
      },
      {
        name: 'miyabi__install',
        description: '既存プロジェクトにMiyabiをインストールします。.claude/、GitHub Actions、組織設計ラベル体系を追加します。',
        inputSchema: {
          type: 'object',
          properties: {
            dryRun: {
              type: 'boolean',
              description: 'ドライラン（実際には変更しない）',
              default: false,
            },
          },
        },
      },
      {
        name: 'miyabi__status',
        description: 'プロジェクトの状態を確認します。GitHub Issues、Actions、Project V2の状態を表示します。',
        inputSchema: {
          type: 'object',
          properties: {
            watch: {
              type: 'boolean',
              description: 'ウォッチモード（自動更新）を有効にするか',
              default: false,
            },
          },
        },
      },
      {
        name: 'miyabi__agent_run',
        description: 'Autonomous Agentを実行してGitHub Issueを自動処理します。CoordinatorAgent → CodeGenAgent → ReviewAgent → PRAgentの順で実行されます。',
        inputSchema: {
          type: 'object',
          properties: {
            issueNumber: {
              type: 'number',
              description: '処理するIssue番号',
            },
            issueNumbers: {
              type: 'array',
              items: { type: 'number' },
              description: '複数のIssue番号（並列処理）',
            },
            concurrency: {
              type: 'number',
              description: '並行実行数',
              default: 2,
            },
            dryRun: {
              type: 'boolean',
              description: 'ドライラン（実際には変更しない）',
              default: false,
            },
          },
        },
      },
      {
        name: 'miyabi__auto',
        description: 'Water Spider Agent（全自動モード）を起動します。GitHub Issueを自動的に検出・処理し続けます。',
        inputSchema: {
          type: 'object',
          properties: {
            maxIssues: {
              type: 'number',
              description: '最大処理Issue数',
              default: 5,
            },
            interval: {
              type: 'number',
              description: 'ポーリング間隔（秒）',
              default: 60,
            },
          },
        },
      },
      {
        name: 'miyabi__todos',
        description: 'コード内のTODOコメントを自動検出してGitHub Issueを作成します。',
        inputSchema: {
          type: 'object',
          properties: {
            path: {
              type: 'string',
              description: 'スキャン対象パス',
              default: './src',
            },
            autoCreate: {
              type: 'boolean',
              description: '自動的にIssue作成するか',
              default: false,
            },
          },
        },
      },
      {
        name: 'miyabi__config',
        description: 'Miyabi設定を表示・編集します。',
        inputSchema: {
          type: 'object',
          properties: {
            action: {
              type: 'string',
              enum: ['get', 'set', 'list'],
              description: 'アクション（get/set/list）',
              default: 'list',
            },
            key: {
              type: 'string',
              description: '設定キー',
            },
            value: {
              type: 'string',
              description: '設定値',
            },
          },
        },
      },
      {
        name: 'miyabi__get_status',
        description: '現在のプロジェクトのMiyabi/Claude Code統合状態を取得します（軽量・高速）',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
    ],
  };
});

// Tool execution handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'miyabi__init': {
        const { projectName, private: isPrivate, skipInstall } = args;
        const flags = [
          isPrivate ? '--private' : '',
          skipInstall ? '--skip-install' : '',
        ].filter(Boolean);

        const result = executeMiyabiCommand(`init ${projectName} ${flags.join(' ')}`);

        return {
          content: [
            {
              type: 'text',
              text: result.success
                ? `✅ プロジェクト "${projectName}" を作成しました\n\n${result.output}`
                : `❌ プロジェクト作成に失敗しました\n\nエラー: ${result.error}\n\n${result.stderr}`,
            },
          ],
        };
      }

      case 'miyabi__install': {
        const { dryRun } = args;
        const flags = dryRun ? '--dry-run' : '';

        const result = executeMiyabiCommand(`install ${flags}`);

        return {
          content: [
            {
              type: 'text',
              text: result.success
                ? `✅ Miyabiをインストールしました\n\n${result.output}`
                : `❌ インストールに失敗しました\n\nエラー: ${result.error}\n\n${result.stderr}`,
            },
          ],
        };
      }

      case 'miyabi__status': {
        const { watch } = args;
        const flags = watch ? '--watch' : '';

        const result = executeMiyabiCommand(`status ${flags}`);

        return {
          content: [
            {
              type: 'text',
              text: result.success
                ? `📊 プロジェクトステータス\n\n${result.output}`
                : `❌ ステータス取得に失敗しました\n\nエラー: ${result.error}\n\n${result.stderr}`,
            },
          ],
        };
      }

      case 'miyabi__agent_run': {
        const { issueNumber, issueNumbers, concurrency, dryRun } = args;

        let command = 'agent run';

        if (issueNumber) {
          command += ` --issue ${issueNumber}`;
        } else if (issueNumbers && issueNumbers.length > 0) {
          command += ` --issues ${issueNumbers.join(',')}`;
        }

        if (concurrency) {
          command += ` --concurrency ${concurrency}`;
        }

        if (dryRun) {
          command += ' --dry-run';
        }

        const result = executeMiyabiCommand(command);

        return {
          content: [
            {
              type: 'text',
              text: result.success
                ? `🤖 Agent実行完了\n\n${result.output}`
                : `❌ Agent実行に失敗しました\n\nエラー: ${result.error}\n\n${result.stderr}\n\n${result.stdout}`,
            },
          ],
        };
      }

      case 'miyabi__auto': {
        const { maxIssues, interval } = args;

        const flags = [
          maxIssues ? `--max-issues ${maxIssues}` : '',
          interval ? `--interval ${interval}` : '',
        ].filter(Boolean);

        const result = executeMiyabiCommand(`auto ${flags.join(' ')}`);

        return {
          content: [
            {
              type: 'text',
              text: result.success
                ? `🕷️  Water Spider Agent起動\n\n${result.output}`
                : `❌ 自動モード起動に失敗しました\n\nエラー: ${result.error}\n\n${result.stderr}`,
            },
          ],
        };
      }

      case 'miyabi__todos': {
        const { path, autoCreate } = args;

        const flags = [
          path ? `--path ${path}` : '',
          autoCreate ? '--auto-create' : '',
        ].filter(Boolean);

        const result = executeMiyabiCommand(`todos ${flags.join(' ')}`);

        return {
          content: [
            {
              type: 'text',
              text: result.success
                ? `📝 TODOスキャン完了\n\n${result.output}`
                : `❌ TODOスキャンに失敗しました\n\nエラー: ${result.error}\n\n${result.stderr}`,
            },
          ],
        };
      }

      case 'miyabi__config': {
        const { action, key, value } = args;

        let command = 'config';

        if (action === 'get' && key) {
          command += ` --get ${key}`;
        } else if (action === 'set' && key && value) {
          command += ` --set ${key}=${value}`;
        }

        const result = executeMiyabiCommand(command);

        return {
          content: [
            {
              type: 'text',
              text: result.success
                ? `⚙️  設定\n\n${result.output}`
                : `❌ 設定操作に失敗しました\n\nエラー: ${result.error}\n\n${result.stderr}`,
            },
          ],
        };
      }

      case 'miyabi__get_status': {
        const status = getProjectStatus();

        let statusText = '📊 プロジェクト状態\n\n';
        statusText += `作業ディレクトリ: ${status.workingDirectory}\n\n`;
        statusText += `Miyabi統合: ${status.hasMiyabi ? '✅ あり' : '❌ なし'}\n`;
        statusText += `Claude Code統合: ${status.hasClaude ? '✅ あり' : '❌ なし'}\n\n`;

        if (status.packageInfo) {
          statusText += `パッケージ: ${status.packageInfo.name}@${status.packageInfo.version}\n`;
          statusText += `依存関係: ${Object.keys(status.packageInfo.dependencies).length}個\n`;
          statusText += `開発依存: ${Object.keys(status.packageInfo.devDependencies).length}個\n`;
        } else {
          statusText += 'package.json: なし\n';
        }

        return {
          content: [
            {
              type: 'text',
              text: statusText,
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `❌ エラーが発生しました\n\n${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Miyabi MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});
