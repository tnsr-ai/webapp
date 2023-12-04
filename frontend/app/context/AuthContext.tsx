"use client";
import useAuth from "@/hooks/useAuth";
import axios from "axios";
import { useRouter } from "next/navigation";
import React, { useState, createContext, useEffect } from "react";
import { getCookie } from "cookies-next";
import { NextRequest } from "next/server";

interface User {
  id: number;
  firstname: string;
  lastname: string;
  email: string;
  refresh_token: string;
  access_token: string;
  token_type: string;
}

interface State {
  loading?: boolean;
  error?: string | null;
  data?: User | null;
}

interface AuthState extends State {
  setAuthState: React.Dispatch<React.SetStateAction<State>>;
}

export const AuthenticationContext = createContext<AuthState>({
  loading: false,
  error: null,
  data: null,
  setAuthState: () => {},
});

export default function AuthContext({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [authState, setAuthState] = useState<State>({
    loading: false,
    data: null,
    error: null,
  });

  const fetchUser = async () => {};

  useEffect(() => {
    fetchUser();
  }, []);

  return (
    <AuthenticationContext.Provider
      value={{
        ...authState,
        setAuthState,
      }}
    >
      {children}
    </AuthenticationContext.Provider>
  );
}
