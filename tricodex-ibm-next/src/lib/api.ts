// src/lib/api.ts

export const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  endpoints: {
    health: "/health",
    analyze: "/analyze",
    status: (taskId: string) => `/analyze/${taskId}`,  // Updated to match backend route
    files: {
      list: "/files",
      info: (fileId: string) => `/files/${fileId}`,
      delete: (fileId: string) => `/files/${fileId}`,
    },
    admin: {
      cleanup: "/admin/cleanup",
    }
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

export async function listFiles(skip = 0, limit = 10) {
  console.log("Fetching files:", { skip, limit });
  
  try {
    const response = await fetch(
      `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.files.list}?skip=${skip}&limit=${limit}`
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Files fetch error:", {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      throw new Error(`Files fetch failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log("Files fetched successfully:", data);
    return data;
  } catch (error) {
    console.error("Files fetch failed:", error);
    throw error;
  }
}

export async function getFileInfo(fileId: string) {
  console.log("Fetching file info:", fileId);
  
  try {
    const response = await fetch(
      `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.files.info(fileId)}`
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("File info fetch error:", {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      throw new Error(`File info fetch failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log("File info fetched successfully:", data);
    return data;
  } catch (error) {
    console.error("File info fetch failed:", error);
    throw error;
  }
}

export async function deleteFile(fileId: string) {
  console.log("Deleting file:", fileId);
  
  try {
    const response = await fetch(
      `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.files.delete(fileId)}`,
      { method: "DELETE" }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("File deletion error:", {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      throw new Error(`File deletion failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log("File deleted successfully:", data);
    return data;
  } catch (error) {
    console.error("File deletion failed:", error);
    throw error;
  }
}

export async function cleanupOldData(days: number = 30) {
  console.log("Running cleanup for data older than", days, "days");
  
  try {
    const response = await fetch(
      `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.admin.cleanup}?days=${days}`,
      { method: "POST" }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Cleanup error:", {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      throw new Error(`Cleanup failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log("Cleanup completed successfully:", data);
    return data;
  } catch (error) {
    console.error("Cleanup failed:", error);
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