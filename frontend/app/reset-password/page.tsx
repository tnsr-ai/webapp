"use client";
import GradientBar from "../components/GradientComponent/GradientBar";
import { useEffect, useState } from "react";
import { setResetPassword } from "../api";
import { Loader } from "@mantine/core";
import { useMutation } from "@tanstack/react-query";
import { useUrl } from "nextjs-current-url";

export default function Reset() {
  const [uid, setUID] = useState("");
  const [ptoken, setPToken] = useState("");
  const { href: currentUrl, pathname } = useUrl() ?? {};

  useEffect(() => {
    if (currentUrl) {
      let url = new URL(currentUrl);
      let params = new URLSearchParams(url.search);
      setUID(params.get("user_id") || "");
      setPToken(params.get("password_token") || "");
    }
  }, [currentUrl]);

  const [message, setMessage] = useState("");
  const [labelColor, setLabelColor] = useState("text-red-600");
  const user_id = uid;
  const password_token = ptoken;
  const [run, setRun] = useState(false);
  const { mutate, isLoading, isSuccess, data, isError } = useMutation(
    (formData) => setResetPassword(formData as any)
  );

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordAlert, setPasswordAlert] = useState("hidden ");
  const [disabled, setDisabled] = useState(true);

  const resetPassword = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    const formData = {
      user_id: Number(user_id),
      password_token: password_token as string,
      password: password,
    };
    mutate(formData as any);
    setRun(true);
  };

  useEffect(() => {
    if (password.length < 8 && confirmPassword.length < 8) {
      setDisabled(true);
      setPasswordAlert("block");
      setMessage("Password must be at least 8 characters");
    }
    if (password !== confirmPassword) {
      setDisabled(true);
      setPasswordAlert("block");
      setMessage("Passwords do not match");
      setLabelColor("text-red-600");
    }
    if (password === confirmPassword && password.length >= 8) {
      setDisabled(false);
      setPasswordAlert("hidden");
    }
    if (password.length === 0 && confirmPassword.length === 0) {
      setDisabled(true);
      setPasswordAlert("hidden");
    }
    if (isSuccess === true) {
      if (data.detail === "Success") {
        setMessage(data.data);
        setLabelColor("text-green-600");
        setPasswordAlert("block");
        if (run === true) {
          setPassword("");
          setConfirmPassword("");
          setRun(false);
        }
      } else {
        setMessage(data.data);
        setLabelColor("text-red-600");
        setPasswordAlert("block");
      }
    }
    if (isError === true) {
      setMessage("Something went wrong");
      setLabelColor("text-red-600");
      setPasswordAlert("block");
    }
  }, [
    password,
    confirmPassword,
    message,
    labelColor,
    disabled,
    passwordAlert,
    isSuccess,
    isError,
    run,
  ]);

  return (
    <div className="grid lg:grid-cols-[30%_70%] w-full">
      <GradientBar />
      <div className="w-full h-full flex justify-center items-center">
        <div
          className="flex-col justify-center items-center text-black"
          data-testid="resetForm"
        >
          <h1 className="text-center font-semibold text-2xl lg:text-3xl mt-[2em] lg:mt-0 tracking-tight">
            Reset Password
          </h1>
          <h1 className="text-center font-normal text-lg lg:text-xl mt-2 lg:mt-3 text-gray-400 tracking-tight">
            Please enter your new password
          </h1>
          <form>
            <div className="mt-3 md:mt-5">
              <div>
                <label className="font-medium tracking-tight">Password</label>
                <input
                  type="password"
                  name="password"
                  required
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                  }}
                  data-testid="passwordInput"
                  className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-lg bg-gray-100"
                />
              </div>
              <div className="mt-2 md:mt-4">
                <label className="font-medium tracking-tight">
                  Confirm Password
                </label>
                <input
                  type="password"
                  name="confirmPassword"
                  required
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                  }}
                  data-testid="confirmPasswordInput"
                  className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-lg bg-gray-100"
                />
              </div>
              <div className={`${passwordAlert} pt-3`}>
                <label className={`font-medium tracking-tighter ${labelColor}`}>
                  {message}
                </label>
              </div>
            </div>
          </form>
          <div className="flex justify-center space-x-5 lg:space-x-8 mt-3 md:mt-5">
            {isLoading === false && (
              <button
                className="w-full px-4 py-2 text-white font-medium bg-purple-600 hover:bg-purple-500 active:bg-purple-600 rounded-lg duration-300 tracking-tight disabled:opacity-50 disabled:hover:opacity-50 disabled:cursor-not-allowed"
                disabled={disabled}
                onClick={(e) => resetPassword(e)}
                data-testid="resetPasswordButton"
              >
                Submit
              </button>
            )}
            {isLoading === true && (
              <div className="flex justify-center items-center">
                <Loader color="grape" />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
