#!/usr/bin/env node
/**
 * GitHub Enhanced MCP Server
 * Provides extended GitHub operations for Issue/PR management
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const { Octokit } = require('@octokit/rest');

class GitHubEnhancedServer {
  constructor() {
    this.server = new Server(
      {
        name: 'github-enhanced-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Initialize Octokit
    const token = process.env.GITHUB_TOKEN;
    if (!token) {
      throw new Error('GITHUB_TOKEN environment variable is required');
    }
    this.octokit = new Octokit({ auth: token });

    // Parse repository
    const repo = process.env.REPOSITORY;
    if (!repo || !repo.includes('/')) {
      throw new Error('REPOSITORY environment variable must be in format "owner/repo"');
    }
    [this.owner, this.repo] = repo.split('/');

    this.setupToolHandlers();
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'create_issue_with_labels',
          description: 'Create GitHub Issue with automatic label assignment based on content',
          inputSchema: {
            type: 'object',
            properties: {
              title: {
                type: 'string',
                description: 'Issue title',
              },
              body: {
                type: 'string',
                description: 'Issue body (markdown)',
              },
              autoLabel: {
                type: 'boolean',
                description: 'Automatically assign labels based on content',
                default: true,
              },
              assignees: {
                type: 'array',
                items: { type: 'string' },
                description: 'GitHub usernames to assign',
              },
            },
            required: ['title', 'body'],
          },
        },
        {
          name: 'get_agent_tasks',
          description: 'Get all Issues with agent-execute label',
          inputSchema: {
            type: 'object',
            properties: {
              state: {
                type: 'string',
                enum: ['open', 'closed', 'all'],
                default: 'open',
              },
            },
          },
        },
        {
          name: 'update_issue_progress',
          description: 'Update Issue with progress report and task checklist',
          inputSchema: {
            type: 'object',
            properties: {
              issueNumber: {
                type: 'number',
                description: 'Issue number',
              },
              progress: {
                type: 'object',
                properties: {
                  completed: { type: 'number' },
                  total: { type: 'number' },
                  currentTask: { type: 'string' },
                  status: { type: 'string', enum: ['in_progress', 'completed', 'failed'] },
                },
                required: ['completed', 'total', 'status'],
              },
            },
            required: ['issueNumber', 'progress'],
          },
        },
        {
          name: 'create_pr_from_agent',
          description: 'Create PR with agent-generated content and quality report',
          inputSchema: {
            type: 'object',
            properties: {
              issueNumber: {
                type: 'number',
                description: 'Related Issue number',
              },
              branch: {
                type: 'string',
                description: 'Source branch name',
              },
              title: {
                type: 'string',
                description: 'PR title',
              },
              body: {
                type: 'string',
                description: 'PR body',
              },
              qualityReport: {
                type: 'object',
                description: 'Quality assessment report',
              },
              draft: {
                type: 'boolean',
                default: true,
              },
            },
            required: ['issueNumber', 'branch', 'title', 'body'],
          },
        },
        {
          name: 'get_pr_review_status',
          description: 'Get detailed review status including checks and approvals',
          inputSchema: {
            type: 'object',
            properties: {
              prNumber: {
                type: 'number',
                description: 'PR number',
              },
            },
            required: ['prNumber'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'create_issue_with_labels':
            return await this.createIssueWithLabels(args);
          case 'get_agent_tasks':
            return await this.getAgentTasks(args);
          case 'update_issue_progress':
            return await this.updateIssueProgress(args);
          case 'create_pr_from_agent':
            return await this.createPRFromAgent(args);
          case 'get_pr_review_status':
            return await this.getPRReviewStatus(args);
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

  async createIssueWithLabels(args) {
    const { title, body, autoLabel = true, assignees = [] } = args;

    // Auto-detect labels
    let labels = [];
    if (autoLabel) {
      labels = this.detectLabels(title, body);
    }

    // Create issue
    const response = await this.octokit.issues.create({
      owner: this.owner,
      repo: this.repo,
      title,
      body,
      labels,
      assignees,
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            status: 'created',
            issue: {
              number: response.data.number,
              url: response.data.html_url,
              labels: response.data.labels.map(l => l.name),
            },
          }, null, 2),
        },
      ],
    };
  }

  detectLabels(title, body) {
    const labels = [];
    const text = `${title} ${body}`.toLowerCase();

    // Feature detection
    if (text.includes('feature') || text.includes('新機能') || text.includes('add')) {
      labels.push('enhancement');
    }

    // Bug detection
    if (text.includes('bug') || text.includes('fix') || text.includes('error') || text.includes('バグ')) {
      labels.push('bug');
    }

    // Documentation detection
    if (text.includes('documentation') || text.includes('docs') || text.includes('readme') || text.includes('ドキュメント')) {
      labels.push('documentation');
    }

    // Security detection
    if (text.includes('security') || text.includes('vulnerability') || text.includes('セキュリティ')) {
      labels.push('security');
    }

    // Performance detection
    if (text.includes('performance') || text.includes('optimize') || text.includes('パフォーマンス')) {
      labels.push('performance');
    }

    return labels;
  }

  async getAgentTasks(args) {
    const { state = 'open' } = args;

    const response = await this.octokit.issues.listForRepo({
      owner: this.owner,
      repo: this.repo,
      state,
      labels: '🤖agent-execute',
      per_page: 100,
    });

    const tasks = response.data.map(issue => ({
      number: issue.number,
      title: issue.title,
      state: issue.state,
      labels: issue.labels.map(l => l.name),
      assignee: issue.assignee?.login,
      created_at: issue.created_at,
      updated_at: issue.updated_at,
      url: issue.html_url,
    }));

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            total: tasks.length,
            tasks,
          }, null, 2),
        },
      ],
    };
  }

  async updateIssueProgress(args) {
    const { issueNumber, progress } = args;

    // Get current issue
    const issue = await this.octokit.issues.get({
      owner: this.owner,
      repo: this.repo,
      issue_number: issueNumber,
    });

    // Create progress comment
    const progressEmoji = {
      in_progress: '🔄',
      completed: '✅',
      failed: '❌',
    };

    const progressBar = this.createProgressBar(progress.completed, progress.total);

    const comment = `
## 🤖 Agent Progress Update

${progressEmoji[progress.status]} **Status**: ${progress.status.replace('_', ' ').toUpperCase()}

### Progress
${progressBar}
**${progress.completed}/${progress.total}** tasks completed

${progress.currentTask ? `**Current Task**: ${progress.currentTask}` : ''}

---
*Updated: ${new Date().toISOString()}*
`;

    await this.octokit.issues.createComment({
      owner: this.owner,
      repo: this.repo,
      issue_number: issueNumber,
      body: comment,
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            status: 'updated',
            issueNumber,
            progress,
          }, null, 2),
        },
      ],
    };
  }

  createProgressBar(completed, total) {
    const percentage = Math.round((completed / total) * 100);
    const filled = Math.round(percentage / 5); // 20 blocks
    const empty = 20 - filled;
    return `[${'█'.repeat(filled)}${'░'.repeat(empty)}] ${percentage}%`;
  }

  async createPRFromAgent(args) {
    const { issueNumber, branch, title, body, qualityReport, draft = true } = args;

    // Enhance PR body with quality report
    let enhancedBody = body;
    if (qualityReport) {
      enhancedBody += `\n\n## 📊 Quality Report\n\n`;
      enhancedBody += `- **Score**: ${qualityReport.score}/100 ${qualityReport.passed ? '✅' : '❌'}\n`;
      enhancedBody += `- **TypeScript Errors**: ${qualityReport.breakdown?.typeScriptScore || 'N/A'}\n`;
      enhancedBody += `- **ESLint Errors**: ${qualityReport.breakdown?.eslintScore || 'N/A'}\n`;
      enhancedBody += `- **Security Score**: ${qualityReport.breakdown?.securityScore || 'N/A'}\n`;
      enhancedBody += `- **Test Coverage**: ${qualityReport.breakdown?.testCoverageScore || 'N/A'}\n`;
    }

    enhancedBody += `\n\nCloses #${issueNumber}`;

    // Create PR
    const response = await this.octokit.pulls.create({
      owner: this.owner,
      repo: this.repo,
      title,
      body: enhancedBody,
      head: branch,
      base: 'main',
      draft,
    });

    // Link to issue
    await this.octokit.issues.createComment({
      owner: this.owner,
      repo: this.repo,
      issue_number: issueNumber,
      body: `🤖 Agent has created a ${draft ? 'draft ' : ''}PR: #${response.data.number}`,
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            status: 'created',
            pr: {
              number: response.data.number,
              url: response.data.html_url,
              draft: response.data.draft,
            },
          }, null, 2),
        },
      ],
    };
  }

  async getPRReviewStatus(args) {
    const { prNumber } = args;

    // Get PR details
    const pr = await this.octokit.pulls.get({
      owner: this.owner,
      repo: this.repo,
      pull_number: prNumber,
    });

    // Get reviews
    const reviews = await this.octokit.pulls.listReviews({
      owner: this.owner,
      repo: this.repo,
      pull_number: prNumber,
    });

    // Get checks
    const checks = await this.octokit.checks.listForRef({
      owner: this.owner,
      repo: this.repo,
      ref: pr.data.head.sha,
    });

    const status = {
      pr: {
        number: pr.data.number,
        state: pr.data.state,
        mergeable: pr.data.mergeable,
        merged: pr.data.merged,
        draft: pr.data.draft,
      },
      reviews: {
        total: reviews.data.length,
        approved: reviews.data.filter(r => r.state === 'APPROVED').length,
        changesRequested: reviews.data.filter(r => r.state === 'CHANGES_REQUESTED').length,
      },
      checks: {
        total: checks.data.check_runs.length,
        passed: checks.data.check_runs.filter(c => c.conclusion === 'success').length,
        failed: checks.data.check_runs.filter(c => c.conclusion === 'failure').length,
        pending: checks.data.check_runs.filter(c => c.status === 'in_progress' || c.status === 'queued').length,
      },
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(status, null, 2),
        },
      ],
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('GitHub Enhanced MCP Server running on stdio');
  }
}

const server = new GitHubEnhancedServer();
server.run().catch(console.error);
