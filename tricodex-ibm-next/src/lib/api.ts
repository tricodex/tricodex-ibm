// src/lib/api.ts

export const API_CONFIG = {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    endpoints: {
      health: "/health",
      analyze: "/analyze",
      status: (taskId: string) => `/status/${taskId}`,
      projects: "/projects",
      timing: "/analyze/timing",
      quality: "/analyze/quality",
      resources: "/analyze/resources",
    }
  }
  
  // API client functions
  export async function startAnalysis(formData: FormData) {
    console.log("Starting analysis with API URL:", API_CONFIG.baseUrl);
    
    try {
      const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.analyze}`, {
        method: "POST",
        body: formData,
      });
  
      const responseData = await response.text();
      let errorDetail;
  
      try {
        // Try to parse as JSON
        const jsonData = JSON.parse(responseData);
        errorDetail = jsonData.detail || responseData;
      } catch {
        // If not JSON, use raw response
        errorDetail = responseData;
      }
  
      if (!response.ok) {
        console.error("Analysis API error:", {
          status: response.status,
          statusText: response.statusText,
          error: errorDetail
        });
        throw new Error(`API error (${response.status}): ${errorDetail}`);
      }
  
      // Only try to parse as JSON if we haven't already
      const data = typeof errorDetail === 'string' ? JSON.parse(responseData) : errorDetail;
      console.log("Analysis started successfully:", data);
      return data;
    } catch (error) {
      console.error("Analysis request failed:", error);
      throw error;
    }
  }
  
  export async function checkAnalysisStatus(taskId: string) {
    console.log("Checking status for task:", taskId);
    
    try {
      const response = await fetch(
        `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.status(taskId)}`
      );
  
      const responseData = await response.text();
      let errorDetail;
  
      try {
        // Try to parse as JSON
        const jsonData = JSON.parse(responseData);
        errorDetail = jsonData.detail || responseData;
      } catch {
        // If not JSON, use raw response
        errorDetail = responseData;
      }
  
      if (!response.ok) {
        console.error("Status check error:", {
          status: response.status,
          statusText: response.statusText,
          error: errorDetail
        });
        throw new Error(`Status check failed (${response.status}): ${errorDetail}`);
      }
  
      // Only try to parse as JSON if we haven't already
      const data = typeof errorDetail === 'string' ? JSON.parse(responseData) : errorDetail;
      console.log("Status check result:", data);
      return data;
    } catch (error) {
      console.error("Status check failed:", error);
      throw error;
    }
  }
  
  export async function getProjects(skip = 0, limit = 10) {
    console.log("Fetching projects:", { skip, limit });
    
    try {
      const response = await fetch(
        `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.projects}?skip=${skip}&limit=${limit}`
      );
  
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Projects fetch error:", {
          status: response.status,
          statusText: response.statusText,
          error: errorText
        });
        throw new Error(`Projects fetch failed: ${response.status} ${response.statusText}`);
      }
  
      const data = await response.json();
      console.log("Projects fetched successfully:", data);
      return data;
    } catch (error) {
      console.error("Projects fetch failed:", error);
      throw error;
    }
  }
  
  export async function checkHealth() {
    console.log("Checking API health");
    
    try {
      const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.health}`);
  
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Health check error:", {
          status: response.status,
          statusText: response.statusText,
          error: errorText
        });
        throw new Error(`Health check failed: ${response.status} ${response.statusText}`);
      }
  
      const data = await response.json();
      console.log("Health check result:", data);
      return data;
    } catch (error) {
      console.error("Health check failed:", error);
      throw error;
    }
  }