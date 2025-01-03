"use client";
import GradientBar from "../components/GradientComponent/GradientBar";
import Link from "next/link";
import { useState, useEffect, useContext } from "react";
import { Loader } from "@mantine/core";
import useAuth from "@/hooks/useAuth";
import { AuthenticationContext } from "../context/AuthContext";
import { isValidEmail } from "../utils/utils";
import { useQueryClient } from "@tanstack/react-query";

function isStrongPassword(password: string): boolean {
  const uniqueChars = new Set(password);
  return password.length >= 8 && uniqueChars.size >= 4;
}

export default function Register() {
  const { signup, googleAuth } = useAuth();
  const { loading, error, setAuthState } = useContext(AuthenticationContext);
  const [inputs, setInputs] = useState({
    firstname: "",
    lastname: "",
    email: "",
    password: "",
    passwordConfirm: "",
  });
  const [disabled, setDisabled] = useState(true);
  const [emailAlert, setEmailAlert] = useState("hidden");
  const [passwordAlert, setpasswordAlert] = useState("hidden");
  const [strongPasswordAlert, setStrongPasswordAlert] = useState("hidden");
  const queryClient = useQueryClient();
  useEffect(() => {
    queryClient.invalidateQueries(["verifyUser"]);
    setAuthState({
      loading: false,
      error: null,
      data: null,
    });
    const validFirstName = inputs.firstname.trim().length >= 1;
    const validLastName = inputs.lastname.trim().length >= 1;
    const validEmail = isValidEmail(inputs.email);
    const validPassword = isStrongPassword(inputs.password);
    const passwordsMatch = inputs.password === inputs.passwordConfirm;
    const allFieldsValid =
      validFirstName &&
      validLastName &&
      validEmail &&
      validPassword &&
      passwordsMatch;

    setDisabled(!allFieldsValid);

    if (inputs.password.length >= 1 && !validPassword) {
      setStrongPasswordAlert("block");
    } else {
      setStrongPasswordAlert("hidden");
    }

    if (inputs.passwordConfirm.length >= 1 && !passwordsMatch) {
      setpasswordAlert("block");
    } else {
      setpasswordAlert("hidden");
    }

    if (inputs.email.length >= 1 && !validEmail) {
      setEmailAlert("block");
    } else {
      setEmailAlert("hidden");
    }
  }, [inputs]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputs({
      ...inputs,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async () => {
    localStorage.clear();
    document.cookie.split(";").forEach((c) => {
      document.cookie = c
        .replace(/^ +/, "")
        .replace(/=.*/, `=;expires=${new Date().toUTCString()};path=/`);
    });
    await signup({
      firstname: inputs.firstname,
      lastname: inputs.lastname,
      email: inputs.email,
      password: inputs.password,
    });
  };

  const googleLogin = async () => {
    const googleState: any = await googleAuth();
  };

  return (
    <div className="grid lg:grid-cols-[30%_70%] w-full">
      <GradientBar />
      <div className="w-full h-full flex justify-center items-center">
        <div className="flex-col text-black" data-testid="registerForm">
          <h1 className="text-center font-semibold text-2xl lg:text-3xl mt-[1em] md:mt-[2em] lg:mt-0 tracking-tight">
            Create an Account
          </h1>
          <h1 className="text-center font-normal text-lg lg:text-xl mt-3 text-gray-400 tracking-tight">
            Already have an account?{" "}
            <Link href="/">
              <span className="text-purple-500 font-medium cursor-pointer">
                {" "}
                Sign in here
              </span>
            </Link>
          </h1>
          {/* Sign in with Google button */}
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
                <defs></defs>
              </svg>
              Sign in with Google
            </button>
          </div>
          <div className="mt-5">
            <h1 className="text-center font-medium text-gray-400">OR</h1>
          </div>
          {/* Sign in with Email Form */}
          <div className="flex justify-center space-x-2 mt-3 md:mt-5">
            <div className="w-[170px]">
              <label className="font-medium tracking-tight">First Name</label>
              <input
                data-testid="firstNameInput"
                type="text"
                name="firstname"
                onChange={handleChange}
                required
                className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-md bg-gray-100"
              />
            </div>
            <div className="w-[170px] ">
              <label className="font-medium tracking-tight">Last Name</label>
              <input
                data-testid="lastNameInput"
                type="text"
                name="lastname"
                onChange={handleChange}
                required
                className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-md bg-gray-100"
              />
            </div>
          </div>
          <div className="mt-3">
            <label className="font-medium tracking-tight">Email</label>
            <input
              data-testid="emailInput"
              type="email"
              name="email"
              onChange={handleChange}
              required
              className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-md bg-gray-100"
            />
            <div className={emailAlert}>
              <label className="font-medium tracking-tighter text-red-600">
                Invalid Email
              </label>
            </div>
          </div>
          <div className="mt-3">
            <div className="flex justify-between">
              <label className="font-medium tracking-tight">Password</label>
            </div>
            <input
              data-testid="passwordInput"
              type="password"
              name="password"
              onChange={handleChange}
              required
              className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-md bg-gray-100"
            />
            <div className={strongPasswordAlert}>
              <label className="font-medium tracking-tighter text-red-600">
                Weak Password
              </label>
            </div>
          </div>
          <div className="mt-3">
            <div className="flex justify-between">
              <label className="font-medium tracking-tight">
                Confirm Password
              </label>
            </div>
            <input
              type="password"
              name="passwordConfirm"
              data-testid="confirmPasswordInput"
              onChange={handleChange}
              required
              className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-md bg-gray-100"
            />
            <div className={passwordAlert}>
              <label className="font-medium tracking-tighter text-red-600">
                Password does not match
              </label>
            </div>
          </div>

          {loading ? (
            <div className="flex mt-10 md:mt-5 justify-center">
              <Loader color="grape" variant="bars" />
            </div>
          ) : (
            <div>
              {error != null ? (
                <div className="mt-2 text-red-600 font-medium">
                  <h1>{error}</h1>
                </div>
              ) : (
                <div></div>
              )}
              <button
                className="w-full px-4 py-2 mt-5 md:mt-10 xl:mt-8 text-white font-medium bg-purple-600 hover:bg-purple-500 active:bg-purple-600 rounded-md duration-300 tracking-tight disabled:opacity-50"
                disabled={disabled}
                onClick={handleSubmit}
                data-testid="signUpButton"
              >
                Sign Up
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
