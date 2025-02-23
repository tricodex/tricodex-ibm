/**
 * API utilities
 */

export interface AnalysisResponse {
  task_id: string;
  message: string;
  status: string;
}

export interface APIError {
  message: string;
  details?: string;
  status?: number;
}

/**
 * API utilities for interacting with the ProcessLens backend
 */
class APIClient {
  private readonly baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }
  
  async startAnalysis(file: File, projectName?: string): Promise<AnalysisResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (projectName) {
      formData.append('project_name', projectName);
    }
    
    try {
      // Validate file before sending
      if (!file.size) {
        throw new Error('Empty file provided');
      }

      console.log(`Starting analysis for file ${file.name} at ${this.baseUrl}/analyze`);
      
      const response = await fetch(`${this.baseUrl}/analyze`, {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'application/json',
        },
      });

      const responseData = await response.text();
      let parsed;
      
      try {
        parsed = JSON.parse(responseData);
      } catch (e) {
        console.error('Failed to parse response:', responseData);
        throw new Error('Invalid response format from server');
      }

      if (!response.ok) {
        // Handle structured error response
        const error: APIError = {
          message: parsed.error || 'Unknown error occurred',
          details: parsed.details,
          status: response.status
        };
        throw error;
      }

      return parsed;
    } catch (error) {
      console.error('Analysis request failed:', error);
      
      // Format error for consistent handling
      const apiError: APIError = {
        message: error instanceof Error ? error.message : 'Unknown error occurred',
        details: error instanceof Error ? error.stack : undefined,
        status: (error && typeof error === 'object' && 'status' in error && typeof error.status === 'number') ? error.status : 500
      };
      throw apiError;
    }
  }

  async getAnalysisStatus(taskId: string) {
    try {
      const response = await fetch(`${this.baseUrl}/analyze/${taskId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Status check failed:', error);
      throw error;
    }
  }

  async checkHealth() {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }
}

export const api = new APIClient();