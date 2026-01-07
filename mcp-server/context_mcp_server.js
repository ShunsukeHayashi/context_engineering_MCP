#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import fetch from 'node-fetch';

const CONTEXT_API_URL = process.env.CONTEXT_API_URL || 'http://localhost:9003';
const AI_GUIDES_API_URL = process.env.AI_GUIDES_API_URL || 'http://localhost:8888';
const WORKFLOW_API_URL = process.env.WORKFLOW_API_URL || 'http://localhost:9002';

class ContextEngineeringMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'context-engineering-mcp-server',
        version: '2.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  async makeRequest(baseUrl, endpoint, options = {}) {
    try {
      const url = `${baseUrl}${endpoint}`;
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Request failed: ${error.message}`);
    }
  }

  setupHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        // AI Guides Tools
        {
          name: 'list_ai_guides',
          description: 'List all available AI guides from OpenAI, Google, and Anthropic',
          inputSchema: {
            type: 'object',
            properties: {},
          },
        },
        {
          name: 'search_ai_guides',
          description: 'Search for AI guides by keyword',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'The keyword to search for',
              },
            },
            required: ['query'],
          },
        },
        {
          name: 'search_guides_with_gemini',
          description: 'Search guides using Gemini AI semantic search',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'The search query',
              },
              use_grounding: {
                type: 'boolean',
                description: 'Whether to use Gemini grounding',
                default: true,
              },
            },
            required: ['query'],
          },
        },
        {
          name: 'analyze_guide',
          description: 'Analyze a guide using Gemini AI',
          inputSchema: {
            type: 'object',
            properties: {
              title: {
                type: 'string',
                description: 'The exact title of the AI guide to analyze',
              },
            },
            required: ['title'],
          },
        },
        
        // Context Engineering Tools
        {
          name: 'create_context_session',
          description: 'Create a new context engineering session',
          inputSchema: {
            type: 'object',
            properties: {
              name: {
                type: 'string',
                description: 'Session name',
                default: 'New Context Session',
              },
              description: {
                type: 'string',
                description: 'Session description',
                default: '',
              },
            },
          },
        },
        {
          name: 'create_context_window',
          description: 'Create a new context window in a session',
          inputSchema: {
            type: 'object',
            properties: {
              session_id: {
                type: 'string',
                description: 'The session ID',
              },
              max_tokens: {
                type: 'integer',
                description: 'Maximum tokens for the context window',
                default: 8192,
              },
              reserved_tokens: {
                type: 'integer',
                description: 'Reserved tokens for response',
                default: 512,
              },
            },
            required: ['session_id'],
          },
        },
        {
          name: 'add_context_element',
          description: 'Add an element to a context window',
          inputSchema: {
            type: 'object',
            properties: {
              window_id: {
                type: 'string',
                description: 'The context window ID',
              },
              content: {
                type: 'string',
                description: 'The content to add',
              },
              type: {
                type: 'string',
                description: 'Element type',
                enum: ['system', 'user', 'assistant', 'function', 'tool', 'multimodal'],
                default: 'user',
              },
              priority: {
                type: 'integer',
                description: 'Priority (1-10, higher is more important)',
                default: 5,
              },
              tags: {
                type: 'array',
                items: { type: 'string' },
                description: 'Tags for the element',
                default: [],
              },
            },
            required: ['window_id', 'content'],
          },
        },
        {
          name: 'analyze_context',
          description: 'Analyze a context window for quality and optimization opportunities',
          inputSchema: {
            type: 'object',
            properties: {
              window_id: {
                type: 'string',
                description: 'The context window ID to analyze',
              },
            },
            required: ['window_id'],
          },
        },
        {
          name: 'optimize_context',
          description: 'Optimize a context window using AI',
          inputSchema: {
            type: 'object',
            properties: {
              window_id: {
                type: 'string',
                description: 'The context window ID to optimize',
              },
              goals: {
                type: 'array',
                items: {
                  type: 'string',
                  enum: ['reduce_tokens', 'improve_clarity', 'enhance_relevance', 'remove_redundancy', 'improve_structure'],
                },
                description: 'Optimization goals',
                default: ['reduce_tokens', 'improve_clarity'],
              },
            },
            required: ['window_id'],
          },
        },
        {
          name: 'auto_optimize_context',
          description: 'Automatically optimize context with AI recommendations',
          inputSchema: {
            type: 'object',
            properties: {
              window_id: {
                type: 'string',
                description: 'The context window ID to auto-optimize',
              },
            },
            required: ['window_id'],
          },
        },
        {
          name: 'create_prompt_template',
          description: 'Create a new prompt template',
          inputSchema: {
            type: 'object',
            properties: {
              name: {
                type: 'string',
                description: 'Template name',
              },
              description: {
                type: 'string',
                description: 'Template description',
              },
              template: {
                type: 'string',
                description: 'Template content with {variables}',
              },
              type: {
                type: 'string',
                enum: ['completion', 'chat', 'instruct', 'fewshot', 'chain_of_thought', 'roleplay'],
                description: 'Template type',
                default: 'completion',
              },
              category: {
                type: 'string',
                description: 'Template category',
                default: 'general',
              },
              tags: {
                type: 'array',
                items: { type: 'string' },
                description: 'Template tags',
                default: [],
              },
            },
            required: ['name', 'description', 'template'],
          },
        },
        {
          name: 'generate_prompt_template',
          description: 'Generate a prompt template using AI',
          inputSchema: {
            type: 'object',
            properties: {
              purpose: {
                type: 'string',
                description: 'The purpose of the template',
              },
              examples: {
                type: 'array',
                items: { type: 'string' },
                description: 'Example outputs',
                default: [],
              },
              constraints: {
                type: 'array',
                items: { type: 'string' },
                description: 'Constraints for the template',
                default: [],
              },
            },
            required: ['purpose'],
          },
        },
        {
          name: 'list_prompt_templates',
          description: 'List available prompt templates',
          inputSchema: {
            type: 'object',
            properties: {
              category: {
                type: 'string',
                description: 'Filter by category',
              },
              tags: {
                type: 'string',
                description: 'Filter by tags (comma-separated)',
              },
            },
          },
        },
        {
          name: 'render_template',
          description: 'Render a prompt template with variables',
          inputSchema: {
            type: 'object',
            properties: {
              template_id: {
                type: 'string',
                description: 'The template ID',
              },
              variables: {
                type: 'object',
                description: 'Variables to substitute in the template',
              },
            },
            required: ['template_id', 'variables'],
          },
        },
        {
          name: 'get_context_stats',
          description: 'Get statistics about the context engineering system',
          inputSchema: {
            type: 'object',
            properties: {},
          },
        },
        
        // Workflow System Tools
        {
          name: 'create_workflow',
          description: 'Create a new AI workflow from user input',
          inputSchema: {
            type: 'object',
            properties: {
              user_input: {
                type: 'string',
                description: 'Description of the workflow to create',
              },
              context: {
                type: 'object',
                description: 'Additional context for workflow generation',
                default: {},
              },
            },
            required: ['user_input'],
          },
        },
        {
          name: 'list_workflows',
          description: 'List all workflows in the system',
          inputSchema: {
            type: 'object',
            properties: {
              status: {
                type: 'string',
                enum: ['pending', 'running', 'completed', 'failed'],
                description: 'Filter workflows by status',
              },
            },
          },
        },
        {
          name: 'get_workflow',
          description: 'Get detailed information about a specific workflow',
          inputSchema: {
            type: 'object',
            properties: {
              workflow_id: {
                type: 'string',
                description: 'The workflow ID',
              },
            },
            required: ['workflow_id'],
          },
        },
        {
          name: 'execute_workflow',
          description: 'Execute a workflow',
          inputSchema: {
            type: 'object',
            properties: {
              workflow_id: {
                type: 'string',
                description: 'The workflow ID to execute',
              },
            },
            required: ['workflow_id'],
          },
        },
        {
          name: 'update_task_status',
          description: 'Update the status of a workflow task',
          inputSchema: {
            type: 'object',
            properties: {
              task_id: {
                type: 'string',
                description: 'The task ID',
              },
              status: {
                type: 'string',
                enum: ['pending', 'running', 'completed', 'failed'],
                description: 'New task status',
              },
              result: {
                type: 'object',
                description: 'Task execution result',
                default: {},
              },
              errors: {
                type: 'array',
                items: { type: 'string' },
                description: 'Any errors encountered',
                default: [],
              },
            },
            required: ['task_id', 'status'],
          },
        },
        
        // Dynamic Template Selection Tools
        {
          name: 'browse_template_categories',
          description: 'Browse available template categories and their templates',
          inputSchema: {
            type: 'object',
            properties: {
              category: {
                type: 'string',
                enum: ['business', 'technical', 'education', 'ai-agents', 'productivity'],
                description: 'Specific category to browse, or leave empty for all',
              },
              show_examples: {
                type: 'boolean',
                description: 'Include usage examples in the response',
                default: false,
              },
            },
          },
        },
        {
          name: 'select_template_by_use_case',
          description: 'Find the best template for a specific use case',
          inputSchema: {
            type: 'object',
            properties: {
              use_case: {
                type: 'string',
                description: 'Description of what you want to accomplish',
              },
              industry: {
                type: 'string',
                description: 'Industry context (optional)',
              },
              complexity: {
                type: 'string',
                enum: ['simple', 'intermediate', 'complex'],
                description: 'Complexity level of the task',
                default: 'intermediate',
              },
            },
            required: ['use_case'],
          },
        },
        {
          name: 'get_template_recommendations',
          description: 'Get AI-powered template recommendations based on context',
          inputSchema: {
            type: 'object',
            properties: {
              context: {
                type: 'string',
                description: 'Detailed description of your project or task',
              },
              goals: {
                type: 'array',
                items: { type: 'string' },
                description: 'List of goals you want to achieve',
                default: [],
              },
              constraints: {
                type: 'array',
                items: { type: 'string' },
                description: 'Any constraints or limitations',
                default: [],
              },
            },
            required: ['context'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          // AI Guides Tools
          case 'list_ai_guides': {
            const guides = await this.makeRequest(AI_GUIDES_API_URL, '/guides');
            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(guides, null, 2),
                },
              ],
            };
          }

          case 'search_ai_guides': {
            const guides = await this.makeRequest(AI_GUIDES_API_URL, `/guides/search?query=${encodeURIComponent(args.query)}`);
            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(guides, null, 2),
                },
              ],
            };
          }

          case 'search_guides_with_gemini': {
            const result = await this.makeRequest(AI_GUIDES_API_URL, '/guides/search/gemini', {
              method: 'POST',
              body: JSON.stringify({
                query: args.query,
                use_grounding: args.use_grounding ?? true,
              }),
            });
            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'analyze_guide': {
            const result = await this.makeRequest(AI_GUIDES_API_URL, `/guides/${encodeURIComponent(args.title)}/analyze`);
            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          // Context Engineering Tools
          case 'create_context_session': {
            const result = await this.makeRequest(CONTEXT_API_URL, '/api/sessions', {
              method: 'POST',
              body: JSON.stringify({
                name: args.name || 'New Context Session',
                description: args.description || '',
              }),
            });
            return {
              content: [
                {
                  type: 'text',
                  text: `Created context session: ${result.name} (ID: ${result.session_id})`,
                },
              ],
            };
          }

          case 'create_context_window': {
            const result = await this.makeRequest(CONTEXT_API_URL, `/api/sessions/${args.session_id}/windows`, {
              method: 'POST',
              body: JSON.stringify({
                max_tokens: args.max_tokens || 8192,
                reserved_tokens: args.reserved_tokens || 512,
              }),
            });
            return {
              content: [
                {
                  type: 'text',
                  text: `Created context window: ${result.window_id} (Max tokens: ${result.max_tokens})`,
                },
              ],
            };
          }

          case 'add_context_element': {
            const result = await this.makeRequest(CONTEXT_API_URL, `/api/contexts/${args.window_id}/elements`, {
              method: 'POST',
              body: JSON.stringify({
                content: args.content,
                type: args.type || 'user',
                priority: args.priority || 5,
                tags: args.tags || [],
              }),
            });
            return {
              content: [
                {
                  type: 'text',
                  text: `Added element to context window. Current tokens: ${result.current_tokens} (${result.utilization_ratio.toFixed(2)}% utilization)`,
                },
              ],
            };
          }

          case 'analyze_context': {
            const result = await this.makeRequest(CONTEXT_API_URL, `/api/contexts/${args.window_id}/analyze`, {
              method: 'POST',
            });
            return {
              content: [
                {
                  type: 'text',
                  text: `Context Analysis Results:\n\nQuality Score: ${result.quality_score.toFixed(2)}\n\nMetrics:\n${JSON.stringify(result.metrics, null, 2)}\n\nInsights:\n${result.insights.join('\n- ')}\n\nRecommendations:\n${result.recommendations.join('\n- ')}`,
                },
              ],
            };
          }

          case 'optimize_context': {
            const result = await this.makeRequest(CONTEXT_API_URL, `/api/contexts/${args.window_id}/optimize`, {
              method: 'POST',
              body: JSON.stringify({
                goals: args.goals || ['reduce_tokens', 'improve_clarity'],
                constraints: args.constraints || {},
              }),
            });
            return {
              content: [
                {
                  type: 'text',
                  text: `Started context optimization task: ${result.task_id}\nStatus: ${result.status}\nGoals: ${result.goals.join(', ')}`,
                },
              ],
            };
          }

          case 'auto_optimize_context': {
            const result = await this.makeRequest(CONTEXT_API_URL, `/api/contexts/${args.window_id}/auto-optimize`, {
              method: 'POST',
            });
            return {
              content: [
                {
                  type: 'text',
                  text: `Auto-optimization started: ${result.task_id}\nRecommended goals: ${result.recommendations.recommended_goals.join(', ')}\nReason: ${result.recommendations.reasoning}`,
                },
              ],
            };
          }

          case 'create_prompt_template': {
            const result = await this.makeRequest(CONTEXT_API_URL, '/api/templates', {
              method: 'POST',
              body: JSON.stringify({
                name: args.name,
                description: args.description,
                template: args.template,
                type: args.type || 'completion',
                category: args.category || 'general',
                tags: args.tags || [],
              }),
            });
            return {
              content: [
                {
                  type: 'text',
                  text: `Created template: ${result.name} (ID: ${result.template_id})\nVariables: ${result.variables.join(', ')}`,
                },
              ],
            };
          }

          case 'generate_prompt_template': {
            const params = new URLSearchParams();
            params.append('purpose', args.purpose);
            if (args.examples && args.examples.length > 0) {
              args.examples.forEach(ex => params.append('examples', ex));
            }
            if (args.constraints && args.constraints.length > 0) {
              args.constraints.forEach(c => params.append('constraints', c));
            }

            const result = await this.makeRequest(CONTEXT_API_URL, `/api/templates/generate?${params.toString()}`, {
              method: 'POST',
            });
            return {
              content: [
                {
                  type: 'text',
                  text: `Generated template: ${result.name} (ID: ${result.template_id})\n\nTemplate:\n${result.template}\n\nVariables: ${result.variables.join(', ')}`,
                },
              ],
            };
          }

          case 'list_prompt_templates': {
            const params = new URLSearchParams();
            if (args.category) params.append('category', args.category);
            if (args.tags) params.append('tags', args.tags);

            const result = await this.makeRequest(CONTEXT_API_URL, `/api/templates?${params.toString()}`);
            const templateList = result.templates.map(t => 
              `${t.name} (ID: ${t.id})\n  Type: ${t.type} | Category: ${t.category}\n  Usage: ${t.usage_count} | Quality: ${t.quality_score.toFixed(2)}\n  Variables: ${t.variables.join(', ')}`
            ).join('\n\n');
            
            return {
              content: [
                {
                  type: 'text',
                  text: `Available Templates (${result.templates.length}):\n\n${templateList}`,
                },
              ],
            };
          }

          case 'render_template': {
            const result = await this.makeRequest(CONTEXT_API_URL, `/api/templates/${args.template_id}/render`, {
              method: 'POST',
              body: JSON.stringify({
                template_id: args.template_id,
                variables: args.variables,
              }),
            });
            return {
              content: [
                {
                  type: 'text',
                  text: `Rendered Template:\n\n${result.rendered_content}`,
                },
              ],
            };
          }

          case 'get_context_stats': {
            const result = await this.makeRequest(CONTEXT_API_URL, '/api/stats');
            return {
              content: [
                {
                  type: 'text',
                  text: `Context Engineering System Statistics:\n\nSessions: ${result.sessions.total} total, ${result.sessions.active} active\nContext Windows: ${result.contexts.total_windows}\nElements: ${result.contexts.total_elements} (avg ${result.contexts.avg_elements_per_window.toFixed(1)} per window)\nTemplates: ${result.templates.total_templates}\nOptimization Tasks: ${result.optimization_tasks}`,
                },
              ],
            };
          }

          // Workflow System Tools
          case 'create_workflow': {
            const result = await this.makeRequest(WORKFLOW_API_URL, '/api/workflows', {
              method: 'POST',
              body: JSON.stringify({
                user_input: args.user_input,
                context: args.context || {},
              }),
            });
            return {
              content: [
                {
                  type: 'text',
                  text: `Workflow Created Successfully!\n\nWorkflow ID: ${result.workflow_id}\nStatus: ${result.status}\nGenerated Tasks: ${result.tasks.length}\n\nWorkflow Description:\n${result.description}\n\nNext Steps:\n- Use execute_workflow to start execution\n- Monitor progress with get_workflow`,
                },
              ],
            };
          }

          case 'list_workflows': {
            const params = new URLSearchParams();
            if (args.status) params.append('status', args.status);
            
            const result = await this.makeRequest(WORKFLOW_API_URL, `/api/workflows?${params.toString()}`);
            const workflowList = result.workflows.map(w => 
              `${w.name} (ID: ${w.id})\n  Status: ${w.status} | Created: ${new Date(w.created_at).toLocaleDateString()}\n  Tasks: ${w.tasks.length} | Progress: ${Math.round((w.completed_tasks / w.tasks.length) * 100)}%`
            ).join('\n\n');
            
            return {
              content: [
                {
                  type: 'text',
                  text: `Available Workflows (${result.workflows.length}):\n\n${workflowList}`,
                },
              ],
            };
          }

          case 'get_workflow': {
            const result = await this.makeRequest(WORKFLOW_API_URL, `/api/workflows/${args.workflow_id}`);
            const taskList = result.tasks.map(t => 
              `- ${t.name} (${t.status})\n  Type: ${t.task_type} | Priority: ${t.priority}\n  Dependencies: ${t.dependencies.join(', ') || 'None'}`
            ).join('\n');
            
            return {
              content: [
                {
                  type: 'text',
                  text: `Workflow Details:\n\nName: ${result.name}\nStatus: ${result.status}\nProgress: ${Math.round((result.completed_tasks / result.tasks.length) * 100)}%\n\nDescription:\n${result.description}\n\nTasks (${result.tasks.length}):\n${taskList}`,
                },
              ],
            };
          }

          case 'execute_workflow': {
            const result = await this.makeRequest(WORKFLOW_API_URL, `/api/workflows/${args.workflow_id}/execute`, {
              method: 'POST',
            });
            return {
              content: [
                {
                  type: 'text',
                  text: `Workflow Execution Started!\n\nWorkflow ID: ${args.workflow_id}\nStatus: ${result.status}\nExecution ID: ${result.execution_id}\n\nMonitor progress with get_workflow or check the dashboard.`,
                },
              ],
            };
          }

          case 'update_task_status': {
            const result = await this.makeRequest(WORKFLOW_API_URL, '/api/tasks/update', {
              method: 'POST',
              body: JSON.stringify({
                task_id: args.task_id,
                status: args.status,
                result: args.result || {},
                errors: args.errors || [],
              }),
            });
            return {
              content: [
                {
                  type: 'text',
                  text: `Task Status Updated!\n\nTask ID: ${args.task_id}\nNew Status: ${args.status}\nWorkflow: ${result.workflow_id}\n\nTask execution ${args.status === 'completed' ? 'completed successfully' : `updated to ${args.status}`}.`,
                },
              ],
            };
          }

          // Dynamic Template Selection Tools
          case 'browse_template_categories': {
            const params = new URLSearchParams();
            if (args.category) params.append('category', args.category);
            
            const result = await this.makeRequest(CONTEXT_API_URL, `/api/templates/categories?${params.toString()}`);
            
            let responseText = args.category ? 
              `Templates in Category: ${args.category}\n\n` : 
              'All Template Categories:\n\n';
            
            for (const [category, templates] of Object.entries(result.categories)) {
              responseText += `📁 ${category.toUpperCase()}\n`;
              templates.forEach(template => {
                responseText += `  • ${template.name} (${template.id})\n`;
                responseText += `    Type: ${template.type} | Quality: ${template.quality_score}⭐\n`;
                responseText += `    Use cases: ${template.metadata.use_cases?.join(', ') || 'General'}\n`;
                if (args.show_examples && template.metadata.examples) {
                  responseText += `    Example: ${template.metadata.examples[0]}\n`;
                }
                responseText += '\n';
              });
              responseText += '\n';
            }
            
            return {
              content: [
                {
                  type: 'text',
                  text: responseText,
                },
              ],
            };
          }

          case 'select_template_by_use_case': {
            const result = await this.makeRequest(CONTEXT_API_URL, '/api/templates/recommend', {
              method: 'POST',
              body: JSON.stringify({
                use_case: args.use_case,
                industry: args.industry,
                complexity: args.complexity,
                selection_mode: 'use_case_match',
              }),
            });
            
            const recommendations = result.recommendations.map((rec, index) => 
              `${index + 1}. ${rec.template.name} (Score: ${rec.score}⭐)\n` +
              `   ID: ${rec.template.id}\n` +
              `   Category: ${rec.template.category} | Type: ${rec.template.type}\n` +
              `   Why recommended: ${rec.reasoning}\n` +
              `   Variables needed: ${rec.template.variables.slice(0, 5).join(', ')}${rec.template.variables.length > 5 ? '...' : ''}`
            ).join('\n\n');
            
            return {
              content: [
                {
                  type: 'text',
                  text: `Template Recommendations for: "${args.use_case}"\n\n${recommendations}\n\nUse render_template with your chosen template ID to generate content.`,
                },
              ],
            };
          }

          case 'get_template_recommendations': {
            const result = await this.makeRequest(CONTEXT_API_URL, '/api/templates/ai-recommend', {
              method: 'POST',
              body: JSON.stringify({
                context: args.context,
                goals: args.goals,
                constraints: args.constraints,
              }),
            });
            
            const recommendations = result.recommendations.map((rec, index) => {
              const template = rec.template;
              return `${index + 1}. ${template.name} (${rec.confidence}% confidence)\n` +
                `   Category: ${template.category} | Complexity: ${template.metadata.complexity || 'medium'}\n` +
                `   Perfect for: ${rec.reasoning}\n` +
                `   Expected outcome: ${rec.expected_outcome}\n` +
                `   Template ID: ${template.id}`;
            }).join('\n\n');
            
            const suggestedWorkflow = result.suggested_workflow ? 
              `\n\n🔄 Suggested Workflow:\n${result.suggested_workflow.map((step, i) => `${i + 1}. ${step}`).join('\n')}` : 
              '';
            
            return {
              content: [
                {
                  type: 'text',
                  text: `AI-Powered Template Recommendations\n\nContext Analysis: ${result.context_analysis}\n\n${recommendations}${suggestedWorkflow}\n\nNext steps: Choose a template and use render_template to generate your content.`,
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
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Context Engineering MCP Server running on stdio');
  }
}

const server = new ContextEngineeringMCPServer();
server.run().catch(console.error);