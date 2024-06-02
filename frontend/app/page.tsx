"use client";
import Link from "next/link";
import { useContext, useEffect, useState } from "react";
import GradientBar from "./components/GradientComponent/GradientBar";
import { Loader } from "@mantine/core";
import useAuth from "@/hooks/useAuth";
import { AuthenticationContext } from "./context/AuthContext";
import { isValidEmail } from "./utils/utils";
import { useQueryClient } from "@tanstack/react-query";

export default function Home() {
  const [inputs, setInputs] = useState({
    email: "",
    password: "",
  });
  const [disabled, setDisabled] = useState(true);
  const [emailAlert, setEmailAlert] = useState("hidden");

  const { signin, googleAuth } = useAuth();
  const { loading, error, setAuthState } = useContext(AuthenticationContext);
  const queryClient = useQueryClient();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputs({
      ...inputs,
      [e.target.name]: e.target.value,
    });
  };

  useEffect(() => {
    queryClient.invalidateQueries(["verifyUser"]);
    setAuthState({
      loading: false,
      error: null,
      data: null,
    });
    if (inputs.email.length >= 2 && !isValidEmail(inputs.email)) {
      setEmailAlert("block");
    }
    if (inputs.email.length >= 2 && isValidEmail(inputs.email)) {
      setEmailAlert("hidden");
    }
    // remove email alert if email input is cleared
    if (inputs.email.length == 0) {
      setEmailAlert("hidden");
    }
    if (
      inputs.email &&
      inputs.password &&
      inputs.password.length >= 8 &&
      isValidEmail(inputs.email)
    ) {
      setDisabled(false);
    } else {
      setDisabled(true);
    }
  }, [inputs, disabled, emailAlert]);

  const handleSubmit = async () => {
    localStorage.clear();
    document.cookie.split(";").forEach((c) => {
      document.cookie = c
        .replace(/^ +/, "")
        .replace(/=.*/, `=;expires=${new Date().toUTCString()};path=/`);
    });
    await signin({ email: inputs.email, password: inputs.password });
  };

  const googleLogin = async () => {
    localStorage.clear();
    document.cookie.split(";").forEach((c) => {
      document.cookie = c
        .replace(/^ +/, "")
        .replace(/=.*/, `=;expires=${new Date().toUTCString()};path=/`);
    });
    const googleState: any = await googleAuth();
  };

  return (
    <div>
      <head>
        <title>Tnsr.ai</title>
      </head>
      <div className="grid lg:grid-cols-[30%_70%] w-full">
        <div data-testid="gradientBar">
          <GradientBar />
        </div>
        <div className="w-full h-full flex justify-center items-center">
          <div
            className="flex-col justify-center items-center text-black"
            data-testid="loginForm"
          >
            <h1 className="text-center font-semibold text-2xl lg:text-3xl mt-[2em] lg:mt-0 tracking-tight">
              Sign In to tnsr.ai
            </h1>
            <h1 className="text-center font-normal text-lg lg:text-xl mt-3 text-gray-400 tracking-tight">
              New here?{" "}
              <Link href="/register">
                <span
                  className="text-purple-500 font-medium cursor-pointer tracking-tight"
                  data-testid="createAccount"
                  data-cy="signup-link"
                >
                  {" "}
                  Create an Account
                </span>
              </Link>
            </h1>
            <form onSubmit={handleSubmit}>
              <div className="mt-3 md:mt-5">
                <label className="font-medium tracking-tight">Email</label>
                <input
                  data-testid="emailInput"
                  type="email"
                  name="email"
                  onChange={handleChange}
                  required
                  className="w-full mt-2 mb-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-md bg-gray-100 "
                />
                <div className={emailAlert} data-testid="invalidEmail">
                  <label className="font-medium tracking-tighter text-red-600">
                    Invalid Email
                  </label>
                </div>
              </div>
              <div className="mt-4">
                <div className="flex justify-between">
                  <label className="font-medium tracking-tight">Password</label>
                  <Link
                    href="/forgot-password"
                    className="text-center text-purple-600 hover:text-purple-500 font-medium tracking-tight"
                    data-testid="forgotPassword"
                    data-cy="forgot-password-link"
                  >
                    Forgot password?
                  </Link>
                </div>
                <input
                  data-testid="passwordInput"
                  type="password"
                  name="password"
                  onChange={handleChange}
                  required
                  className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-md bg-gray-100"
                />
              </div>
            </form>
            {loading ? (
              <div className="flex mt-10 md:mt-5 justify-center">
                <Loader color="grape" variant="bars" />
              </div>
            ) : (
              <div id="login_section">
                {error != null ? (
                  <div className="mt-2 text-red-600 font-medium">
                    <h1>{error}</h1>
                  </div>
                ) : (
                  <div></div>
                )}
                <button
                  className="w-full px-4 py-2 mt-8 text-white font-medium bg-purple-600 hover:bg-purple-500 active:bg-purple-600 rounded-md duration-300 tracking-tight disabled:opacity-50"
                  disabled={disabled}
                  onClick={handleSubmit}
                  data-testid="signInButton"
                  data-cy="signin-button"
                >
                  Sign in
                </button>
                <div className="mt-5">
                  <h1 className="text-center font-medium text-gray-400">OR</h1>
                </div>
                <div className="mt-5">
                  <button
                    className="w-full flex items-center justify-center gap-x-3 py-2.5 border-transparent focus:border-transparent rounded-md text-sm font-medium duration-150 bg-gray-100 text-gray-600 focus:bg-gray-200 tracking-tight"
                    disabled={loading}
                    onClick={googleLogin}
                    data-testid="googleLogin"
                  >
                    <svg
                      className="w-5 h-5"
                      viewBox="0 0 48 48"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <g clipPath="url(#clip0_17_40)">
                        <path
                          d="M47.532 24.5528C47.532 22.9214 47.3997 21.2811 47.1175 19.6761H24.48V28.9181H37.4434C36.9055 31.8988 35.177 34.5356 32.6461 36.2111V42.2078H40.3801C44.9217 38.0278 47.532 31.8547 47.532 24.5528Z"
                          fill="#4285F4"
                        />
                        <path
                          d="M24.48 48.0016C30.9529 48.0016 36.4116 45.8764 40.3888 42.2078L32.6549 36.2111C30.5031 37.675 27.7252 38.5039 24.4888 38.5039C18.2275 38.5039 12.9187 34.2798 11.0139 28.6006H3.03296V34.7825C7.10718 42.8868 15.4056 48.0016 24.48 48.0016Z"
                          fill="#34A853"
                        />
                        <path
                          d="M11.0051 28.6006C9.99973 25.6199 9.99973 22.3922 11.0051 19.4115V13.2296H3.03298C-0.371021 20.0112 -0.371021 28.0009 3.03298 34.7825L11.0051 28.6006Z"
                          fill="#FBBC04"
                        />
                        <path
                          d="M24.48 9.49932C27.9016 9.44641 31.2086 10.7339 33.6866 13.0973L40.5387 6.24523C36.2 2.17101 30.4414 -0.068932 24.48 0.00161733C15.4055 0.00161733 7.10718 5.11644 3.03296 13.2296L11.005 19.4115C12.901 13.7235 18.2187 9.49932 24.48 9.49932Z"
                          fill="#EA4335"
                        />
                      </g>
                      <defs>
                        <clipPath id="clip0_17_40">
                          <rect width="48" height="48" fill="white" />
                        </clipPath>
                      </defs>
                    </svg>
                    Continue with Google
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
