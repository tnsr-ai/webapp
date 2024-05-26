import { useQuery } from "@tanstack/react-query";
import { getCookie } from "cookies-next";
import {
  dashboardEndpoints,
  authEndpoints,
  uploadEndpoints,
  contentEndpoints,
  settingsEndpoints,
  jobsEndpoints,
  optionsEndpoints,
  billingEndpoints,
} from "./endpoints";

// Auth Endpoints

export const useDashboard = () => {
  const jwt = getCookie("access_token");
  return useQuery({
    queryKey: [dashboardEndpoints["getStats"]],
    queryFn: async () => {
      const url = dashboardEndpoints["getStats"];
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${jwt}`,
        },
      });
      const data = await response.json();
      return data;
    },
  });
};

//  Billing Endpoints

export const useGetBalance = () => {
  const jwt = getCookie("access_token");
  return useQuery({
    queryKey: [billingEndpoints["getBalance"]],
    queryFn: async () => {
      const url = billingEndpoints["getBalance"];
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${jwt}`,
        },
      });
      const data = await response.json();
      return data;
    },
  });
};

export const useGetRates = (country: string) => {
  return useQuery({
    queryKey: [billingEndpoints["priceConversion"]],
    queryFn: async () => {
      const url = `${billingEndpoints["priceConversion"]}/?countryCode=${country}`;
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      const data = await response.json();
      return data;
    },
    enabled: false,
    keepPreviousData: true,
    staleTime: Infinity,
  });
};

// Invoice Endpoints

export const useGetInvoice = (limit: number, offset: number) => {
  const jwt = getCookie("access_token");
  return useQuery({
    queryKey: [
      billingEndpoints["getInvoices"],
      {
        limit: limit,
        offset: offset,
      },
    ],
    queryFn: async () => {
      const url = `${billingEndpoints["getInvoices"]}/?limit=${limit}&offset=${offset}`;
      const jwt = getCookie("access_token");
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${jwt}`,
        },
      });
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const data = await response.json();
      return data;
    },
  });
};

// Get client IP

export const useGetIP = () => {
  return useQuery({
    queryKey: ["/billing/get_ip"],
    queryFn: async () => {
      const url = `https://api.country.is`;
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      const data = await response.json();
      return data;
    },
    enabled: false,
    keepPreviousData: true,
    staleTime: Infinity,
  });
};

// Verify user

export const useVerifyUser = () => {
  const jwt = getCookie("access_token");
  const shouldFetch = Boolean(jwt);
  return useQuery({
    queryKey: [authEndpoints["verify"]],
    queryFn: async () => {
      const url = authEndpoints["verify"];
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${jwt}`,
        },
      });
      const data = await response.json();
      return data;
    },
    enabled: shouldFetch,
    staleTime: Infinity,
    cacheTime: 1000 * 60 * 60 * 24,
    retry: false,
  });
};

// Forgot Password
export const setForgotPassword = async (formData: { email: string }) => {
  const url = authEndpoints["forgotPassword"];
  const response = await fetch(url, {
    method: "POST",
    body: JSON.stringify(formData),
    headers: {
      "Content-Type": "application/json",
    },
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Error occurred");
  }
  return data;
};

export const setResetPassword = async (formData: {
  user_id: number;
  password_token: string;
  password: string;
}) => {
  const url = authEndpoints["resetPassword"];
  const response = await fetch(url, {
    method: "POST",
    body: JSON.stringify(formData),
    headers: {
      "Content-Type": "application/json",
    },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(
      data.message || "An error occurred during the password reset."
    );
  }
  return data;
};

// Setting endpoint

export const setPassword = async (formData: {
  current_password: string;
  new_password: string;
  confirm_password: string;
}) => {
  const jwt = getCookie("access_token");
  const url = settingsEndpoints["changePassword"];
  const response = await fetch(url, {
    method: "POST",
    body: JSON.stringify(formData),
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${jwt}`,
    },
  });
  const data = await response.json();
  return data;
};

export const setSettings = async (formData: {
  newsletter: boolean;
  email_notification: boolean;
  discord_webhook: string;
}) => {
  const jwt = getCookie("access_token");
  const url = settingsEndpoints["updateSettings"];
  const response = await fetch(url, {
    method: "POST",
    body: JSON.stringify(formData),
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${jwt}`,
    },
  });
  const data = await response.json();
  return data;
};

export const useGetSettings = () => {
  const jwt = getCookie("access_token");
  return useQuery({
    queryKey: [settingsEndpoints["getSettings"]],
    queryFn: async () => {
      const url = settingsEndpoints["getSettings"];
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${jwt}`,
        },
      });
      const data = await response.json();
      return data;
    },
  });
};

// Content Endpoints

export const useListContent = (
  content_id: number,
  content_type: string,
  limit: number,
  offset: number
) => {
  const jwt = getCookie("access_token");
  return useQuery({
    queryKey: [
      "/content/get_content_list",
      {
        content_id: content_id,
        content_type: content_type,
        limit: limit,
        offset: offset,
      },
    ],
    queryFn: async () => {
      const url = `${contentEndpoints["contentList"]}/?limit=${limit}&offset=${offset}&content_id=${content_id}&content_type=${content_type}`;
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${jwt}`,
        },
      });
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const data = await response.json();
      return data;
    },
    retry: 2,
  });
};

export const registerJob = async (job_type: string, config_json: any) => {
  const jwt = getCookie("access_token");
  const url = jobsEndpoints["registerJob"];
  const postData = {
    job_type: job_type,
    config_json: config_json,
  };
  const response = await fetch(url, {
    method: "POST",
    body: JSON.stringify(postData),
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${jwt}`,
    },
  });
  const data = await response.json();
  return data;
};

export const getJobEstimate = async (content_id: number, job_config: any) => {
  const jwt = getCookie("access_token");
  const url = jobsEndpoints["jobEstimate"];
  const postData = {
    content_id: content_id,
    job_config: job_config,
  };
  const response = await fetch(url, {
    method: "POST",
    body: JSON.stringify(postData),
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${jwt}`,
    },
  });
  if (!response.ok) {
    throw new Error("Network response was not ok");
  }
  const data = await response.json();
  return data;
};

export const useGetJobs = (job_type: string, limit: number, offset: number) => {
  const jwt = getCookie("access_token");
  return useQuery({
    queryKey: [
      "/jobs/get_jobs",
      { job_type: job_type, limit: limit, offset: offset },
    ],
    queryFn: async () => {
      const url = `${jobsEndpoints["get_jobs"]}/?limit=${limit}&offset=${offset}&job_type=${job_type}`;
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${jwt}`,
        },
      });
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const data = await response.json();
      return data;
    },
    refetchInterval: 1000 * 10,
  });
};

export const useJobsConfig = () => {
  const jwt = getCookie("access_token");
  return useQuery({
    queryKey: [jobsEndpoints["filterConfig"]],
    queryFn: async () => {
      const url = jobsEndpoints["filterConfig"];
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${jwt}`,
        },
      });
      const data = await response.json();
      return data;
    },
  });
};

export const useGetUserConfig = () => {
  const jwt = getCookie("access_token");
  return useQuery({
    queryKey: [optionsEndpoints["userTierConfig"]],
    queryFn: async () => {
      const url = optionsEndpoints["userTierConfig"];
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${jwt}`,
        },
      });
      const data = await response.json();
      return data;
    },
  });
};
